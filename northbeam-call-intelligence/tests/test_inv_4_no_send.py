"""INV-4: nothing in this project sends e-mail. Follow-ups are drafts a human sends."""

from pathlib import Path

from tests.helpers import make_env

FORBIDDEN = ("smtplib", "sendmail", "send_message", "sendgrid", "mailgun", "postmark", "ses.send",
             "aiosmtplib", "yagmail")


def test_source_tree_has_no_mail_sending_code():
    for path in Path("app").rglob("*.py"):
        text = path.read_text(encoding="utf-8").lower()
        for token in FORBIDDEN:
            assert token not in text, f"{path} mentions {token}"


def test_followup_is_a_pending_draft_and_never_executed():
    env = make_env()
    call = env.register("demo-discovery")
    draft = next(a for a in call["actions"] if a["kind"] == "followup_draft")
    assert draft["requires_approval"] and draft["state"] == "pending_approval"
    assert "followup_draft" not in [r["kind"] for r in env.crm.records]


def test_approving_hands_the_draft_to_a_human_and_still_sends_nothing():
    env = make_env()
    call = env.register("demo-discovery")
    out = env.svc.decide(call["id"], "manager-1", "approve", call["review_hash"])
    draft = next(a for a in out["actions"] if a["kind"] == "followup_draft")
    assert draft["state"] == "approved_draft"
    assert "followup_draft" not in [r["kind"] for r in env.crm.records]
