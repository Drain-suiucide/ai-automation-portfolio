"""
Seed the database with realistic demo emails by hitting POST /process.
Usage: python scripts/seed_demo.py
"""
import httpx

API_URL = "http://127.0.0.1:8000"

EMAILS = [
    {
        "external_id": "demo-001",
        "subject": "Critical production outage",
        "body": "Our production system is completely down since 30 minutes. We lose $10k per hour. Need immediate help. - CTO, Enterprise Client",
        "from_address": "cto@enterprise-client.com",
    },
    {
        "external_id": "demo-002",
        "subject": "Question about pricing",
        "body": "Hi, I'm evaluating your product for our team of 50. Could you share pricing details and a demo? Thanks, Sarah from TechCorp.",
        "from_address": "sarah@techcorp.io",
    },
    {
        "external_id": "demo-003",
        "subject": "Invoice INV-2024-118 unpaid",
        "body": "Hi, this is John Smith from ACME Corp. Invoice INV-2024-118 for 1200 EUR is overdue by 14 days. Please process the payment by 2024-11-15. Phone: +49 30 12345678.",
        "from_address": "john.smith@acme.com",
    },
    {
        "external_id": "demo-004",
        "subject": "You won a $1000 gift card!!!",
        "body": "Click here to claim your prize now! Limited time offer!",
        "from_address": "noreply@spam.xyz",
    },
    {
        "external_id": "demo-005",
        "subject": "FYI: Office closed next Friday",
        "body": "Just a heads up, the office will be closed next Friday for maintenance. No action required.",
        "from_address": "hr@company.com",
    },
]


def main():
    print(f"Seeding {len(EMAILS)} demo emails to {API_URL}...")
    for i, email in enumerate(EMAILS, 1):
        try:
            r = httpx.post(f"{API_URL}/process", json=email, timeout=120.0)
            r.raise_for_status()
            data = r.json()
            print(f"  [{i}/{len(EMAILS)}] ✓ {email['subject'][:40]}... → {data['priority']['priority']} / {data['classification']['category']}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 409:
                print(f"  [{i}/{len(EMAILS)}] ~ {email['subject'][:40]} (already exists)")
            else:
                print(f"  [{i}/{len(EMAILS)}] ✗ {email['subject'][:40]}: {e.response.text}")
        except Exception as e:
            print(f"  [{i}/{len(EMAILS)}] ✗ {email['subject'][:40]}: {e}")
    print("Done.")


if __name__ == "__main__":
    main()