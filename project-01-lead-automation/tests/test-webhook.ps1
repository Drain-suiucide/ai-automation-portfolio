param(
    [ValidateSet('high','medium','low','duplicate')]
    [string]$Case = 'high',
    [string]$BaseUrl = 'http://localhost:5678/webhook-test/lead-capture'
)

$common = @{
    name = 'Portfolio Workflow Test'
    employees = 12
    service = 'AI Business Automation'
}

switch ($Case) {
    'high' {
        $lead = $common.Clone()
        $lead.email = 'your-test-inbox@example.com'
        $lead.company = 'High Value Test Company'
        $lead.message = 'We have a defined business need to automate lead qualification, sales reporting and follow-ups, and want to evaluate a solution soon.'
    }
    'medium' {
        $lead = $common.Clone()
        $lead.email = 'your-test-inbox@example.com'
        $lead.company = 'Medium Value Test Company'
        $lead.message = 'We are exploring a basic lead capture workflow. Budget is limited and purchase timing is not decided.'
    }
    'low' {
        $lead = $common.Clone()
        $lead.email = 'your-test-inbox@example.com'
        $lead.company = 'Low Value Research Test'
        $lead.message = 'I am only researching a personal idea. There is no defined company project, budget, or purchase plan.'
    }
    'duplicate' {
        $lead = $common.Clone()
        $lead.email = 'your-test-inbox@example.com'
        $lead.company = 'Duplicate Detection Test Company'
        $lead.message = 'This exact payload is intended to verify duplicate detection. Keep it identical for both requests.'
    }
}

function Send-Lead([hashtable]$Payload) {
    $json = $Payload | ConvertTo-Json -Depth 5
    try {
        $response = Invoke-RestMethod -Uri $BaseUrl -Method POST -ContentType 'application/json' -Body $json
        $response | ConvertTo-Json -Depth 10
    }
    catch {
        Write-Host "Request failed: $($_.Exception.Message)" -ForegroundColor Yellow
        if ($_.ErrorDetails.Message) { Write-Host $_.ErrorDetails.Message }
    }
}

Write-Host "Case: $Case" -ForegroundColor Cyan
Write-Host 'WARNING: this can send real email/Telegram notifications when live credentials are configured.' -ForegroundColor Yellow

if ($Case -eq 'duplicate') {
    Write-Host 'Request 1 (expect a new lead):'
    Send-Lead $lead
    Start-Sleep -Seconds 2
    Write-Host 'Request 2 with identical payload (expect HTTP 409 duplicate):'
    Send-Lead $lead
} else {
    Send-Lead $lead
}
