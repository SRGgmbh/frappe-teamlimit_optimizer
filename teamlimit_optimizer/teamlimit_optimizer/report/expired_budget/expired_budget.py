# Copyright (c) 2026, SRG - Systemhaus GmbH and contributors
# For license information, please see LICENSE

import frappe
from frappe import _
from frappe.utils import add_days, add_months, add_to_date, get_datetime, now_datetime, time_diff_in_hours


def execute(filters=None):
	want = (filters or {}).get("cause") or "All"
	now = now_datetime()
	since = add_days(now, -56)
	tasks = frappe.get_all("Claude Task", fields=["creation", "claimed_at"])
	weeks = {}
	for w in frappe.get_all(
		"Claude Usage Week",
		filters={"parenttype": "Claude Account", "week_reset": ["between", [since, now]]},
		fields=["parent", "week_reset", "week_peak"],
	):
		wasted = round(max(0, 100 - (w.week_peak or 0)), 1)
		if wasted <= 0:
			continue
		reset = get_datetime(w.week_reset)
		key = reset.isocalendar()[1]
		acc = frappe.db.get_value("Claude Account", w.parent, ["claude_team", "seat_type"], as_dict=True) or frappe._dict()
		weeks.setdefault(key, []).append(
			{"reset": reset, "account": w.parent, "team": acc.claude_team, "seat": acc.seat_type, "wasted": wasted, "weight": 5 if acc.seat_type == "Premium" else 1}
		)

	cause_open, cause_none = _("Tasks open"), _("No tasks in the pool")
	result = []
	for key, rows in weeks.items():
		resets = [r["reset"] for r in rows]
		# a week counts as "tasks open" if a task was waiting in the pool at any reset of that week
		any_open = sum(
			1
			for t in tasks
			if any(get_datetime(t.creation) < rs and (not t.claimed_at or get_datetime(t.claimed_at) >= rs) for rs in resets)
		)
		period = _("CW{0}").format(f"{key:02d}")
		latest = str(max(resets))
		if any_open:
			if want == "No tasks in the pool":
				continue
			for r in rows:
				result.append(
					{"period": period, "reset": r["reset"], "account": r["account"], "team": r["team"], "seat": _(r["seat"] or ""), "wasted": r["wasted"],
					 "budgets": round(r["wasted"] * r["weight"] / 100.0, 2), "open": any_open, "cause": cause_open, "sortkey": str(r["reset"]), "is_total": 0}
				)
		else:
			if want == "Tasks open":
				continue
			result.append(
				{"period": period, "reset": None, "account": _("All accounts ({0})").format(len(rows)), "team": "", "seat": "",
				 "wasted": round(sum(r["wasted"] for r in rows) / len(rows), 1), "budgets": round(sum(r["wasted"] * r["weight"] for r in rows) / 100.0, 2),
				 "open": 0, "cause": cause_none, "sortkey": latest, "is_total": 1}
			)
	result.sort(key=lambda r: (r["sortkey"][:10], r["is_total"], r["wasted"]), reverse=True)
	columns = [
		{"fieldname": "period", "label": _("Week"), "fieldtype": "Data", "width": 80},
		{"fieldname": "reset", "label": _("Reset"), "fieldtype": "Datetime", "width": 150},
		{"fieldname": "account", "label": _("Claude Account"), "fieldtype": "Data", "width": 250},
		{"fieldname": "team", "label": _("Claude Team"), "fieldtype": "Data", "width": 130},
		{"fieldname": "seat", "label": _("Seat"), "fieldtype": "Data", "width": 90},
		{"fieldname": "wasted", "label": _("Expired %"), "fieldtype": "Percent", "width": 110},
		{"fieldname": "budgets", "label": _("= Standard Weekly Budgets"), "fieldtype": "Float", "width": 180},
		{"fieldname": "open", "label": _("Open Tasks at the Resets"), "fieldtype": "Int", "width": 180},
		{"fieldname": "cause", "label": _("Cause"), "fieldtype": "Data", "width": 180},
	]
	message = _(
		"Weeks of the last 8 weeks with expired budget. “Tasks open”: tasks were waiting in the pool at at least one reset of the week, listed per account. "
		"“No tasks in the pool”: no task was waiting at any reset of the week, one total row for all accounts; “Expired %” is the average there. "
		"“= Standard weekly budgets” converts into full budgets of a standard seat: 100 % of a standard seat = 1, 100 % of a premium seat = 5."
	)
	return columns, result, message
