# Copyright (c) 2026, SRG - Systemhaus GmbH and contributors
# For license information, please see LICENSE

import frappe
from frappe import _
from frappe.utils import get_datetime, now_datetime


def execute(filters=None):
	now = now_datetime()
	y = now.year
	months = [_("Jan"), _("Feb"), _("Mar"), _("Apr"), _("May"), _("Jun"), _("Jul"), _("Aug"), _("Sep"), _("Oct"), _("Nov"), _("Dec")]
	acc = {}
	for r in frappe.get_all(
		"Claude Usage Week", filters={"parenttype": "Claude Account", "week_reset": [">=", f"{y - 1}-01-01"]}, fields=["week_reset", "week_peak"]
	):
		dt = get_datetime(r.week_reset)
		a = acc.setdefault((dt.year, dt.month), [0.0, 0])
		a[0] += r.week_peak or 0
		a[1] += 1
	result = []
	for m in range(1, 13):
		cur, prev = acc.get((y, m)), acc.get((y - 1, m))
		result.append(
			{
				"month": months[m - 1],
				"this_year": round(cur[0] / cur[1], 1) if cur and (y, m) <= (now.year, now.month) else None,
				"last_year": round(prev[0] / prev[1], 1) if prev else None,
			}
		)
	columns = [
		{"fieldname": "month", "label": _("Month"), "fieldtype": "Data", "width": 80},
		{"fieldname": "this_year", "label": _("Avg Usage {0} %").format(y), "fieldtype": "Percent", "width": 160},
		{"fieldname": "last_year", "label": _("Avg Usage {0} %").format(y - 1), "fieldtype": "Percent", "width": 160},
	]
	chart = {
		"data": {"labels": [r["month"] for r in result], "datasets": [{"name": str(y), "values": [r["this_year"] or 0 for r in result]}, {"name": str(y - 1), "values": [r["last_year"] or 0 for r in result]}]},
		"type": "line",
		"fieldtype": "Percent",
	}
	return columns, result, None, chart
