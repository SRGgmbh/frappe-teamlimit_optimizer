# Copyright (c) 2026, SRG - Systemhaus GmbH and contributors
# For license information, please see LICENSE

import frappe
from frappe import _
from frappe.utils import add_days, get_datetime, now_datetime

WEEKS = 8
PREMIUM_WEIGHT = 5
WIDE_ROLES = {"Claude Usage Manager", "Claude Usage User", "System Manager", "Administrator"}


def execute(filters=None):
	filters = frappe._dict(filters or {})
	now = now_datetime()

	# Claude Usage Team only sees its own team, like "Who can help?"
	team = filters.get("claude_team")
	if not WIDE_ROLES & set(frappe.get_roles()):
		my_team = frappe.db.get_value("Claude Account", {"frappe_user": frappe.session.user}, "claude_team")
		if not my_team:
			return [], [], _("Your Frappe user is not linked to a Claude account with a Claude Team. Please ask the administrator to add the link.")
		team = my_team

	accounts = {
		a.name: a
		for a in frappe.get_all("Claude Account", filters={"claude_team": team} if team else {}, fields=["name", "claude_team", "seat_type"])
	}
	tasks = [
		(get_datetime(t.creation), get_datetime(t.claimed_at) if t.claimed_at else None)
		for t in frappe.get_all("Claude Task", fields=["creation", "claimed_at"])
	]

	if filters.get("view") == "Pool":
		monday = week_start(now)
		rows = pool_rows(monday, tasks, get_account_weeks(add_days(monday, -7 * WEEKS), monday, accounts))
		return pool_columns(), rows, pool_message(rows)
	rows = employee_rows(tasks, get_account_weeks(add_days(now, -7 * WEEKS), now, accounts))
	return employee_columns(), rows, employee_message()


def get_account_weeks(since, until, accounts):
	"""Completed Claude weeks (one per account and reset) with the expired share of the budget."""
	if not accounts:
		return []
	return [
		account_week(accounts[w.parent], w.week_reset, w.week_peak)
		for w in frappe.get_all(
			"Claude Usage Week",
			filters={"parenttype": "Claude Account", "parent": ["in", list(accounts)], "week_reset": ["between", [since, until]]},
			fields=["parent", "week_reset", "week_peak"],
		)
	]


def account_week(account, week_reset, week_peak):
	wasted = round(max(0, 100 - (week_peak or 0)), 1)
	weight = PREMIUM_WEIGHT if account.seat_type == "Premium" else 1
	return frappe._dict(
		account=account.name, team=account.claude_team, seat=account.seat_type, reset=get_datetime(week_reset),
		wasted=wasted, budgets=round(wasted * weight / 100.0, 2),
	)


def week_start(moment):
	"""Monday 00:00 of the calendar week of the given moment."""
	moment = get_datetime(moment)
	return get_datetime(add_days(moment.date(), -moment.weekday()))


def calendar_week(moment):
	return _("CW{0}").format(f"{moment.isocalendar()[1]:02d}")


def waiting_at(moment, tasks):
	"""Number of tasks that were waiting unclaimed in the pool at the given moment."""
	return sum(1 for created, claimed in tasks if created < moment and (not claimed or claimed >= moment))


def waiting_between(start, end, tasks):
	"""True if any task was waiting unclaimed in the pool at some time in [start, end)."""
	return any(created < end and (not claimed or claimed >= start) for created, claimed in tasks)


def employee_rows(tasks, account_weeks):
	"""One row per account week with expired budget, judged at that account's own reset."""
	rows = []
	for w in account_weeks:
		if w.wasted <= 0:
			continue
		waiting = waiting_at(w.reset, tasks)
		rows.append({
			"period": calendar_week(w.reset),
			"reset": w.reset,
			"account": w.account,
			"team": w.team,
			"seat": _(w.seat or ""),
			"wasted": w.wasted,
			"budgets": w.budgets,
			"open": waiting,
			"pool": _("Tasks open") if waiting else _("No tasks in the pool"),
		})
	rows.sort(key=lambda r: (r["reset"], r["wasted"]), reverse=True)
	return rows


def pool_rows(monday, tasks, account_weeks, weeks=WEEKS):
	"""Completed calendar weeks before `monday` in which no task was waiting at any time."""
	rows = []
	for i in range(1, weeks + 1):
		ws, we = add_days(monday, -7 * i), add_days(monday, -7 * (i - 1))
		if waiting_between(ws, we, tasks):
			continue
		resets = [w for w in account_weeks if ws <= w.reset < we]
		rows.append({
			"period": calendar_week(ws),
			"from_date": ws.date(),
			"to_date": add_days(we, -1).date(),
			"accounts": len(resets),
			"wasted": round(sum(w.wasted for w in resets) / len(resets), 1) if resets else 0,
			"budgets": round(sum(w.budgets for w in resets), 2),
		})
	return rows


def employee_columns():
	return [
		{"fieldname": "period", "label": _("Week"), "fieldtype": "Data", "width": 80},
		{"fieldname": "reset", "label": _("Reset"), "fieldtype": "Datetime", "width": 150},
		{"fieldname": "account", "label": _("Claude Account"), "fieldtype": "Link", "options": "Claude Account", "width": 250},
		{"fieldname": "team", "label": _("Claude Team"), "fieldtype": "Data", "width": 130},
		{"fieldname": "seat", "label": _("Seat"), "fieldtype": "Data", "width": 90},
		{"fieldname": "wasted", "label": _("Expired %"), "fieldtype": "Percent", "width": 110},
		{"fieldname": "budgets", "label": _("= Standard Weekly Budgets"), "fieldtype": "Float", "width": 180},
		{"fieldname": "open", "label": _("Open Tasks at Reset"), "fieldtype": "Int", "width": 170},
		{"fieldname": "pool", "label": _("Pool at Reset"), "fieldtype": "Data", "width": 190},
	]


def pool_columns():
	return [
		{"fieldname": "period", "label": _("Week"), "fieldtype": "Data", "width": 80},
		{"fieldname": "from_date", "label": _("From"), "fieldtype": "Date", "width": 110},
		{"fieldname": "to_date", "label": _("To"), "fieldtype": "Date", "width": 110},
		{"fieldname": "accounts", "label": _("Accounts with Reset"), "fieldtype": "Int", "width": 160},
		{"fieldname": "wasted", "label": _("Ø Expired %"), "fieldtype": "Percent", "width": 120},
		{"fieldname": "budgets", "label": _("= Standard Weekly Budgets"), "fieldtype": "Float", "width": 180},
	]


def employee_message():
	return _(
		"Every Claude week of the last {0} weeks in which an account let budget expire, evaluated at that account's own reset. "
		"Red: tasks were waiting in the pool when the budget expired – this budget could have been used. "
		"Green: the pool was empty at that moment. "
		"“= Standard weekly budgets” converts into full budgets of a standard seat: 100 % of a standard seat = 1, 100 % of a premium seat = 5."
	).format(WEEKS)


def pool_message(rows):
	return _(
		"Calendar weeks (Monday to Sunday) of the last {0} completed weeks in which no task was waiting in the pool at any time: {1} weeks, "
		"{2} standard weekly budgets expired in them. These weeks lacked work for the team – this is the potential a well-filled pool could have used. "
		"Each account counts in the week of its own reset."
	).format(WEEKS, len(rows), round(sum(r["budgets"] for r in rows), 2))
