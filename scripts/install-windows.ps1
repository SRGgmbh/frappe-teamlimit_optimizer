# Teamlimit Optimizer – one-line installer for Windows (run as administrator, once per computer or terminal server)
#
#   & ([scriptblock]::Create((irm https://raw.githubusercontent.com/SRGgmbh/frappe-teamlimit_optimizer/version-16/scripts/install-windows.ps1))) `
#       -FrappeUrl "https://erp.example.com" -IngestAuth "token <api_key>:<api_secret>"
#
# Installs the reporting script to C:\ProgramData\TeamlimitOptimizer, stores address and ingest key in config.json
# and registers a scheduled task that runs hidden for every signed-in user at logon and then every hour.
# Running it again updates the script and the task.
param(
    [Parameter(Mandatory = $true)][string]$FrappeUrl,
    [Parameter(Mandatory = $true)][string]$IngestAuth,
    [string]$Branch = "version-16",
    [int]$IntervalMinutes = 60,
    [string]$Repo = "SRGgmbh/frappe-teamlimit_optimizer"
)
$ErrorActionPreference = "Stop"

$principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw "Please run this installer as administrator."
}

$dir = Join-Path $env:ProgramData "TeamlimitOptimizer"
New-Item -ItemType Directory -Force -Path $dir | Out-Null

$src = "https://raw.githubusercontent.com/$Repo/$Branch/scripts/windows/Teamlimit-Report.ps1"
$script = Join-Path $dir "Teamlimit-Report.ps1"
Invoke-WebRequest -Uri $src -OutFile $script -UseBasicParsing
Write-Host "Reporting script installed: $script"

@{ url = $FrappeUrl.TrimEnd("/"); auth = $IngestAuth } | ConvertTo-Json | Set-Content -Path (Join-Path $dir "config.json") -Encoding UTF8
Write-Host "Configuration written: $(Join-Path $dir 'config.json')"

$taskArgs = "--headless powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$script`""
$action = New-ScheduledTaskAction -Execute "conhost.exe" -Argument $taskArgs
$trigger = New-ScheduledTaskTrigger -AtLogOn
$trigger.Repetition = (New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes)).Repetition
$users = New-ScheduledTaskPrincipal -GroupId "S-1-5-32-545" -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -Hidden -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 5) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName "Teamlimit Optimizer" -Action $action -Trigger $trigger -Principal $users -Settings $settings -Force | Out-Null
Write-Host "Scheduled task 'Teamlimit Optimizer' registered (every $IntervalMinutes minutes, hidden, for all users)."
Write-Host "Test with:  powershell -ExecutionPolicy Bypass -File `"$script`" -Test"
