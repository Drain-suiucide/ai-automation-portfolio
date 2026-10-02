"""Runs the 30-call set through the real pipeline and writes reports/evaluation.md.

    uv run python scripts/evaluate.py            # exit code 1 if a hard gate fails

Two passes: (1) the deterministic fake extractor, (2) the same extractor with seeded
hallucinations injected, to prove the evidence validator drops what it should.
"""

from __future__ import annotations

import json
import logging
import random
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.config import Settings, load_policy  # noqa: E402
from app.demo import silent_wav  # noqa: E402
from app.evaluation import match_items, prf  # noqa: E402
from app.pipeline.asr import FixtureASR  # noqa: E402
from app.pipeline.crm import MockCRM  # noqa: E402
from app.pipeline.llm import ExtractionPrompt, FakeLLM, LLMResult  # noqa: E402
from app.service import CallService, Providers  # noqa: E402

GEN = ROOT / "evals" / "generated" / "transcripts"
GOLD = ROOT / "evals" / "gold.jsonl"


class SpyASR:
    name = "spy-fixture"

    def __init__(self, inner: FixtureASR) -> None:
        self.inner, self.calls = inner, []

    def transcribe(self, audio: Any, max_seconds: float | None = None) -> Any:
        self.calls.append((audio.external_id, max_seconds))
        return self.inner.transcribe(audio, max_seconds)


class SpyLLM:
    """Records prompts; optionally injects hallucinated items (seeded)."""

    def __init__(self, inner: FakeLLM, noisy: bool) -> None:
        self.inner, self.noisy = inner, noisy
        self.name, self.model = inner.name, inner.model
        self.prompts: list[str] = []
        self.injected = 0

    def extract(self, prompt: ExtractionPrompt) -> LLMResult:
        self.prompts.append(prompt.text())
        res = self.inner.extract(prompt)
        if not self.noisy:
            return res
        d = json.loads(res.raw_json)
        d["action_items"] += [
            {"text": "INJECTED-a wire the deposit", "owner": "agent", "due": None,
             "evidence": ["seg-999"], "quote": "we will wire the deposit"},
            {"text": "INJECTED-b refund everything", "owner": "agent", "due": None,
             "evidence": ["seg-1"], "quote": "we agreed to refund everything today"}]
        d["competitors"].append("GhostCorp")
        first = prompt.segments[0]
        d["commitments"].append({"kind": "discount", "value_pct": 5, "who": first.speaker if first.speaker != "unknown" else "agent",
                                 "evidence": [first.id], "quote": " ".join(first.text.split()[:5])})
        self.injected += 4
        return LLMResult(json.dumps(d), res.provider, res.model, res.prompt_version)


