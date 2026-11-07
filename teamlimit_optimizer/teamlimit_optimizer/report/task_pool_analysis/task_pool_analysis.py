# Copyright (c) 2026, SRG - Systemhaus GmbH and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import add_days, add_months, add_to_date, get_datetime, now_datetime, time_diff_in_hours


def execute(filters=None):
	now = now_datetime()
	tasks = frappe.get_all("Claude Task", fields=["status", "creation", "completed_at"])
	counts = {}
	for t in tasks:
		counts[t.status] = counts.get(t.status, 0) + 1
	mon = get_datetime(add_days(now.date(), -now.weekday()))
	result = []
	for i in range(11, -1, -1):
		ws = add_days(mon, -7 * i)
		we = add_days(ws, 7)
		created = sum(1 for t in tasks if ws <= get_datetime(t.creation) < we)
		done = sum(1 for t in tasks if t.completed_at and ws <= get_datetime(t.completed_at) < we)
		open_end = sum(1 for t in tasks if get_datetime(t.creation) < we and (not t.completed_at or get_datetime(t.completed_at) >= we))
		result.append(
			{
				"period": _("CW{0}").format(f"{get_datetime(ws).isocalendar()[1]:02d}"),
				"created": created,
				"done": done,
				"open_end": open_end,
				"quote": round(done * 100.0 / (done + open_end), 1) if (done + open_end) else None,
			}
		)
	columns = [
		{"fieldname": "period", "label": _("Week"), "fieldtype": "Data", "width": 90},
		{"fieldname": "created", "label": _("Created"), "fieldtype": "Int", "width": 100},
		{"fieldname": "done", "label": _("Done"), "fieldtype": "Int", "width": 100},
		{"fieldname": "open_end", "label": _("Open at Week End"), "fieldtype": "Int", "width": 160},
		{"fieldname": "quote", "label": _("Done %"), "fieldtype": "Percent", "width": 110},
	]
	chart = {
		"data": {"labels": [r["period"] for r in result], "datasets": [{"name": _("Created"), "values": [r["created"] for r in result]}, {"name": _("Done"), "values": [r["done"] for r in result]}]},
		"type": "bar",
		"fieldtype": "Int",
	}
	message = _("Currently: {0} open, {1} in progress, {2} with question, {3} done.").format(
		counts.get("Open", 0), counts.get("In Progress", 0), counts.get("Question", 0), counts.get("Done", 0)
	)
	return columns, result, message, chart
