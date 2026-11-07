<p align="center">
  <img src="teamlimit_optimizer/public/images/logo.svg" width="112" alt="Teamlimit Optimizer logo">
</p>

<h1 align="center">Teamlimit Optimizer</h1>
<p align="center"><b>for Claude by Anthropic</b> · a Frappe app · English and German</p>

Every member of a Claude Team plan has their own usage limits – a 5-hour session window and a weekly limit. Limits cannot be transferred between seats, and budget that is not used by the weekly reset is gone. Teamlimit Optimizer makes those limits visible for the whole team and helps to use them fully:

- **Live usage of all members** – 5-hour window and week, colour thresholds, pace against the week (Monday to Friday or including weekends) and time left until the reset.
- **Who can help?** – suggests colleagues with free capacity: own Claude Team first, standard seats before premium seats.
- **Task pool** – ready-made prompts that anyone with spare budget starts in Claude Desktop with one click, with take-over lock, questions, result link and Frappe notifications to the requester.
- **Reports** – trend, year comparison, task pool analysis, helpers of the week and expired budget with its cause (tasks were waiting vs. the pool was empty).
- **Skills** for Claude to write and complete pool tasks, plus an instruction for other AI assistants (ChatGPT, Copilot, Gemini) – in English and German.

> **Not an official Anthropic product.** Claude and Anthropic are trademarks of Anthropic, PBC. This app only refers to them descriptively.

## How it works

A small reporting script runs hourly on every computer (Windows: PowerShell via the Task Scheduler, hidden; Linux: systemd user timer or cron). It reads the signed-in user's usage from the local Claude Code sign-in and sends **only** the e-mail address, seat tier, percentages and reset times to Frappe. The Claude token never leaves the device.

The scripts authenticate as a dedicated **ingest user** that may only call the reporting method and cannot read any data.

Frappe keeps one record per Claude account with one row per Claude week. Each 5-hour window is counted once in its highest bucket (50–74 %, 75–89 %, 90–99 %, 100 %), recognised by its reset time, so several devices of the same person never count twice.

## Branches

| Branch | Frappe | Purpose |
| --- | --- | --- |
| `version-16` | v16 | Stable release for production. Use this branch. |
| `develop` | v16 | Latest development state. Not for production. |
| `version-17` | v17 | Will be created once Frappe v17 is available. |

Branch names follow the Frappe convention, so `bench get-app --branch version-16` matches the Frappe version of your bench. Changes are made on `develop` and merged into the version branches when they are stable. The links to scripts and skills in this README and in the in-app guides point to `version-16`.

## Requirements

- Frappe Framework v16. ERPNext or Frappe HR are **not** required.
- Claude Team plan; on every computer Claude Code signed in with the user's Claude account (Claude Desktop alone is not enough – see the in-app guide).
- Windows 10 21H2 / Windows 11 / Windows Server 2022 or newer for hidden execution (`conhost --headless`); Linux with `bash`, `curl` and `python3`.

## Installation

```bash
cd ~/frappe-bench
bench get-app --branch version-16 https://github.com/SRGgmbh/frappe-teamlimit_optimizer
bench --site <your-site> install-app teamlimit_optimizer
bench --site <your-site> migrate
```

On Frappe Cloud, add the repository with the branch `version-16` to a private bench and install the app on the site.

## Setup

1. Open **Teamlimit Settings**, enter the number of Claude users in your Team plan and check the colour thresholds.
2. Click **Reporting scripts → Set up ingest user**.
3. Click **Reporting scripts → Show install commands**. You get two ready-to-copy one-liners with your site address and the ingest key:

   **Windows** – as administrator in PowerShell, once per computer or terminal server, or as a GPO computer startup script:

   ```powershell
   & ([scriptblock]::Create((irm https://raw.githubusercontent.com/SRGgmbh/frappe-teamlimit_optimizer/version-16/scripts/install-windows.ps1))) -FrappeUrl "https://erp.example.com" -IngestAuth "token <api_key>:<api_secret>"
   ```

   **Linux** – as the user whose usage is reported:

   ```bash
   curl -fsSL https://raw.githubusercontent.com/SRGgmbh/frappe-teamlimit_optimizer/version-16/scripts/install-linux.sh | bash -s -- --url "https://erp.example.com" --auth "token <api_key>:<api_secret>"
   ```

