from __future__ import annotations

from pathlib import Path

from app.db import Store
from app.models import LawfulBasis, Lead
from app.pipeline.dedupe import dedupe_against_store, prepare_lead
from app.service import import_csv


def test_needs_basis_gate(tmp_path: Path) -> None:
    store = Store(path=str(tmp_path / "s.json"))
    lead = prepare_lead(
        Lead(
            company="X",
            domain="x.com",
            contact_name="A B",
            email="a@x.com",
            lawful_basis=LawfulBasis.UNKNOWN,
        )
    )
    lead, _ = dedupe_against_store(lead, store)
    assert lead.state.value == "needs_basis"


def test_fuzzy_merge(tmp_path: Path) -> None:
    store = Store(path=str(tmp_path / "s.json"))
    a = prepare_lead(
        Lead(
            company="Acme Retail Ltd",
            domain="acme-retail.com",
            contact_name="Anna",
            email="anna@acme-retail.com",
            lawful_basis=LawfulBasis.CONSENT,
        )
    )
    store.upsert_lead(a)
    b = prepare_lead(
        Lead(
            company="Acme Retail",
            domain="www.acme-retail.com",
            contact_name="Anna",
            email="anna@acme-retail.com",
            lawful_basis=LawfulBasis.CONSENT,
        )
    )
    b, decision = dedupe_against_store(b, store)
    assert decision is not None
    assert decision.action == "merge"
    assert b.merged_into == a.id


def test_import_csv(tmp_path: Path) -> None:
    store = Store(path=str(tmp_path / "s.json"))
    csv_path = Path(__file__).resolve().parents[1] / "data" / "leads.csv"
    if not csv_path.exists():
        return
    leads = import_csv(csv_path.read_text(encoding="utf-8"), store)
    assert len(leads) >= 50
