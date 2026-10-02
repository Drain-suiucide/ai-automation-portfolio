"""INV-1: a call without established consent never reaches full ASR or the LLM."""

from app.config import ROOT
from tests.helpers import make_env


def test_consent_false_never_touches_asr_or_llm():
    env = make_env()
    call = env.register("demo-discovery", consent=False)
    assert call["status"] == "blocked_no_consent"
    assert env.asr.calls == []
    assert env.llm.prompts == []
    assert call["segments"] == [] and call["insights"] is None


def test_consent_unknown_without_phrase_runs_only_a_short_probe():
    env = make_env()
    call = env.register("demo-no-consent", consent=None)
    assert call["status"] == "blocked_no_consent"
    assert env.asr.calls == [60], "only the 60 s probe may run"
    assert env.llm.prompts == []
    assert call["segments"] == [], "the probe transcript must not be stored"
    assert "consent_checked" in [e["event"] for e in call["audit"]]


def test_blocked_call_audio_is_purged():
    env = make_env()
    call = env.register("demo-no-consent", consent=None)
    assert [k for k in env.svc.blobs.all_keys() if f"calls/{call['id'][5:]}" in k] == []
    assert "audio_purged" in [e["event"] for e in call["audit"]]


def test_consent_unknown_with_phrase_is_processed():
    env = make_env()
    call = env.register("demo-discovery", consent=None)
    assert call["status"] == "analyzed"
    assert env.asr.calls == [60, None]


def test_consent_true_skips_the_probe():
    env = make_env()
    call = env.register("demo-discovery", consent=True)
    assert call["status"] == "analyzed"
    assert env.asr.calls == [None]


def test_customer_saying_the_phrase_does_not_grant_consent():
    env = make_env(demo=False)
    env.write_fixture("cust-says", [
        ("agent", "Hi, thanks for calling, how can I help you today with your account?"),
        ("customer", "Please note this call is being recorded, I want it on the record."),
        ("agent", "Understood, I will send you the summary by Friday afternoon after the call.")])
    call = env.register("cust-says", consent=None)
    assert call["status"] == "blocked_no_consent"


def test_phrase_after_probe_window_does_not_count():
    env = make_env(demo=False)
    turns = [("agent", "Let us talk about your setup and what you need this quarter overall.")] * 14
    turns.append(("agent", "By the way, this call is being recorded."))
    env.write_fixture("late-phrase", turns)
    assert env.register("late-phrase", consent=None)["status"] == "blocked_no_consent"


def test_policy_probe_window_is_configured_in_yaml():
    assert (ROOT / "app" / "policies" / "default.yml").read_text().count("consent_probe_seconds: 60") == 1