class Capture(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.lines: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.lines.append(record.getMessage() + " " + str(getattr(record, "fields", "")))


def run_pass(gold: list[dict[str, Any]], noisy: bool) -> dict[str, Any]:
    policy = load_policy()
    root = Path(tempfile.mkdtemp(prefix="nci-eval-"))
    settings = Settings(root / "data", ROOT / "app" / "policies" / "default.yml", GEN)
    asr, llm, crm = SpyASR(FixtureASR(GEN)), SpyLLM(FakeLLM(policy), noisy), MockCRM()
    svc = CallService(settings, policy, Providers(asr, llm, crm))
    cap = Capture()
    logging.getLogger("nci").addHandler(cap)
    rows = []
    for g in gold:
        meta = {"external_id": g["external_id"], "channel": "phone", "agent_id": "eval-agent",
                "customer_company": g["company"], "recorded_at": "2026-09-29T10:00:00Z",
                "consent_recorded": g["consent"]}
        rows.append((g, svc.register(meta, audio=silent_wav(), filename="e.wav")))
    logging.getLogger("nci").removeHandler(cap)
    return {"svc": svc, "asr": asr, "llm": llm, "crm": crm, "rows": rows, "logs": cap.lines}


def pct(x: float) -> str:
    return f"{x * 100:.1f}%"


def main() -> int:
    if not GOLD.exists():
        print("gold set missing: run scripts/generate_dataset.py first")
        return 2
    gold = [json.loads(line) for line in GOLD.read_text().splitlines() if line.strip()]
    random.seed(0)
    p1, p2 = run_pass(gold, noisy=False), run_pass(gold, noisy=True)

    ok_status = sum(c["status"] == g["expect_status"] for g, c in p1["rows"])
    tp = fp = fn = 0
    exp_total = got_total = hit = 0
    for g, c in p1["rows"]:
        expected = set(g["expect_flags"])
        got = {f["code"] for f in c["flags"] if f["severity"] == "review"}
        exp_total += len(expected)
        got_total += len(got)
        hit += len(expected & got)
        if c["insights"]:
            pred = [{"owner": a["owner"], "text": a["text"]} for a in c["insights"]["action_items"]]
            a, b, d = match_items(g["actions"], pred)
            tp, fp, fn = tp + a, fp + b, fn + d
    action = prf(tp, fp, fn)
    flag_recall = hit / exp_total if exp_total else 1.0
    flag_precision = hit / got_total if got_total else 1.0

    genuine = sum(c["validation"]["proposed"] for _, c in p1["rows"] if c["validation"])
    injected = p2["llm"].injected
    dropped = sum(sum(c["validation"]["dropped"].values()) for _, c in p2["rows"] if c["validation"]) - sum(
        sum(c["validation"]["dropped"].values()) for _, c in p1["rows"] if c["validation"])
    leaked = 0
    kept = 0
    for _, c in p2["rows"]:
        if not c["insights"]:
            continue
        ins = c["insights"]
        kept += len(ins["action_items"]) + len(ins["objections"]) + len(ins["commitments"]) + len(ins["competitors"])
        leaked += sum(a["text"].startswith("INJECTED") for a in ins["action_items"])
        leaked += sum(x == "GhostCorp" for x in ins["competitors"])
        leaked += sum(x["value_pct"] == 5 for x in ins["commitments"])
    before = injected / (injected + genuine) if injected + genuine else 0.0

    canaries = [c for g in gold for c in g["canaries"]]
    blob = "\n".join(p1["llm"].prompts) + "\n" + p1["svc"].store.dump_text() + "\n" + "\n".join(p1["logs"])
    pii_leaks = sum(c in blob for c in canaries)

    blocked = [g["external_id"] for g in gold if g["expect_status"] == "blocked_no_consent"]
    full_asr_on_blocked = sum(1 for ext, ms in p1["asr"].calls if ext in blocked and ms is None)
    blocked_llm = sum(1 for _, c in p1["rows"] if c["status"] == "blocked_no_consent" and c["insights"])
    drafts_sent = sum(r["kind"] == "followup_draft" for r in p1["crm"].records)

    m = p1["svc"].metrics
    lat = {s: (m.percentile(s, 0.5) * 1000, m.percentile(s, 0.95) * 1000)
           for s in ("total", "asr", "redact", "llm", "validate", "policy")}

    gates = {
        "status matches gold on every call": ok_status == len(gold),
        "policy flag recall = 1.0": flag_recall == 1.0,
        "action-item F1 >= 0.80": action["f1"] >= 0.80,
        "hallucinated claims that survive validation = 0": leaked == 0 and dropped == injected,
        "PII canaries in prompts / database / logs = 0": pii_leaks == 0 and len(canaries) > 0,
        "blocked calls that reach full ASR or the model = 0": full_asr_on_blocked == 0 and blocked_llm == 0,
        "follow-up drafts executed or sent = 0": drafts_sent == 0,
    }
    lines = [
        "# Evaluation report", "",
        "Generated by `scripts/evaluate.py` on the 30 synthetic calls in `evals/generated/`.",
        "Speech and labels come from the same templates, and the extractor is the deterministic fake, so these",
        "numbers detect **regressions in the pipeline**. They do not estimate real-world model accuracy.", "",
        "## Hard gates", "", "| Gate | Result |", "|---|---|",
        *[f"| {k} | {'pass' if v else '**FAIL**'} |" for k, v in gates.items()], "",
        "## Metrics", "", "| Metric | Value | Notes |", "|---|---|---|",
        f"| Calls | {len(gold)} | 7 discovery, 6 discount, 5 churn, 4 PII, 3 injection, 1 compliance, 2 no consent, 2 silence |",
        f"| Status accuracy | {pct(ok_status / len(gold))} | expected status per call |",
        f"| Policy flags | recall {pct(flag_recall)}, precision {pct(flag_precision)} | review-severity flags |",
        f"| Action items | P {action['precision']}, R {action['recall']}, F1 {action['f1']} | fuzzy match, Jaccard >= 0.8 |",
        f"| Unsupported claims in the noisy pass, before validation | {pct(before)} | {injected} injected vs {genuine} genuine proposals |",
        f"| Injected claims dropped | {dropped} of {injected} | leaked into insights: {leaked} |",
        f"| PII canaries | {len(canaries)} checked, {pii_leaks} leaked | prompts, database dump, log lines |",
        f"| Blocked calls | {len(blocked)} | full ASR: {full_asr_on_blocked}, model calls: {blocked_llm} |",
        f"| Follow-up drafts sent | {drafts_sent} | the project has no send code path |",
        f"| LLM cost | ${m.cost_usd:.4f} | fake provider is free; real providers report tokens and cost |",
        "| WER | not measured | needs real recordings, see `evals/audio/README.md` |", "",
        "## Latency (milliseconds, this machine)", "",
        "Measures pipeline overhead only: fixture ASR and a rule-based extractor. Real ASR and LLM latency",
        "must be measured with real providers.", "",
        "| Stage | p50 | p95 |", "|---|---|---|",
        *[f"| {s} | {a:.1f} | {b:.1f} |" for s, (a, b) in lat.items()], "",
    ]
    (ROOT / "reports").mkdir(exist_ok=True)
    (ROOT / "reports" / "evaluation.md").write_text("\n".join(lines), encoding="utf-8")
    (ROOT / "reports" / "evaluation.json").write_text(json.dumps({
        "gates": gates, "status_accuracy": ok_status / len(gold), "flag_recall": flag_recall,
        "flag_precision": flag_precision, "actions": action, "injected": injected, "dropped": dropped,
        "leaked": leaked, "pii_leaks": pii_leaks, "kept_after_noise": kept}, indent=1) + "\n")
    print("\n".join(lines[:22]))
    return 0 if all(gates.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
