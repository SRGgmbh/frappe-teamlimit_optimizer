<p align="center">
  <img src="teamlimit_optimizer/public/images/logo.svg" width="96" alt="Teamlimit Optimizer logo">
</p>

<h1 align="center">Teamlimit Optimizer</h1>
<p align="center"><b>for Claude by Anthropic</b> · a Frappe app · German UI included</p>

Every member of a Claude Team plan has their own usage limits – a 5-hour session window and a weekly limit. Limits cannot be transferred between seats, and budget that is not used by the weekly reset is gone. Teamlimit Optimizer makes those limits visible for the whole team and helps to use them fully:

- **Live usage of all members** – 5-hour window and week, with colour thresholds, pace against the week and time left until the reset.
- **Who can help?** – suggests colleagues with free capacity: own Claude Team first, standard seats before premium seats.
- **Task pool** – ready-made prompts that anyone with spare budget can start in Claude Desktop with one click, including take-over lock, questions, result link and notifications to the requester.
- **Reports** – trend, year comparison, task pool analysis, helpers of the week and expired budget (with the cause: tasks were available vs. the pool was empty).
- **Skills** for Claude to write good pool tasks and to close them, plus an instruction for other AI assistants (ChatGPT, Copilot, Gemini).

> **Not an official Anthropic product.** Claude and Anthropic are trademarks of Anthropic, PBC. This app only refers to them descriptively.

## How it works

A small reporting script runs on every computer (Windows: PowerShell via the Task Scheduler, hidden; Linux: systemd timer or cron) once an hour. It reads the signed-in user's usage from the local Claude Code sign-in and sends **only** the e-mail address, seat tier, percentages and reset times to Frappe. The Claude token never leaves the device.

The scripts authenticate as a dedicated **ingest user** that may only call the reporting method and cannot read any data. Address and key are filled in when an administrator downloads the scripts from the settings.

Frappe keeps one record per Claude account with one row per Claude week. Each 5-hour window is counted once in its highest bucket (50–74 %, 75–89 %, 90–99 %, 100 %), recognised by its reset time, so several devices of the same person never count twice.

## Requirements

- Frappe Framework v15 or v16 (developed and tested against v16). ERPNext or Frappe HR are **not** required.
- Claude Team plan; on every computer Claude Code signed in with the user's Claude account (Claude Desktop alone is not enough – see the in-app guide).
- Windows 10 21H2 / Windows 11 / Windows Server 2022 or newer for hidden execution (`conhost --headless`); Linux with `bash`, `curl` and `python3`.

## Installation

```bash
cd ~/frappe-bench
bench get-app https://github.com/<your-org>/teamlimit_optimizer
bench --site <your-site> install-app teamlimit_optimizer
bench --site <your-site> migrate
```

On Frappe Cloud, add the repository to a private bench and install the app on the site.

## Setup

1. Open **Teamlimit Settings** – enter the number of Claude users in your Team plan and check the colour thresholds.
2. In the settings click **Reporting scripts → Set up ingest user**.
3. Download the Windows script, the Linux script and the scheduled task (XML) from the same menu and roll them out (GPO, Intune or manually).
4. Every user signs in to Claude Code once.
5. Assign the roles **Claude Usage Manager / User / Team** to your Frappe users and create your **Claude Teams** and **Claude Projects**.
6. Distribute the skills from the [`skills`](skills) folder to your Claude organisation (adjust the Frappe address in `aufgabe-einstellen` first).

Detailed, step-by-step instructions – including GPO settings, systemd units and how to write good pool tasks – are part of the app: **Teamlimit Optimizer → Guides**. The guides are currently available in German.

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
- All reports are shared by design: everyone with access sees everyone's usage. Members who should not appear simply do not get the script (e.g. GPO security filtering). Check works council and data protection requirements in your organisation before rollout.
- Reports are protected by the shared ingest key, not per person. A user could deliberately report wrong values for someone else; for the purpose of the app this was considered acceptable.

## Translations

The source language is English. A complete German translation is included in `teamlimit_optimizer/locale/de.po`. Further languages are welcome via the usual Frappe translation workflow.

## License

MIT – see [license.txt](license.txt). © 2026 SRG - Systemhaus GmbH
