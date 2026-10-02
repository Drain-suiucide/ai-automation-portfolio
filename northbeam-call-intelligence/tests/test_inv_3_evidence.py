"""INV-3: model claims without valid evidence never reach the CRM."""

import json

from app.domain import Segment
from app.pipeline.insights import SchemaError, build_insights, check_grounding
from tests.helpers import ScriptedLLM, make_env, raises

SEGS = [Segment("seg-1", 0, 5, "agent", "I can do twenty-five percent off if you sign this week.", 0.9),
        Segment("seg-2", 5, 9, "customer", "That is above our budget, we also use Vantora today.", 0.9)]
BY_ID = {s.id: s for s in SEGS}


def item(**kw):
    base = {"text": "Send quote", "owner": "agent", "due": None, "evidence": ["seg-1"],
            "quote": "I can do twenty-five percent off"}
    base.update(kw)
    return base


def test_check_grounding_reasons():
    assert check_grounding(item(), BY_ID) is None
    assert check_grounding(item(evidence=[]), BY_ID) == "missing_evidence"
    assert check_grounding(item(evidence=["seg-9"]), BY_ID) == "unknown_segment"
    assert check_grounding(item(quote=""), BY_ID) == "missing_quote"
    assert check_grounding(item(quote="totally invented words"), BY_ID) == "quote_not_in_evidence"
    assert check_grounding(item(quote=" ".join(["word"] * 16)), BY_ID) == "quote_too_long"


def test_quote_matches_ignoring_case_and_punctuation():
    assert check_grounding(item(quote="I CAN do twenty five percent, off"), BY_ID) is None


def test_quote_must_come_from_a_cited_segment():
    assert check_grounding(item(quote="above our budget", evidence=["seg-1"]), BY_ID) == "quote_not_in_evidence"


def test_validator_drops_and_counts_each_bad_claim():
    payload = {"summary": "s", "sentiment": "neutral",
               "action_items": [item(), item(evidence=["seg-42"]), item(quote="invented"),
                                {"text": "no owner", "evidence": ["seg-1"], "quote": "I can do"}],
               "objections": [{"type": "price", "evidence": ["seg-2"], "quote": "above our budget"},
                              {"type": "bogus", "evidence": ["seg-2"], "quote": "above our budget"}],
               "commitments": [{"kind": "discount", "value_pct": 10, "who": "agent",
                                "evidence": ["seg-1"], "quote": "I can do twenty-five percent off"}],
               "competitors": ["Vantora", "GhostCorp"], "crm_stage": "closed_won"}
    ins, rep = build_insights(json.dumps(payload), SEGS)
    assert len(ins.action_items) == 1 and len(ins.objections) == 1
    assert ins.commitments == () and ins.competitors == ("Vantora",)
    assert rep.dropped["unknown_segment"] == 1 and rep.dropped["quote_not_in_evidence"] == 1
    assert rep.dropped["malformed"] == 1 and rep.dropped["bad_owner"] == 1
    assert rep.dropped["numeric_mismatch"] == 1
    assert rep.dropped["competitor_not_in_transcript"] == 1
    assert rep.ignored_keys == ("crm_stage",)


def test_agent_commitment_must_be_said_by_the_agent():
    payload = {"summary": "s", "sentiment": "neutral", "commitments": [
        {"kind": "discount", "value_pct": 25, "who": "customer", "evidence": ["seg-1"],
         "quote": "I can do twenty-five percent off"}]}
    ins, rep = build_insights(json.dumps(payload), SEGS)
    assert ins.commitments == () and rep.dropped["speaker_mismatch"] == 1


def test_malformed_json_raises_schema_error():
    raises(SchemaError, lambda: build_insights("not json", SEGS))
    raises(SchemaError, lambda: build_insights("[1, 2]", SEGS))
    raises(SchemaError, lambda: build_insights(json.dumps({"action_items": "x"}), SEGS))


def test_fenced_json_is_tolerated():
    ins, _ = build_insights("```json\n" + json.dumps({"summary": "ok", "sentiment": "neutral"}) + "\n```", SEGS)
    assert ins.summary == "ok"


def test_only_grounded_items_reach_the_crm():
    llm = ScriptedLLM({
        "summary": "s", "sentiment": "neutral",
        "action_items": [
            {"text": "Send the revised quote", "owner": "agent", "due": None, "evidence": ["seg-5"],
             "quote": "I'll send you a quote for forty seats by Friday."},
            {"text": "INVENTED wire transfer", "owner": "agent", "due": None, "evidence": ["seg-77"],
             "quote": "wire the money"},
            {"text": "INVENTED refund", "owner": "agent", "due": None, "evidence": ["seg-5"],
             "quote": "we will refund everything"}]})
    env = make_env(llm=llm)
    call = env.register("demo-discovery")
    tasks = [a for a in call["actions"] if a["kind"] == "task"]
    assert [t["payload"]["text"] for t in tasks] == ["Send the revised quote"]
    assert "INVENTED" not in json.dumps(env.crm.records)
    assert call["validation"]["dropped"] == {"unknown_segment": 1, "quote_not_in_evidence": 1}
    assert "ungrounded_items_dropped" in [f["code"] for f in call["flags"]]
