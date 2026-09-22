# Lead Intake Automation

## Overview
A local n8n workflow that receives lead data through a webhook,
validates the email format, and returns a processing status.

## Workflow
Webhook → IF → Valid Lead / Invalid Lead

## Features
- Receives JSON via HTTP POST
- Validates email format using a regular expression
- Routes valid and invalid submissions
- Preserves the original lead fields
- Returns a processing result

## Test
Send a POST request to the n8n webhook test URL with JSON data.

## Requirements
- n8n
- PowerShell or another HTTP client

## Notes
This project is a local portfolio demo.
The email check validates format only; it does not verify
whether the mailbox exists.