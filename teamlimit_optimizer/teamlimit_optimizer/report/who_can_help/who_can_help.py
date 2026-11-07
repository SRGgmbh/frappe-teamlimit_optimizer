# Copyright (c) 2026, SRG - Systemhaus GmbH and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import add_days, add_months, add_to_date, get_datetime, now_datetime, time_diff_in_hours


def _eff(pct, reset, now):
	if reset and get_datetime(reset) < now:
		return 0
	return pct or 0


def execute(filters=None):
	now = now_datetime()
	user = frappe.session.user
	roles = frappe.get_roles()
	wide = bool({"Claude Usage Manager", "Claude Usage User", "System Manager", "Administrator"} & set(roles))
	me = frappe.db.get_value("Claude Account", {"frappe_user": user}, ["name", "claude_team", "week_pct", "week_reset"], as_dict=True)
	my_team = me.claude_team if me else None
	s = frappe.get_cached_doc("Teamlimit Settings")
	threshold, warn, crit, stale_h = s.min_free_pct or 25, s.warn_pct or 60, s.crit_pct or 90, s.stale_hours or 3

	columns = [
		{"fieldname": "rank", "label": _("Rank"), "fieldtype": "Int", "width": 60},
		{"fieldname": "member", "label": _("Colleague"), "fieldtype": "Data", "width": 240},
		{"fieldname": "team", "label": _("Claude Team"), "fieldtype": "Data", "width": 130},
		{"fieldname": "seat", "label": _("Seat"), "fieldtype": "Data", "width": 90},
		{"fieldname": "free", "label": _("Free %"), "fieldtype": "Percent", "width": 100},
		{"fieldname": "stage", "label": _("Level"), "fieldtype": "Data", "width": 190},
		{"fieldname": "last_seen", "label": _("Last Reported"), "fieldtype": "Datetime", "width": 150},
	]
	if not wide and not my_team:
		return columns, [], _("Your Frappe user is not linked to a Claude account with a Claude Team. Please ask the administrator to add the link.")

	flt = {} if wide else {"claude_team": my_team}
	cands, stale_list = [], []
	for m in frappe.get_all(
		"Claude Account", filters=flt, fields=["name", "claude_team", "seat_type", "five_pct", "five_reset", "week_pct", "week_reset", "last_seen"]
	):
		if me and m.name == me.name:
			continue
		if (not m.last_seen) or time_diff_in_hours(now, m.last_seen) > stale_h:
			stale_list.append(m)
			continue
		free = round(max(0, min(100 - _eff(m.five_pct, m.five_reset, now), 100 - _eff(m.week_pct, m.week_reset, now))), 1)
		prem = m.seat_type == "Premium"
		own = bool(my_team) and m.claude_team == my_team
		cands.append({"stage": (3 if prem else 1) + (0 if own else 1), "member": m.name, "team": m.claude_team, "seat": m.seat_type, "free": free, "prem": prem, "last_seen": m.last_seen})

	std_ok = any((not c["prem"]) and c["free"] >= threshold for c in cands)
	cands = [c for c in cands if c["free"] >= threshold and not (std_ok and c["prem"])]
	cands.sort(key=lambda c: (c["stage"], -c["free"]))
	labels = {1: _("Own team"), 2: _("Other team"), 3: _("Premium, own team"), 4: _("Premium, other team")}
	result = [
		{"rank": i + 1, "member": c["member"], "team": c["team"], "seat": _(c["seat"]), "free": c["free"], "stage": labels[c["stage"]], "last_seen": c["last_seen"], "_warn": warn, "_crit": crit}
		for i, c in enumerate(cands)
	]

	hint = []
	if me and me.week_reset and get_datetime(me.week_reset) > now:
		hint.append(_("Your weekly budget: {0} % free, reset in {1} h.").format(int(round(100 - (me.week_pct or 0))), int(round(time_diff_in_hours(me.week_reset, now)))))
	open_tasks = frappe.db.count("Claude Task", {"status": "Open"})
	if open_tasks:
		hint.append(_("{0} open tasks are waiting in the task pool.").format(open_tasks))
	if not result:
		hint.append(_("Right now nobody has at least {0} % free.").format(threshold))
	if stale_list:
		result.append({"member": _("No current information"), "_section": 1})
		for m in stale_list:
			last_free = round(max(0, min(100 - (m.five_pct or 0), 100 - (m.week_pct or 0))), 1)
			result.append({"member": m.name, "team": m.claude_team, "seat": _(m.seat_type), "free": last_free, "stage": _("No current information"), "last_seen": m.last_seen, "_stale": 1})
	expected = s.expected_accounts or 0
	known = frappe.db.count("Claude Account")
	if expected > known:
		hint.append(_("{0} account(s) have never reported.").format(expected - known))
	return columns, result, " ".join(hint)
