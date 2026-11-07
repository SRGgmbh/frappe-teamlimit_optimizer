# Copyright (c) 2026, SRG - Systemhaus GmbH and contributors
# For license information, please see LICENSE

import json
import os

import frappe
from frappe import _
from frappe.utils import add_days, flt, get_datetime, now_datetime, time_diff_in_seconds

INGEST_ROLE = "Claude Usage Ingest"
TOLERANCE_SECONDS = 1800  # a 5-h window and a week are recognised by their reset time ± 30 min


def _has_role(*roles):
	user_roles = frappe.get_roles()
	return "Administrator" in user_roles or any(r in user_roles for r in roles)


def _bucket(pct):
	if pct >= 100:
		return 100
	if pct >= 90:
		return 90
	if pct >= 75:
		return 75
	if pct >= 50:
		return 50
	return 0


def _same_time(a, b):
	if not a or not b:
		return False
	return abs(time_diff_in_seconds(a, b)) <= TOLERANCE_SECONDS


def _num(value):
	return None if value in (None, "") else flt(value)


@frappe.whitelist(methods=["POST"])
def report(**kwargs):
	"""Receives the usage of one Claude account from a reporting script.

	Only numbers leave the device: e-mail, seat tier and percentages with reset times.
	"""
	if not _has_role(INGEST_ROLE, "System Manager"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	d = frappe._dict(kwargs)
	email = (d.get("email") or "").strip().lower()
	if not email or "@" not in email:
		frappe.throw(_("E-mail missing"))

	five = _num(d.get("five_pct"))
	week = _num(d.get("week_pct"))
	five_reset = get_datetime(d.five_reset) if d.get("five_reset") else None
	week_reset = get_datetime(d.week_reset) if d.get("week_reset") else None

	frappe.db.get_value("Claude Account", email, "name", for_update=True)
	if frappe.db.exists("Claude Account", email):
		acc = frappe.get_doc("Claude Account", email)
	else:
		acc = frappe.new_doc("Claude Account")
		acc.email = email

	tier = d.get("rate_limit_tier") or ""
	acc.rate_limit_tier = tier
	acc.subscription_type = d.get("subscription_type") or ""
	if tier:
		acc.seat_type = "Premium" if "max" in tier else "Standard"
	acc.five_pct = five or 0
	acc.five_reset = five_reset
	acc.week_pct = week or 0
	acc.week_reset = week_reset
	acc.last_seen = now_datetime()

	row = None
	if week_reset:
		for r in acc.weeks:
			if _same_time(r.week_reset, week_reset):
				row = r
		if not row:
			row = acc.append(
				"weeks",
				{"week_reset": week_reset, "week_peak": 0, "windows": 0, "b50": 0, "b75": 0, "b90": 0, "b100": 0},
			)
		if week is not None and week > (row.week_peak or 0):
			row.week_peak = week
		if d.get("extra_used") not in (None, ""):
			row.extra_used = flt(d.get("extra_used"))

	# Each 5-h window counts once, in its highest bucket. Two devices of the same
	# account report the same reset time and therefore never count twice.
	if five_reset and five is not None and row:
		new_bucket = _bucket(five)
		if _same_time(acc.cur_window_reset, five_reset):
			old_bucket = acc.cur_window_bucket or 0
			if new_bucket > old_bucket:
				target = row
				for r in acc.weeks:
					if _same_time(r.week_reset, acc.cur_window_week):
						target = r
				if old_bucket:
					target.set(f"b{old_bucket}", max(0, (target.get(f"b{old_bucket}") or 0) - 1))
				target.set(f"b{new_bucket}", (target.get(f"b{new_bucket}") or 0) + 1)
				acc.cur_window_bucket = new_bucket
		else:
			row.windows = (row.windows or 0) + 1
			if new_bucket:
				row.set(f"b{new_bucket}", (row.get(f"b{new_bucket}") or 0) + 1)
			acc.cur_window_reset = five_reset
			acc.cur_window_bucket = new_bucket
			acc.cur_window_week = row.week_reset

	acc.flags.ignore_permissions = True
	acc.save()
	return {"ok": True, "account": acc.name}


@frappe.whitelist(methods=["POST"])
def task(task, action, **kwargs):
	"""Takes over, releases, asks about or completes a task from the task pool."""
	if not frappe.db.exists("Claude Task", task):
		frappe.throw(_("Task not found"))
	user = frappe.session.user
	frappe.db.get_value("Claude Task", task, "status", for_update=True)
	doc = frappe.get_doc("Claude Task", task)
	now = now_datetime()

	if action == "claim":
		if doc.status == "In Progress" and doc.claimed_by == user:
			pass
		elif doc.status != "Open":
			frappe.throw(_("This task has already been taken by {0}.").format(doc.claimed_by or _("someone else")))
		else:
			doc.status = "In Progress"
			doc.claimed_by = user
			doc.claimed_at = now
	elif action == "release":
		doc.status = "Open"
		doc.claimed_by = None
		doc.claimed_at = None
	elif action == "question":
		doc.status = "Question"
		doc.notes_question = kwargs.get("text") or ""
	elif action == "done":
		if not kwargs.get("result_url"):
			frappe.throw(_("Please enter a result link."))
		doc.status = "Done"
		doc.result_url = kwargs.get("result_url")
		doc.result_summary = kwargs.get("summary") or ""
		doc.completed_at = now
		doc.claimed_by = doc.claimed_by or user
		email = (kwargs.get("claude_email") or "").strip().lower()
		doc.claude_email = email or frappe.db.get_value("Claude Account", {"frappe_user": user}, "name") or ""
	else:
		frappe.throw(_("Unknown action"))

	doc.flags.ignore_permissions = True
	doc.save()
	return {"status": doc.status, "claimed_by": doc.claimed_by}


def _month_avg(year, month):
	start = f"{year:04d}-{month:02d}-01"
	end = add_days(frappe.utils.add_months(start, 1), -1)
	rows = frappe.get_all(
		"Claude Usage Week",
		filters={"parenttype": "Claude Account", "week_reset": ["between", [start, end]]},
		pluck="week_peak",
	)
	return round(sum(r or 0 for r in rows) / len(rows), 1) if rows else 0


@frappe.whitelist()
def kpi(filters=None):
	"""Values for the number cards on the dashboard. Contains no personal data."""
	if isinstance(filters, str):
		filters = json.loads(filters or "{}")
	key = (filters or {}).get("kpi")
	now = now_datetime()
	value, fieldtype = 0, "Int"
	active = frappe.db.count("Claude Account", {"last_seen": [">=", add_days(now, -7)]})
	monday = add_days(now.date(), -now.weekday())

	if key == "active":
		value = active
	elif key == "missing":
		expected = frappe.db.get_single_value("Teamlimit Settings", "expected_accounts") or 0
		value = max(0, expected - active)
	elif key == "util_month":
		value, fieldtype = _month_avg(now.year, now.month), "Percent"
	elif key == "util_prev_month":
		prev = get_datetime(frappe.utils.add_months(now, -1))
		value, fieldtype = _month_avg(prev.year, prev.month), "Percent"
	elif key == "util_prev_year":
		value, fieldtype = _month_avg(now.year - 1, now.month), "Percent"
	elif key == "limit_week":
		value = sum(
			frappe.get_all(
				"Claude Usage Week",
				filters={"parenttype": "Claude Account", "week_reset": [">=", monday]},
				pluck="b100",
			)
		)
	elif key == "wasted":
		peaks = frappe.get_all(
			"Claude Usage Week",
			filters={"parenttype": "Claude Account", "week_reset": ["between", [add_days(now, -28), now]]},
			pluck="week_peak",
		)
		value = round(sum(max(0, 100 - (p or 0)) for p in peaks) / len(peaks), 1) if peaks else 0
		fieldtype = "Percent"
	elif key == "open_tasks":
		value = frappe.db.count("Claude Task", {"status": "Open"})
	elif key == "done_week":
		value = frappe.db.count("Claude Task", {"status": "Done", "completed_at": [">=", monday]})
	return {"value": value, "fieldtype": fieldtype}


@frappe.whitelist()
def setup_ingest_user():
	"""Creates the ingest user for the reporting scripts and (re)generates its API keys."""
	frappe.only_for("System Manager")
	from frappe.core.doctype.user.user import generate_keys

	host = (frappe.local.site or "localhost").split(":")[0]
	email = f"teamlimit-ingest@{host}" if "." in host else "teamlimit-ingest@example.com"
	if not frappe.db.exists("User", email):
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "Teamlimit Ingest",
				"send_welcome_email": 0,
				"user_type": "System User",
				"roles": [{"role": INGEST_ROLE}],
			}
		)
		user.flags.ignore_permissions = True
		user.insert()
	secret = generate_keys(email)["api_secret"]
	settings = frappe.get_single("Teamlimit Settings")
	settings.ingest_user = email
	settings.ingest_api_key = frappe.db.get_value("User", email, "api_key")
	settings.ingest_api_secret = secret
	settings.flags.ignore_permissions = True
	settings.save()
	return {"user": email}


