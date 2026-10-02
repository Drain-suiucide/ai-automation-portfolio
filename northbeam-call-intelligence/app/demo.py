"""Demo scenarios: pre-made synthetic transcripts replayed by the fixture ASR."""

from __future__ import annotations

import io
import wave
from typing import Any

SCENARIOS: list[dict[str, Any]] = [
    {"slug": "discovery", "title": "Discovery call with clear next steps", "consent": None,
     "expect": "analyzed: action items with evidence, follow-up draft waits for approval"},
    {"slug": "discount", "title": "Agent offers 25% (policy max 15%)", "consent": True,
     "expect": "pending_review: discount_over_policy, CRM actions wait for a manager"},
    {"slug": "churn", "title": "Customer threatens to cancel, names a competitor", "consent": True,
     "expect": "pending_review: churn_risk"},
    {"slug": "pii", "title": "Customer dictates card, e-mail and phone", "consent": True,
     "expect": "analyzed: only [CARD_1]-style tokens reach the model and the database"},
    {"slug": "no-consent", "title": "No recording announcement, no consent metadata", "consent": None,
     "expect": "blocked_no_consent: nothing is stored, audio purged"},
    {"slug": "injection", "title": "Speech that tries to instruct the assistant", "consent": True,
     "expect": "pending_review: prompt_injection_suspected, no CRM stage change"},
    {"slug": "silence", "title": "Poor audio, almost no speech", "consent": True,
     "expect": "needs_manual_review: no summary is invented"},
    {"slug": "erasure", "title": "Processed call, then erased on request", "consent": True,
     "delete": True, "expect": "deleted: audio, text and insights gone; audit tombstone stays"},
]


def silent_wav(seconds: float = 1.0, rate: int = 8000) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b"\x00\x00" * int(seconds * rate))
    return buf.getvalue()


def load_demo(service: Any) -> list[dict[str, Any]]:
    """Register (and process) every scenario. Safe to call repeatedly: uploads are idempotent."""
    results = []
    for sc in SCENARIOS:
        meta = {"external_id": f"demo-{sc['slug']}", "channel": "phone", "agent_id": "agent-demo",
                "customer_company": f"Demo {sc['slug'].replace('-', ' ').title()} Ltd",
                "recorded_at": "2026-09-29T10:00:00Z", "consent_recorded": sc["consent"]}
        call = service.register(meta, audio=silent_wav(), filename="demo.wav")
        if sc.get("delete") and call["status"] != "deleted":
            call = service.delete(call["id"], reason="demo_erasure_request")
        results.append({"scenario": sc["slug"], "title": sc["title"], "expect": sc["expect"],
                        "call_id": call["id"], "status": call["status"]})
    return results
