# Copyright (c) 2026, SRG - Systemhaus GmbH and contributors
# For license information, please see LICENSE

import frappe
from frappe import _
from frappe.utils import add_days, add_months, add_to_date, get_datetime, now_datetime, time_diff_in_hours

POINTS = {"S": 1, "M": 2, "L": 4}


def execute(filters=None):
	period = (filters or {}).get("period") or "This Week"
	now = now_datetime()
	mon = add_days(now.date(), -now.weekday())
	start = {"This Week": mon, "Last 4 Weeks": add_days(mon, -21), "This Year": f"{now.year}-01-01"}.get(period, mon)
	agg = {}
	for t in frappe.get_all("Claude Task", filters={"status": "Done", "completed_at": [">=", start]}, fields=["claude_email", "claimed_by", "effort"]):
		k = t.claude_email or t.claimed_by or _("unknown")
		e = (t.effort or "S")[0]
		a = agg.setdefault(k, {"tasks": 0, "points": 0, "S": 0, "M": 0, "L": 0})
		a["tasks"] += 1
		a["points"] += POINTS.get(e, 1)
		a[e] = a.get(e, 0) + 1
	rows = [
		{"account": k, "team": frappe.db.get_value("Claude Account", k, "claude_team") if "@" in k else None, "tasks": a["tasks"], "points": a["points"], "s": a["S"], "m": a["M"], "l": a["L"]}
		for k, a in agg.items()
	]
	rows.sort(key=lambda r: (-r["points"], -r["tasks"]))
	for i, r in enumerate(rows):
		r["rank"] = i + 1
	columns = [
		{"fieldname": "rank", "label": _("Rank"), "fieldtype": "Int", "width": 60},
		{"fieldname": "account", "label": _("Claude Account"), "fieldtype": "Data", "width": 260},
		{"fieldname": "team", "label": _("Claude Team"), "fieldtype": "Data", "width": 130},
		{"fieldname": "points", "label": _("Points (S 1 / M 2 / L 4)"), "fieldtype": "Int", "width": 170},
		{"fieldname": "tasks", "label": _("Tasks"), "fieldtype": "Int", "width": 90},
		{"fieldname": "s", "label": "S", "fieldtype": "Int", "width": 50},
		{"fieldname": "m", "label": "M", "fieldtype": "Int", "width": 50},
		{"fieldname": "l", "label": "L", "fieldtype": "Int", "width": 50},
	]
	message = (
		_("Biggest helper: {0} with {1} points.").format(rows[0]["account"], rows[0]["points"])
		if rows
		else _("No task has been completed in the selected period yet.")
	)
	return columns, rows, message
