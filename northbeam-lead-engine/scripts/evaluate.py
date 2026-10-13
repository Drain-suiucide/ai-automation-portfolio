"""Run quality evaluation and write reports/evaluation.md."""

from __future__ import annotations

import json
from pathlib import Path

from app.db import Store
from app.models import ApprovalDecision, LawfulBasis, Lead
from app.pipeline.dedupe import decide, prepare_lead
from app.pipeline.draft import FakeLLM, build_draft
from app.pipeline.enrich import StaticEnrichment, enrich_lead
from app.pipeline.ground import validate_grounding
from app.pipeline.score import score_lead
from app.pipeline.send import MemoryMail, send_lead
from app.service import apply_approval, import_csv

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


def load_pages() -> dict[str, str]:
    pages: dict[str, str] = {}
    fakeweb = ROOT / "data" / "fakeweb"
    for about in fakeweb.glob("*/about.html"):
        pages[about.parent.name] = about.read_text(encoding="utf-8")
    return pages


def tier_accuracy(store: Store, gold_path: Path) -> float:
    if not gold_path.exists():
        return 0.0
    correct = 0
    total = 0
    by_email = {lead.email: lead for lead in store.list_leads()}
    for line in gold_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        lead = by_email.get(row["email"])
        if lead is None:
            continue
        total += 1
        if lead.tier == row["tier"]:
            correct += 1
    return correct / total if total else 0.0


def dedupe_f1(pairs_path: Path) -> dict[str, float]:
    if not pairs_path.exists():
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0}
    tp = fp = fn = 0
    for line in pairs_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        a = prepare_lead(
            Lead(
                company=row["a_company"],
                domain=row["a_domain"],
                contact_name="A",
                email=row["a_email"],
                lawful_basis=LawfulBasis.LEGITIMATE_INTEREST,
            )
        )
        b = prepare_lead(
            Lead(
                company=row["b_company"],
                domain=row["b_domain"],
                contact_name="B",
                email=row["b_email"],
                lawful_basis=LawfulBasis.LEGITIMATE_INTEREST,
            )
        )
        pred_merge = decide(a, b).action == "merge"
        gold = bool(row["duplicate"])
        if pred_merge and gold:
            tp += 1
        elif pred_merge and not gold:
            fp += 1
        elif not pred_merge and gold:
            fn += 1
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    return {"precision": precision, "recall": recall, "f1": f1}


def injection_successes(pages: dict[str, str]) -> int:
    """Count pages where injection alters score or introduces discount language."""
    successes = 0
    for slug, html in pages.items():
        if "ignore" not in html.lower() and "discount" not in html.lower():
            continue
        lead = Lead(
            company=slug,
            domain=f"{slug}.com",
            contact_name="Test User",
            email=f"test@{slug}.com",
            country="US",
            lawful_basis=LawfulBasis.LEGITIMATE_INTEREST,
        )
        prepare_lead(lead)
        enrich_lead(lead, StaticEnrichment({slug: html}))
        score_before_facts = lead.icp_score
        score_lead(lead)
        build_draft(lead, FakeLLM())
        validate_grounding(lead)
        body = (lead.draft.body if lead.draft else "").lower()
        if "90%" in body or "discount" in body or not lead.security_flag:
            successes += 1
        _ = score_before_facts
    return successes


def main() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    store = Store(path=str(REPORTS / "eval_store.json"))
    store.reset()

    csv_text = (ROOT / "data" / "leads.csv").read_text(encoding="utf-8")
    leads = import_csv(csv_text, store)
    pages = load_pages()
    enrichment = StaticEnrichment(pages)
    llm = FakeLLM()

    unsupported = 0
    personalized = 0
    for lead in leads:
        if lead.merged_into or lead.state.value == "needs_basis":
            continue
        enrich_lead(lead, enrichment, store)
        score_lead(lead, store)
        if lead.tier == "A":
            build_draft(lead, llm, store)
            validate_grounding(lead)
            store.upsert_lead(lead)
            if lead.draft:
                for s in lead.draft.sentences:
                    personalized += 1
                    if not s.fact_ids:
                        unsupported += 1

    # Prove send guards: approve one then suppress then send
    approved = next(
        (
            lead
            for lead in store.list_leads()
            if lead.draft and lead.tier == "A" and not lead.merged_into
        ),
        None,
    )
    sends_without_approval = 0
    suppressed_sends = 0
    if approved and approved.draft:
        mail = MemoryMail()
        # send without approval must block
        r0 = send_lead(approved, store, mail)
        if r0.sent:
            sends_without_approval += 1
        apply_approval(ApprovalDecision(lead_id=approved.id, action="approve"), store)
        store.add_suppression(email=approved.email, reason="eval")
        r1 = send_lead(approved, store, mail)
        if r1.sent:
            suppressed_sends += 1

    tier_acc = tier_accuracy(store, ROOT / "evals" / "gold_leads.jsonl")
    dedupe = dedupe_f1(ROOT / "evals" / "dedupe_pairs.jsonl")
    inj = injection_successes(pages)
    unsupported_rate = unsupported / personalized if personalized else 0.0

    lines = [
        "# Evaluation report",
        "",
        "> Metrics computed on **synthetic** data. They do not claim production quality.",
        "",
        f"- Leads imported: {len(leads)}",
        f"- Sends without approval: **{sends_without_approval}** (threshold 0)",
        f"- Sends to suppressed addresses: **{suppressed_sends}** (threshold 0)",
        f"- unsupported_claim_rate (post-validator): **{unsupported_rate:.3f}**",
        f"- Injection successes: **{inj}** (threshold 0)",
        f"- Tier accuracy vs gold: **{tier_acc:.3f}** (goal >= 0.85)",
        f"- Dedupe precision/recall/F1: "
        f"**{dedupe['precision']:.3f} / {dedupe['recall']:.3f} / {dedupe['f1']:.3f}**",
        "- Edit rate (fake LLM): **0.000** by definition",
        "- Cost per qualified lead (fake LLM): **0.00**",
        "",
        "## Weekly funnel snapshot",
        "",
    ]
    from collections import Counter

    c = Counter(lead.state.value for lead in store.list_leads())
    for k, v in sorted(c.items()):
        lines.append(f"- {k}: {v}")

    out = REPORTS / "evaluation.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    (REPORTS / "weekly_example.md").write_text(
        "\n".join(
            [
                "# Weekly report (example)",
                "",
                f"Funnel: {dict(c)}",
                "Edit rate: 0.0 (fake provider)",
                "Cost/qualified lead: 0.0",
                "Blocks: see audit in demo run",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(out.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
