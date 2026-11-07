# Teamlimit Optimizer – reporting script for Windows
# Reads the Claude usage of the signed-in user and reports it to Frappe.
# The Claude token never leaves the device; only e-mail, seat tier and percentages are sent.
# Run manually with visible output:  powershell -ExecutionPolicy Bypass -File .\Teamlimit-Report.ps1 -Test
#
# Address and key are either filled in when the script is downloaded from the Teamlimit Settings,
# or read from config.json next to the script (written by scripts/install-windows.ps1).
param([switch]$Test)

$FrappeUrl  = "__FRAPPE_URL__"
$IngestAuth = "__INGEST_AUTH__"   # ingest user: may only report, cannot read anything

$ErrorActionPreference = "Stop"
$logDir = Join-Path $env:LOCALAPPDATA "TeamlimitOptimizer"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$log = Join-Path $logDir "report.log"
function Log($msg) {
    $line = "{0:yyyy-MM-dd HH:mm:ss}  {1}" -f (Get-Date), $msg
    Add-Content -Path $log -Value $line -Encoding UTF8
    if ($Test) { Write-Host $line }
}
function LocalTime($iso) {
    if (-not $iso) { return $null }
    return ([datetimeoffset]::Parse($iso)).LocalDateTime.ToString("yyyy-MM-dd HH:mm:ss")
}

$cfgPath = Join-Path $PSScriptRoot "config.json"
if ($FrappeUrl.StartsWith("__") -and (Test-Path $cfgPath)) {
    $cfg = Get-Content $cfgPath -Raw | ConvertFrom-Json
    $FrappeUrl = $cfg.url
    $IngestAuth = $cfg.auth
}
if ($FrappeUrl.StartsWith("__")) { Log "No configuration found (config.json next to the script)."; exit 1 }

try {
    $credFile = Join-Path $env:USERPROFILE ".claude\.credentials.json"
    if (-not (Test-Path $credFile)) { Log "No Claude Code sign-in found, skipped."; exit 0 }
    $oauth = (Get-Content $credFile -Raw | ConvertFrom-Json).claudeAiOauth
    if (-not $oauth.accessToken) { Log "Sign-in file without token, skipped."; exit 0 }

    $expires = [datetimeoffset]::FromUnixTimeMilliseconds([int64]$oauth.expiresAt).LocalDateTime
    if ($expires -lt (Get-Date)) { Log "Token expired ($expires). Start Claude Code once, then try again."; exit 0 }

    $email = $null
    $cfgFile = Join-Path $env:USERPROFILE ".claude.json"
    if (Test-Path $cfgFile) { $email = (Get-Content $cfgFile -Raw | ConvertFrom-Json).oauthAccount.emailAddress }
    if (-not $email) { Log "E-mail not found in .claude.json (oauthAccount.emailAddress)."; exit 1 }

    $usage = Invoke-RestMethod -Uri "https://api.anthropic.com/api/oauth/usage" -Method Get -TimeoutSec 30 -Headers @{
        "Authorization"  = "Bearer $($oauth.accessToken)"
        "anthropic-beta" = "oauth-2025-04-20"
        "User-Agent"     = "claude-code/2.1.0"
    }
    if ($Test) { Log ("Usage response: " + ($usage | ConvertTo-Json -Depth 5 -Compress)) }

    $body = @{
        email             = $email
        subscription_type = $oauth.subscriptionType
        rate_limit_tier   = $oauth.rateLimitTier
        five_pct          = $usage.five_hour.utilization
        five_reset        = LocalTime $usage.five_hour.resets_at
        week_pct          = $usage.seven_day.utilization
        week_reset        = LocalTime $usage.seven_day.resets_at
    }
    if ($usage.extra_usage -and $usage.extra_usage.used_credits -ne $null) { $body.extra_used = $usage.extra_usage.used_credits }

    Invoke-RestMethod -Uri "$FrappeUrl/api/method/teamlimit_optimizer.api.report" -Method Post -TimeoutSec 30 `
        -Headers @{ "Authorization" = $IngestAuth } -ContentType "application/json; charset=utf-8" `
        -Body ([System.Text.Encoding]::UTF8.GetBytes(($body | ConvertTo-Json -Compress))) | Out-Null
    Log ("Reported: {0}  5h {1}%  week {2}%  tier {3}" -f $email, $body.five_pct, $body.week_pct, $body.rate_limit_tier)
}
catch {
    Log ("Error: " + $_.Exception.Message)
    exit 1
}
