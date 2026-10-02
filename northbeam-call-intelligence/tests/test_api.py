"""HTTP layer smoke tests. Skipped when fastapi/httpx are not installed."""

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

from app.demo import silent_wav  # noqa: E402
from app.main import create_app  # noqa: E402
from tests.helpers import make_env  # noqa: E402

FORM = {"external_id": "demo-discount", "channel": "phone", "agent_id": "a-1",
        "customer_company": "Acme", "recorded_at": "2026-09-29T10:00:00Z", "consent_recorded": "true"}


def client():
    env = make_env()
    return TestClient(create_app(env.svc)), env


def test_health_dashboard_and_request_id():
    c, _ = client()
    r = c.get("/health", headers={"X-Request-ID": "abc123"})
    assert r.status_code == 200 and r.json()["audit_chain_ok"] and r.headers["X-Request-ID"] == "abc123"
    assert "Call review" in c.get("/").text
    assert "nci_calls_total" in c.get("/metrics").text or c.get("/metrics").status_code == 200


def test_upload_review_and_erase_flow():
    c, _ = client()
    r = c.post("/v1/calls", data=FORM, files={"file": ("call.wav", silent_wav(), "audio/wav")})
    assert r.status_code == 201 and r.json()["status"] == "pending_review"
    call = r.json()
    again = c.post("/v1/calls", data=FORM, files={"file": ("call.wav", silent_wav(), "audio/wav")})
    assert again.status_code == 200 and again.json()["id"] == call["id"]
    bad = c.post(f"/v1/calls/{call['id']}/approve", json={"reviewer_id": "m-1", "content_hash": "0" * 64})
    assert bad.status_code == 409
    ok = c.post(f"/v1/calls/{call['id']}/approve", json={"reviewer_id": "m-1", "content_hash": call["review_hash"]})
    assert ok.status_code == 200 and ok.json()["status"] == "approved"
    gone = c.delete(f"/v1/calls/{call['id']}")
    assert gone.status_code == 200 and gone.json()["status"] == "deleted"
    assert c.get("/v1/calls/call-9999").status_code == 404


def test_validation_errors_are_422_and_demo_loads():
    c, _ = client()
    r = c.post("/v1/calls", data={**FORM, "channel": "fax"}, files={"file": ("a.wav", silent_wav(), "audio/wav")})
    assert r.status_code == 422
    r = c.post("/v1/calls", data={**FORM, "consent_recorded": "maybe"}, files={"file": ("a.wav", silent_wav(), "audio/wav")})
    assert r.status_code == 422
    loaded = c.post("/v1/demo/load").json()
    assert len(loaded) == 8 and {x["status"] for x in loaded} >= {"analyzed", "pending_review", "deleted"}
    assert c.get("/v1/calls", params={"status": "pending_review"}).json()
