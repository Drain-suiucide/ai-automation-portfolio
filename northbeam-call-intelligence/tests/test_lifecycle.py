"""Registration, validation, approvals, retries and reporting."""

import wave
from pathlib import Path

from app.demo import load_demo, silent_wav
from app.domain import ConflictError, RequestError
from app.evaluation import jaccard, match_items, prf, wer
from app.pipeline.asr import split_stereo_wav
from tests.helpers import ScriptedLLM, flag_codes, make_env, raises

META = {"external_id": "e1", "channel": "phone", "agent_id": "a1", "customer_company": "Acme",
        "recorded_at": "2026-09-29T10:00:00Z", "consent_recorded": True}


def test_registration_validation():
    env = make_env()
    reg = env.svc.register
    for bad in ({"external_id": "../etc/passwd"}, {"external_id": ""}, {"channel": "fax"},
                {"agent_id": ""}, {"customer_company": " "}, {"recorded_at": "yesterday"},
                {"consent_recorded": "yes"}):
        raises(RequestError, lambda bad=bad: reg({**META, **bad}, audio=silent_wav(), filename="a.wav"))
    raises(RequestError, lambda: reg(META, audio=silent_wav(), filename="a.exe"))
    raises(RequestError, lambda: reg(META, audio=b"", filename="a.wav"))
    raises(RequestError, lambda: reg(META))
    raises(RequestError, lambda: reg(META, audio=silent_wav(), filename="a.wav", audio_key="inbox/a.wav"))
    raises(RequestError, lambda: reg(META, audio_key="inbox/missing.wav"))


def test_audio_key_is_moved_out_of_the_inbox():
    env = make_env()
    env.svc.blobs.put("inbox/demo-discovery.wav", silent_wav())
    call = env.svc.register({**META, "external_id": "demo-discovery"}, audio_key="inbox/demo-discovery.wav")
    assert call["status"] == "analyzed" and not env.svc.blobs.exists("inbox/demo-discovery.wav")
    raises(RequestError, lambda: env.svc.register(
        {**META, "external_id": "demo-pii"}, audio_key="../../etc/passwd"))


def test_upload_is_idempotent():
    env = make_env()
    a = env.register("demo-discovery")
    b = env.register("demo-discovery")
    assert a["id"] == b["id"] and b["idempotent"] and env.asr.calls == [None]


def test_approval_is_bound_to_the_reviewed_content():
    env = make_env()
    call = env.register("demo-discount")
    assert env.crm.records == []
    raises(ConflictError, lambda: env.svc.decide(call["id"], "m-1", "approve", "0" * 64))
    raises(RequestError, lambda: env.svc.decide(call["id"], " ", "approve", call["review_hash"]))
    out = env.svc.decide(call["id"], "m-1", "approve", call["review_hash"])
    assert out["status"] == "approved" and out["approval"]["reviewer_id"] == "m-1"
    kinds = sorted(r["kind"] for r in env.crm.records)
    assert kinds[0] == "note" and "task" in kinds
    note = next(r for r in env.crm.records if r["kind"] == "note")
    assert note["payload"]["commitments"][0]["status"] == "pending_manager_approval"
    raises(ConflictError, lambda: env.svc.decide(call["id"], "m-1", "approve"))


def test_reject_cancels_pending_actions():
    env = make_env()
    call = env.register("demo-churn")
    out = env.svc.decide(call["id"], "m-2", "reject", call["review_hash"])
    assert out["status"] == "rejected" and env.crm.records == []
    assert {a["state"] for a in out["actions"]} == {"cancelled"}


def test_unflagged_call_writes_note_and_tasks_immediately_but_not_the_draft():
    env = make_env()
    call = env.register("demo-discovery")
    assert call["status"] == "analyzed" and flag_codes(call) == []
    assert sorted({r["kind"] for r in env.crm.records}) == ["note", "task"]


def test_invalid_model_output_is_retried_then_sent_to_manual_review():
    llm = ScriptedLLM("not json at all")
    env = make_env(llm=llm)
    call = env.register("demo-discovery")
    assert llm.calls == 3
    assert call["status"] == "needs_manual_review" and call["status_reason"] == "llm_output_invalid"
    assert call["insights"] is None and env.crm.records == []
    assert [e["event"] for e in call["audit"]].count("llm_output_invalid") == 3


def test_a_retry_can_succeed():
    ok = {"summary": "fine", "sentiment": "neutral"}
    llm = ScriptedLLM("{broken", ok)
    env = make_env(llm=llm)
    call = env.register("demo-discovery")
    assert llm.calls == 2 and call["status"] == "analyzed" and call["insights"]["summary"] == "fine"


def test_silence_and_missing_transcript_go_to_manual_review_without_calling_the_model():
    env = make_env()
    silent = env.register("demo-silence")
    assert silent["status"] == "needs_manual_review" and silent["status_reason"] == "too_short_or_silent"
    assert env.llm.prompts == [] and silent["insights"] is None
    missing = env.register("no-such-fixture")
    assert missing["status"] == "needs_manual_review" and missing["status_reason"] == "asr_failed"


def test_demo_loader_covers_every_scenario_and_is_repeatable():
    env = make_env()
    first = {r["scenario"]: r["status"] for r in load_demo(env.svc)}
    assert first == {"discovery": "analyzed", "discount": "pending_review", "churn": "pending_review",
                     "pii": "analyzed", "no-consent": "blocked_no_consent",
                     "injection": "pending_review", "silence": "needs_manual_review",
                     "erasure": "deleted"}
    second = {r["scenario"]: r["status"] for r in load_demo(env.svc)}
    assert first == second and len(env.svc.list_calls()) == 8
    assert env.svc.store.verify_audit_chain()


def test_reports_health_and_metrics():
    env = make_env()
    load_demo(env.svc)
    rep = env.svc.daily_report()
    assert rep["calls"] == 8 and rep["by_status"]["pending_review"] == 3
    assert rep["review_flags"]["discount_over_policy"] == 1 and len(rep["pending_review"]) == 3
    assert env.svc.health()["audit_chain_ok"]
    text = env.svc.metrics.render()
    assert 'nci_calls_total{status="analyzed"} 3' in text and "nci_stage_seconds_count" in text


def test_evaluation_helpers():
    assert wer("the quick brown fox", "the quick brown fox") == 0.0
    assert abs(wer("the quick brown fox", "the quick red fox jumps") - 0.5) < 1e-9
    assert jaccard("Send the quote.", "send the quote") == 1.0
    gold = [{"owner": "agent", "text": "Send the quote by Friday"}]
    assert match_items(gold, [{"owner": "agent", "text": "send the quote by friday."}]) == (1, 0, 0)
    assert match_items(gold, [{"owner": "customer", "text": "Send the quote by Friday"}]) == (0, 1, 1)
    assert prf(1, 1, 0)["precision"] == 0.5


def test_stereo_wav_is_split_into_agent_and_customer_channels():
    import array
    import tempfile
    tmp = Path(tempfile.mkdtemp())
    left, right = [100, 200, 300, 400], [-1, -2, -3, -4]
    inter = array.array("h")
    for lft, rgt in zip(left, right, strict=True):
        inter.extend([lft, rgt])
    src = tmp / "st.wav"
    with wave.open(str(src), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(8000)
        w.writeframes(inter.tobytes())
    paths = split_stereo_wav(src, tmp / "out")
    got = []
    for p in paths:
        with wave.open(str(p), "rb") as w:
            assert w.getnchannels() == 1
            a = array.array("h")
            a.frombytes(w.readframes(w.getnframes()))
            got.append(list(a))
    assert got == [left, right]
