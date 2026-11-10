# Copyright (c) 2026, SRG - Systemhaus GmbH and contributors
# For license information, please see LICENSE

import frappe
from frappe import _
from frappe.utils import add_days, get_datetime, now_datetime


def _snap(v):
	b = 0
	for x in (50, 75, 90, 100):
		if v >= x:
			b = x
	return b or 50


def execute(filters=None):
	f = filters or {}
	monthly = f.get("granularity") == "Month"
	metric = f.get("metric") or "usage"
	s = frappe.get_cached_doc("Teamlimit Settings")
	w_b, c_b = _snap(s.warn_pct or 60), _snap(s.crit_pct or 90)
	now = now_datetime()
	months = [_("Jan"), _("Feb"), _("Mar"), _("Apr"), _("May"), _("Jun"), _("Jul"), _("Aug"), _("Sep"), _("Oct"), _("Nov"), _("Dec")]
	agg = {}
	for r in frappe.get_all(
		"Claude Usage Week",
		filters={"parenttype": "Claude Account"},
		fields=["week_reset", "week_peak", "windows", "b50", "b75", "b90", "b100"],
		order_by="week_reset asc",
	):
		if not r.week_reset:
			continue
		dt = get_datetime(r.week_reset)
		key = (dt.year, dt.month) if monthly else tuple(dt.isocalendar()[:2])
		a = agg.setdefault(key, {"n": 0, "sum": 0.0, "windows": 0, "orange": 0, "red": 0, "dt": dt})
		bs = {50: r.b50 or 0, 75: r.b75 or 0, 90: r.b90 or 0, 100: r.b100 or 0}
		a["n"] += 1
		a["sum"] += r.week_peak or 0
		a["windows"] += r.windows or 0
		a["red"] += sum(v for b, v in bs.items() if b >= c_b)
		a["orange"] += sum(v for b, v in bs.items() if w_b <= b < c_b)

	def avg(k):
		a = agg.get(k)
		return round(a["sum"] / a["n"], 1) if a and a["n"] else None

	result = []
	if monthly:
		keys, y, m = [], now.year, now.month
		for _i in range(12):
			keys.insert(0, (y, m))
			m -= 1
			if m == 0:
				m, y = 12, y - 1
		for k in keys:
			result.append({"period": months[k[1] - 1], "avg_peak": avg(k), "prev_peak": avg((k[0] - 1, k[1]))})
	else:
		tasks = frappe.get_all("Claude Task", fields=["creation", "completed_at"])
		for k in sorted(agg)[-6:]:
			a = agg[k]
			mon = get_datetime(add_days(a["dt"].date(), -a["dt"].weekday()))
			wend = add_days(mon, 7)
			done = sum(1 for t in tasks if t.completed_at and mon <= get_datetime(t.completed_at) < wend)
			open_end = sum(1 for t in tasks if get_datetime(t.creation) < wend and (not t.completed_at or get_datetime(t.completed_at) >= wend))
			result.append(
				{
					"period": _("CW{0}").format(f"{k[1]:02d}"),
					"avg_peak": avg(k),
					"windows": a["windows"],
					"ok": max(0, a["windows"] - a["orange"] - a["red"]),
					"warn": a["orange"],
					"crit": a["red"],
					"tasks_done": done,
					"tasks_open": open_end,
					"task_quote": round(done * 100.0 / (done + open_end), 1) if (done + open_end) else None,
				}
			)

	columns = [
		{"fieldname": "period", "label": _("Period"), "fieldtype": "Data", "width": 100},
		{"fieldname": "avg_peak", "label": _("Avg Usage %"), "fieldtype": "Percent", "width": 130},
	]
	if monthly:
		columns.append({"fieldname": "prev_peak", "label": _("Previous Year %"), "fieldtype": "Percent", "width": 120})
	else:
		columns += [
			{"fieldname": "windows", "label": _("5-h Windows"), "fieldtype": "Int", "width": 100},
			{"fieldname": "ok", "label": _("Below Yellow"), "fieldtype": "Int", "width": 100},
			{"fieldname": "warn", "label": _("Yellow Reached"), "fieldtype": "Int", "width": 110},
			{"fieldname": "crit", "label": _("Red Reached"), "fieldtype": "Int", "width": 110},
			{"fieldname": "tasks_done", "label": _("Tasks Done"), "fieldtype": "Int", "width": 110},
			{"fieldname": "tasks_open", "label": _("Tasks Open at Week End"), "fieldtype": "Int", "width": 170},
			{"fieldname": "task_quote", "label": _("Tasks Done %"), "fieldtype": "Percent", "width": 120},
		]
	labels = [r["period"] for r in result]
	val = lambda k: [r.get(k) or 0 for r in result]  # noqa: E731
	if metric == "sessions":
		chart = {
			"data": {"labels": labels, "datasets": [{"name": _("Below Yellow"), "values": val("ok")}, {"name": _("Yellow Reached"), "values": val("warn")}, {"name": _("Red Reached"), "values": val("crit")}]},
			"type": "bar",
			"fieldtype": "Int",
			"barOptions": {"stacked": 1},
			"colors": ["#2E8540", "#F5A623", "#E24C4C"],
		}
	elif monthly:
		chart = {"data": {"labels": labels, "datasets": [{"name": _("Last 12 Months"), "values": val("avg_peak")}, {"name": _("Previous Year"), "values": val("prev_peak")}]}, "type": "line", "fieldtype": "Percent"}
	else:
		chart = {"data": {"labels": labels, "datasets": [{"name": _("Avg Usage"), "values": val("avg_peak")}, {"name": _("Tasks Done"), "values": val("task_quote")}]}, "type": "line", "fieldtype": "Percent"}
	return columns, result, None, chart
