"""Generate synthetic leads.csv for the demo."""

from __future__ import annotations

import csv
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "leads.csv"

COMPANIES = [
    ("Acme Retail Ltd", "acme-retail.com", "Retail", "US"),
    ("Acme Retail", "www.acme-retail.com", "Retail", "US"),  # dup variant
    ("BrightSaaS Inc", "brightsaas.com", "SaaS", "US"),
    ("Bright SaaS", "brightsaas.com", "SaaS", "US"),  # dup
    ("FleetLogix GmbH", "fleetlogix.com", "Logistics", "DE"),
    ("PayNorth", "paynorth.com", "Fintech", "NL"),
    ("Helix MFG", "helixmfg.com", "Manufacturing", "US"),
    ("CarePulse", "carepulse.com", "Healthcare", "GB"),
    ("EvilCorp", "evilcorp.com", "Retail", "US"),
    ("BlockedCorp", "blockedcorp.example", "Other", "XX"),
    ("Nordic Packs AB", "nordicpacks.com", "Retail", "SE"),
    ("DataBridge", "databridge.com", "SaaS", "US"),
    ("Orbit Tools", "orbit-tools.com", "SaaS", "CA"),
    ("Silk & Stone", "silkstone.com", "Retail", "FR"),
    ("QuickHaul", "quickhaul.com", "Logistics", "GB"),
    ("NovaPay", "novapay.io", "Fintech", "US"),
    ("GreenMill", "greenmill.com", "Manufacturing", "DE"),
    ("PulseCare", "pulsecare.com", "Healthcare", "US"),
    ("SkyShelf", "skyshelf.com", "Retail", "US"),
    ("CloudNest", "cloudnest.io", "SaaS", "US"),
]

FIRST = ["Anna", "Ben", "Carla", "Diego", "Elena", "Farah", "Gus", "Hana", "Ivan", "Jules"]
LAST = ["Nguyen", "Patel", "Schmidt", "Rossi", "Kim", "Garcia", "Brown", "Silva", "Cohen", "Walsh"]
TITLES = ["Head of Growth", "VP Sales", "Revenue Ops", "Founder", "SDR Manager", "COO"]
BASES = ["legitimate_interest", "consent", "unknown"]


def main() -> None:
    random.seed(42)
    rows: list[dict[str, str]] = []
    for i in range(200):
        company, domain, _industry, country = COMPANIES[i % len(COMPANIES)]
        # dirty fields
        if i % 17 == 0:
            domain = domain.upper()
        if i % 23 == 0:
            company = company + " "
        email_name = f"{FIRST[i % len(FIRST)].lower()}.{LAST[i % len(LAST)].lower()}"
        if i % 11 == 0 and i > 20:
            email = f"info@{domain.lower().removeprefix('www.')}"
        else:
            email = f"{email_name}@{domain.lower().removeprefix('www.')}"
        basis = BASES[i % 3]
        if country == "DE" and i % 2 == 0:
            basis = "legitimate_interest"  # will hit country_policy without consent
        if country == "DE" and i % 5 == 0:
            basis = "consent"
        rows.append(
            {
                "company": company,
                "domain": domain,
                "contact_name": f"{FIRST[i % len(FIRST)]} {LAST[i % len(LAST)]}",
                "email": email,
                "title": TITLES[i % len(TITLES)],
                "country": country,
                "source": "csv",
                "collected_at": "2026-09-01T10:00:00Z",
                "lawful_basis": basis,
            }
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "company",
                "domain",
                "contact_name",
                "email",
                "title",
                "country",
                "source",
                "collected_at",
                "lawful_basis",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} leads to {OUT}")


if __name__ == "__main__":
    main()
