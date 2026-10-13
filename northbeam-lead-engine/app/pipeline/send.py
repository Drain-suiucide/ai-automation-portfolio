from __future__ import annotations

import asyncio
import random
import smtplib
from email.message import EmailMessage
from secrets import token_urlsafe
from typing import Protocol

from app.db import Store
from app.metrics import observe_block, observe_send
from app.models import Lead, LeadState, SendResult
from app.pipeline.guard import check_send_guards
from app.settings import get_settings, load_yaml
from app.state_machine import transition


class MailProvider(Protocol):
    def send(self, *, to: str, subject: str, body: str, unsubscribe_url: str) -> str:
        ...


class SMTPMail:
    def __init__(self, host: str | None = None, port: int | None = None) -> None:
        settings = get_settings()
        self.host = host or settings.mail_host
        self.port = port or settings.mail_port
        self.mail_from = settings.mail_from

    def send(self, *, to: str, subject: str, body: str, unsubscribe_url: str) -> str:
        msg = EmailMessage()
        msg["From"] = self.mail_from
        msg["To"] = to
        msg["Subject"] = subject
        msg["List-Unsubscribe"] = f"<{unsubscribe_url}>"
        msg["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"
        msg.set_content(body)
        with smtplib.SMTP(self.host, self.port, timeout=10) as smtp:
            smtp.send_message(msg)
        return msg["Message-ID"] or token_urlsafe(8)


class MemoryMail:
    def __init__(self) -> None:
        self.outbox: list[dict[str, str]] = []

    def send(self, *, to: str, subject: str, body: str, unsubscribe_url: str) -> str:
        mid = token_urlsafe(8)
        self.outbox.append(
            {
                "to": to,
                "subject": subject,
                "body": body,
                "unsubscribe_url": unsubscribe_url,
                "message_id": mid,
                "list_unsubscribe": unsubscribe_url,
            }
        )
        return mid


def ensure_unsubscribe_token(lead: Lead, store: Store) -> str:
    for token, email in store.tokens.items():
        if email == lead.email:
            return token
    token = token_urlsafe(16)
    store.tokens[token] = lead.email
    store.persist()
    return token


def send_lead(lead: Lead, store: Store, mail: MailProvider) -> SendResult:
    reason = check_send_guards(lead, store)
    if reason:
        observe_block(reason)
        observe_send("blocked")
        if lead.draft:
            lead.draft.block_reason = reason
        store.append_audit("send_blocked", lead.id, reason=reason)
        store.upsert_lead(lead)
        return SendResult(lead_id=lead.id, sent=False, reason=reason)

    assert lead.draft is not None
    settings = get_settings()
    token = ensure_unsubscribe_token(lead, store)
    unsub = f"{settings.unsubscribe_base_url.rstrip('/')}/v1/unsubscribe/{token}"
    body = lead.draft.body.replace("{{unsubscribe_url}}", unsub)
    if "List-Unsubscribe" not in body and unsub not in body:
        # body must contain working unsubscribe link (INV-7)
        observe_block("missing_unsubscribe")
        return SendResult(lead_id=lead.id, sent=False, reason="missing_unsubscribe")

    limits = load_yaml("send_limits.yml")
    jitter = random.uniform(
        float(limits.get("jitter_seconds_min", 0)),
        float(limits.get("jitter_seconds_max", 0)),
    )
    if jitter > 0:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            import time

            time.sleep(jitter)

    message_id = mail.send(
        to=lead.email,
        subject=lead.draft.subject,
        body=body,
        unsubscribe_url=unsub,
    )
    transition(lead, LeadState.SENT)
    store.sends_today += 1
    store.domain_sends[lead.canonical_domain] = store.domain_sends.get(lead.canonical_domain, 0) + 1
    from app.models import utcnow

    store.contacted_at[lead.email] = utcnow().isoformat()
    store.append_audit("sent", lead.id, message_id=message_id)
    store.upsert_lead(lead)
    observe_send("sent")
    return SendResult(lead_id=lead.id, sent=True, message_id=message_id)
