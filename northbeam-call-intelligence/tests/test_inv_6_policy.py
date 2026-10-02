"""INV-6: policy flags are deterministic. Model output can add to them, never remove them."""

import json

from app.config import Policy, load_policy
from tests.helpers import POLICY, ScriptedLLM, flag_codes, make_env

CLEAN = {"summary": "Nothing to see.", "sentiment": "positive", "action_items": [], "objections": [],
         "commitments": [], "competitors": [], "followup_draft": "",
         "risk_flags": [], "requires_review": False}


def test_flag_survives_a_model_that_reports_nothing():
    env = make_env(llm=ScriptedLLM(CLEAN))
    call = env.register("demo-discount")
    assert call["status"] == "pending_review"
    assert "discount_over_policy" in flag_codes(call)
    assert call["flags"][0]["evidence"] == ["seg-3"]


def test_flag_survives_a_model_that_lies_about_the_number():
    lie = dict(CLEAN, commitments=[{"kind": "discount", "value_pct": 10, "who": "agent",
                                    "evidence": ["seg-3"], "quote": "I can do twenty-five percent off"}])
    env = make_env(llm=ScriptedLLM(lie))
    call = env.register("demo-discount")
    assert call["insights"]["commitments"] == []
    assert call["validation"]["dropped"]["numeric_mismatch"] == 1
    assert "discount_over_policy" in flag_codes(call)


def test_model_cannot_set_review_flags_through_extra_keys():
    env = make_env(llm=ScriptedLLM(dict(CLEAN, risk_flags=[], requires_review=False)))
    call = env.register("demo-churn")
    assert "churn_risk" in flag_codes(call) and call["requires_review"]


def _discount_env(pct_words: str):
    env = make_env(demo=False, llm=ScriptedLLM(CLEAN))
    env.write_fixture("d", [
        ("agent", "Hello, this is Sam from Northbeam. This call is being recorded for our notes today."),
        ("customer", "Your price is high for our team, can you do something about it please?"),
        ("agent", f"Sure, I can offer {pct_words} off the list price if you sign this week, no problem.")])
    return env


def test_discount_threshold_boundaries():
    assert "discount_over_policy" not in flag_codes(_discount_env("10 percent").register("d"))
    assert "discount_over_policy" not in flag_codes(_discount_env("fifteen percent").register("d"))
    assert "discount_over_policy" in flag_codes(_discount_env("16%").register("d"))
    assert "discount_over_policy" in flag_codes(_discount_env("thirty percent").register("d"))


def test_customer_asking_for_a_big_discount_is_not_an_agent_commitment():
    env = make_env(demo=False, llm=ScriptedLLM(CLEAN))
    env.write_fixture("ask", [
        ("agent", "Hello, this is Sam from Northbeam. This call is being recorded for our notes today."),
        ("customer", "Honestly we would need a 40% discount before we could even consider signing this."),
        ("agent", "I cannot promise that today, let me check what is possible and come back to you.")])
    assert "discount_over_policy" not in flag_codes(env.register("ask"))


def test_competitor_alone_is_not_churn_but_with_negative_tone_it_is():
    env = make_env(demo=False, llm=ScriptedLLM(CLEAN))
    env.write_fixture("c1", [
        ("agent", "Hello, this is Sam from Northbeam. This call is being recorded for our notes today."),
        ("customer", "We are also looking at Vantora for a comparison, that is all for now, thanks.")])
    assert "churn_risk" not in flag_codes(env.register("c1"))
    env.write_fixture("c2", [
        ("agent", "Hello, this is Sam from Northbeam. This call is being recorded for our notes today."),
        ("customer", "We are frustrated and disappointed, and Vantora looks better to us right now.")])
    assert "churn_risk" in flag_codes(env.register("c2"))


def test_compliance_keyword_is_flagged():
    env = make_env(demo=False, llm=ScriptedLLM(CLEAN))
    env.write_fixture("gdpr", [
        ("agent", "Hello, this is Sam from Northbeam. This call is being recorded for our notes today."),
        ("customer", "Before we sign, our lawyer wants a data processing agreement under GDPR from you.")])
    assert "compliance_review" in flag_codes(env.register("gdpr"))


def test_low_asr_confidence_is_flagged():
    env = make_env(demo=False, llm=ScriptedLLM(CLEAN))
    env.write_fixture("lowc", [
        ("agent", "Hello, this is Sam from Northbeam. This call is being recorded for our notes today."),
        ("customer", "Yes please continue with the plan we discussed last week, it sounds reasonable.")],
        conf=0.4)
    assert "low_asr_confidence" in flag_codes(env.register("lowc"))


def test_price_statement_from_unlabeled_speaker_needs_a_human():
    env = make_env(demo=False, llm=ScriptedLLM(CLEAN))
    env.write_fixture("unk", [
        ("unknown", "Hello and welcome, this call is being recorded for our notes today, thanks."),
        ("unknown", "We can do thirty percent off the price if you sign this week, that is our best offer.")])
    codes = flag_codes(env.register("unk"))
    assert "discount_over_policy" in codes and "unknown_speaker_role" in codes


def test_policy_file_is_validated():
    bad = json.loads(json.dumps({"max_discount_pct": "x"}))
    try:
        Policy.from_dict(bad)
    except ValueError:
        pass
    else:
        raise AssertionError("bad policy accepted")
    assert isinstance(load_policy().max_discount_pct, int) and POLICY.max_discount_pct == 15