REPO = "SRGgmbh/frappe-teamlimit_optimizer"
BRANCH = "version-16"
RAW = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/scripts"

# the reporting scripts live in the repository root, folder "scripts"
SCRIPT_FILES = {
	"windows": ("windows/Teamlimit-Report.ps1", "Teamlimit-Report.ps1"),
	"linux": ("linux/teamlimit-report.sh", "teamlimit-report.sh"),
	"task": ("windows/Teamlimit-Optimizer-Task.xml", "Teamlimit-Optimizer-Task.xml"),
}


def _ingest_auth():
	settings = frappe.get_single("Teamlimit Settings")
	if not settings.ingest_api_key:
		frappe.throw(_("Please set up the ingest user first."))
	return f"token {settings.ingest_api_key}:{settings.get_password('ingest_api_secret')}"


@frappe.whitelist()
def get_install_commands():
	"""One-line install commands for Windows and Linux with this site's address and the ingest key."""
	frappe.only_for("System Manager")
	url = frappe.utils.get_url()
	auth = _ingest_auth()
	return {
		"windows": f"& ([scriptblock]::Create((irm {RAW}/install-windows.ps1))) -FrappeUrl \"{url}\" -IngestAuth \"{auth}\"",
		"linux": f"curl -fsSL {RAW}/install-linux.sh | bash -s -- --url \"{url}\" --auth \"{auth}\"",
	}


@frappe.whitelist()
def download_script(kind="windows"):
	"""Delivers a reporting script with this site's address and the ingest key filled in."""
	frappe.only_for("System Manager")
	if kind not in SCRIPT_FILES:
		frappe.throw(_("Unknown script"))
	template, filename = SCRIPT_FILES[kind]
	path = os.path.join(os.path.dirname(frappe.get_app_path("teamlimit_optimizer")), "scripts", template)
	with open(path, encoding="utf-8-sig") as f:
		content = f.read()

	if kind != "task":
		content = content.replace("__FRAPPE_URL__", frappe.utils.get_url()).replace("__INGEST_AUTH__", _ingest_auth())

	frappe.response["filename"] = filename
	frappe.response["filecontent"] = content.encode("utf-8-sig" if kind == "windows" else "utf-8")
	frappe.response["type"] = "download"
