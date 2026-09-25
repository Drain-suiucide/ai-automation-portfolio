# Lead Intake Automation

An n8n workflow that automatically receives incoming leads, validates their email addresses, and separates valid leads from invalid submissions.

## Business Problem

Manual lead processing creates unnecessary work and increases the risk of accepting incorrect contact information.

This workflow automates the initial lead validation step immediately after a lead is submitted.

## Workflow

```text
Webhook
   ↓
Edit Fields
   ↓
Email Validation
   ↓
IF
  ├── Valid Lead
  └── Invalid Lead
```

## What It Does

* Receives lead data through an HTTP POST webhook
* Extracts the lead's name and email
* Validates the email format using a regular expression
* Routes valid and invalid leads into separate branches
* Returns a structured result describing the validation status

## Example Input

```json
{
  "name": "Alex Manoev",
  "email": "alex@example.com"
}
```

## Valid Lead Output

```json
{
  "name": "Alex Manoev",
  "email": "alex@example.com",
  "status": "valid"
}
```

## Invalid Lead Output

```json
{
  "name": "Alex Manoev",
  "email": "not-an-email",
  "status": "invalid",
  "error": "Email format is invalid"
}
```

## Technologies

* n8n
* Webhooks
* JavaScript expressions
* Regular expressions
* HTTP / JSON
* Git / GitHub

## Business Value

The workflow can be used as an initial layer in a larger lead-processing system.

Possible extensions include:

* CRM integration
* Google Sheets / Airtable storage
* Lead enrichment
* Duplicate detection
* AI lead qualification
* Email notifications
* Slack notifications
* Automatic lead scoring

## Project Structure

```text
01-lead-intake/
├── README.md
└── workflow.json
```

## Author

Wokich — AI Automation Portfolio
