# Copyright (c) 2026, SRG - Systemhaus GmbH and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import add_days, add_months, add_to_date, get_datetime, now_datetime, time_diff_in_hours


def _eff(pct, reset, now):
	if reset and get_datetime(reset) < now:
		return 0
	return pct or 0


def _work_fraction(reset, now, weekend):
	"""Share of working time of the current Claude week that has passed."""
	reset = get_datetime(reset)
	total = done = 0
	for i in range(168):
		h = add_to_date(reset, hours=-168 + i)
		if weekend or h.weekday() < 5:
			total += 1
			if h < now:
				done += 1
	return done / total if total else 0


def execute(filters=None):
	now = now_datetime()
	s = frappe.get_cached_doc("Teamlimit Settings")
	warn, crit, stale_h = s.warn_pct or 60, s.crit_pct or 90, s.stale_hours or 3
	result = []
	for m in frappe.get_all(
		"Claude Account",
		fields=["name", "claude_team", "seat_type", "weekend_work", "five_pct", "five_reset", "week_pct", "week_reset", "last_seen"],
	):
		f5 = _eff(m.five_pct, m.five_reset, now)
		fw = _eff(m.week_pct, m.week_reset, now)
		free = round(max(0, min(100 - f5, 100 - fw)), 1)
		stale = (not m.last_seen) or time_diff_in_hours(now, m.last_seen) > stale_h
		w = frappe.get_all(
			"Claude Usage Week",
			filters={"parent": m.name, "parenttype": "Claude Account"},
			fields=["windows", "b75", "b90", "b100"],
			order_by="week_reset desc",
			limit=1,
		)
		w = w[0] if w else frappe._dict()
		target, tempo, rest = None, "", ""
		if m.week_reset and get_datetime(m.week_reset) > now:
			left_h = time_diff_in_hours(m.week_reset, now)
			target = round(_work_fraction(m.week_reset, now, m.weekend_work) * 100, 0)
			diff = fw - target
			tempo = _("ahead") if diff > 10 else (_("behind") if diff < -10 else _("on track"))
			rest = _("{0} % in {1} h").format(int(round(100 - fw)), int(round(left_h)))
		result.append(
			{
				"member": m.name,
				"team": m.claude_team,
				"seat": _(m.seat_type),
				"five": f5,
				"five_reset": m.five_reset,
				"week": fw,
				"week_reset": m.week_reset,
				"target": target,
				"tempo": tempo,
				"rest": rest,
				"free": free,
				"units": round(free * (5 if m.seat_type == "Premium" else 1) / 100.0, 2),
				"windows": w.get("windows") or 0,
				"b75": (w.get("b75") or 0) + (w.get("b90") or 0) + (w.get("b100") or 0),
				"b100": w.get("b100") or 0,
				"last_seen": m.last_seen,
				"state": _("outdated") if stale else _("current"),
				"_warn": warn,
				"_crit": crit,
			}
		)
	result.sort(key=lambda r: -r["free"])
	columns = [
		{"fieldname": "member", "label": _("Claude Account"), "fieldtype": "Link", "options": "Claude Account", "width": 220},
		{"fieldname": "team", "label": _("Claude Team"), "fieldtype": "Data", "width": 120},
		{"fieldname": "seat", "label": _("Seat"), "fieldtype": "Data", "width": 90},
		{"fieldname": "five", "label": _("5 h %"), "fieldtype": "Percent", "width": 90},
		{"fieldname": "five_reset", "label": _("5 h Reset"), "fieldtype": "Datetime", "width": 150},
		{"fieldname": "week", "label": _("Week %"), "fieldtype": "Percent", "width": 90},
		{"fieldname": "week_reset", "label": _("Weekly Reset"), "fieldtype": "Datetime", "width": 150},
		{"fieldname": "target", "label": _("Week Target %"), "fieldtype": "Percent", "width": 100},
		{"fieldname": "tempo", "label": _("Pace"), "fieldtype": "Data", "width": 100},
		{"fieldname": "rest", "label": _("Left Until Reset"), "fieldtype": "Data", "width": 120},
		{"fieldname": "free", "label": _("Free %"), "fieldtype": "Percent", "width": 90},
		{"fieldname": "units", "label": _("Free (Standard Units)"), "fieldtype": "Float", "width": 120, "hidden": 1},
		{"fieldname": "windows", "label": _("Windows This Week"), "fieldtype": "Int", "width": 100, "hidden": 1},
		{"fieldname": "b75", "label": _("Thereof ≥ 75 %"), "fieldtype": "Int", "width": 90, "hidden": 1},
		{"fieldname": "b100", "label": _("Thereof 100 %"), "fieldtype": "Int", "width": 90, "hidden": 1},
		{"fieldname": "last_seen", "label": _("Last Reported"), "fieldtype": "Datetime", "width": 150},
		{"fieldname": "state", "label": _("Status"), "fieldtype": "Data", "width": 90},
	]
	return columns, result