4. Every user signs in to Claude Code once.
5. Assign the roles **Claude Usage Manager / User / Team** and create your **Claude Teams** and **Claude Projects**.
6. Upload the skills to your Claude organisation (see below).

Detailed step-by-step instructions – GPO, manual installation without the installer, interval, roles, writing good pool tasks – are part of the app: **Teamlimit Optimizer → Guides**. The in-app guides are currently available in German.

## Scripts

| File | Purpose |
| --- | --- |
| [`scripts/install-windows.ps1`](scripts/install-windows.ps1) | One-line installer for Windows: reporting script, configuration, scheduled task |
| [`scripts/install-linux.sh`](scripts/install-linux.sh) | One-line installer for Linux: reporting script, configuration, systemd timer or cron |
| [`scripts/windows/Teamlimit-Report.ps1`](scripts/windows/Teamlimit-Report.ps1) | Reporting script for Windows |
| [`scripts/windows/Teamlimit-Optimizer-Task.xml`](scripts/windows/Teamlimit-Optimizer-Task.xml) | Scheduled task for manual import |
| [`scripts/linux/teamlimit-report.sh`](scripts/linux/teamlimit-report.sh) | Reporting script for Linux |

The reporting scripts can also be downloaded from **Teamlimit Settings → Reporting scripts** with address and key already filled in.

## Skills

| Purpose | English | German |
| --- | --- | --- |
| Write a task for the pool together with Claude | [`pool-task-create`](skills/en/pool-task-create/SKILL.md) | [`aufgabe-einstellen`](skills/de/aufgabe-einstellen/SKILL.md) |
| Complete a task: check criteria, share result, write summary | [`pool-task-complete`](skills/en/pool-task-complete/SKILL.md) | [`aufgabe-abschliessen`](skills/de/aufgabe-abschliessen/SKILL.md) |
| Instruction for other AI assistants | [`pool-task-create-other-ai.md`](skills/en/pool-task-create-other-ai.md) | [`aufgabe-einstellen-andere-ki.md`](skills/de/aufgabe-einstellen-andere-ki.md) |

Ready-to-upload ZIP files are in [`skills/dist`](skills/dist). Change the Frappe address in the create skill before uploading. Both languages produce the same hand-over block, and the app reads English and German blocks.

## Roles

| Role | Access |
| --- | --- |
| System Manager | Setup, Claude Teams, assignments, guides, scripts |
| Claude Usage Manager | Overview, statistics, expired budget and “Who can help?” |
| Claude Usage User | “Who can help?” across all teams, task pool |
| Claude Usage Team | “Who can help?” within the own Claude Team only |
| Claude Usage Ingest | Only the ingest user of the reporting scripts |

Any desk user can create tasks for the pool.

## Important notes

- The usage values come from an endpoint that Claude Code uses internally and that is **not officially documented** by Anthropic. It may change or be rate-limited at any time; the reporting part is deliberately small so it can be replaced.
- All reports are shared by design: everyone with access sees everyone's usage. Members who should not appear simply do not get the script. Check works council and data protection requirements in your organisation before rollout.
- Reports are protected by the shared ingest key, not per person. A user could deliberately report wrong values for someone else; for the purpose of the app this was considered acceptable.

## Translations

The source language is English. A complete German translation is included in [`teamlimit_optimizer/locale/de.po`](teamlimit_optimizer/locale/de.po); the skills are available in both languages. Further languages are welcome via the usual Frappe translation workflow – please open a pull request against `develop`.

## Contributing

Issues and pull requests are welcome at [github.com/SRGgmbh/frappe-teamlimit_optimizer](https://github.com/SRGgmbh/frappe-teamlimit_optimizer/issues). Please base pull requests on `develop`.

## License

MIT – see [LICENSE](LICENSE). © 2026 SRG - Systemhaus GmbH
