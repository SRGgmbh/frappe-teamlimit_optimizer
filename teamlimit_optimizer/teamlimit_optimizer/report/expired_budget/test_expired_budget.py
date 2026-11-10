# Copyright (c) 2026, SRG - Systemhaus GmbH and contributors
# For license information, please see LICENSE

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase
from frappe.utils import add_days, add_to_date, get_datetime, now_datetime

from teamlimit_optimizer.teamlimit_optimizer.report.expired_budget.expired_budget import (
	WEEKS,
	account_week,
	employee_rows,
	execute,
	pool_rows,
	waiting_at,
	waiting_between,
	week_start,
)

TEAM = "_Test Teamlimit Team"
STD = "tlo-standard@example.com"
PREM = "tlo-premium@example.com"


def dt(value):
	return get_datetime(value)


def acc(name, seat="Standard", team=TEAM):
	return frappe._dict(name=name, seat_type=seat, claude_team=team)


class UnitTestExpiredBudget(UnitTestCase):
	"""Pure calculation helpers, no database."""

	def test_waiting_at(self):
		tasks = [(dt("2026-11-02 08:00"), dt("2026-11-04 10:00")), (dt("2026-11-03 08:00"), None)]
		self.assertEqual(waiting_at(dt("2026-11-02 07:00"), tasks), 0)  # nothing created yet
		self.assertEqual(waiting_at(dt("2026-11-03 09:00"), tasks), 2)
		self.assertEqual(waiting_at(dt("2026-11-04 10:00"), tasks), 2)  # claimed exactly at the moment still counts
		self.assertEqual(waiting_at(dt("2026-11-05 09:00"), tasks), 1)

	def test_waiting_between(self):
		tasks = [(dt("2026-11-03 08:00"), dt("2026-11-03 09:00"))]
		self.assertTrue(waiting_between(dt("2026-11-02"), dt("2026-11-09"), tasks))
		self.assertFalse(waiting_between(dt("2026-11-09"), dt("2026-11-16"), tasks))  # claimed before the week
		self.assertFalse(waiting_between(dt("2026-10-26"), dt("2026-11-02"), tasks))  # created after the week

	def test_week_start(self):
		self.assertEqual(week_start(dt("2026-11-12 15:30")), dt("2026-11-09 00:00"))
		self.assertEqual(week_start(dt("2026-11-09 00:00")), dt("2026-11-09 00:00"))

	def test_account_week_weights_premium(self):
		self.assertEqual(account_week(acc(STD), "2026-11-04 10:00", 70).budgets, 0.3)
		self.assertEqual(account_week(acc(PREM, "Premium"), "2026-11-04 10:00", 90).budgets, 0.5)
		self.assertEqual(account_week(acc(STD), "2026-11-04 10:00", 120).wasted, 0)

	def test_employee_rows_red_and_green(self):
		weeks = [
			account_week(acc(STD), "2026-11-04 10:00", 70),  # pool empty at its reset -> green
			account_week(acc(PREM, "Premium"), "2026-11-11 10:00", 40),  # task waiting at its reset -> red
			account_week(acc(STD), "2026-11-12 10:00", 100),  # nothing expired -> no row
		]
		tasks = [(dt("2026-11-10 08:00"), None)]
		rows = employee_rows(tasks, weeks)
		self.assertEqual([r["account"] for r in rows], [PREM, STD])  # newest reset first
		self.assertEqual(rows[0]["open"], 1)
		self.assertEqual(rows[0]["budgets"], 3.0)
		self.assertEqual(rows[1]["open"], 0)

	def test_pool_rows_only_weeks_without_tasks(self):
		monday = dt("2026-11-16 00:00")
		weeks = [
			account_week(acc(STD), "2026-11-04 10:00", 70),  # CW45
			account_week(acc(PREM, "Premium"), "2026-11-06 23:00", 90),  # CW45
			account_week(acc(STD), "2026-11-11 10:00", 50),  # CW46, task waiting that week
		]
		tasks = [(dt("2026-11-10 08:00"), dt("2026-11-13 08:00"))]
		rows = pool_rows(monday, tasks, weeks, weeks=3)
		self.assertEqual([str(r["from_date"]) for r in rows], ["2026-11-02", "2026-10-26"])
		cw45 = rows[0]
		self.assertEqual(str(cw45["to_date"]), "2026-11-08")
		self.assertEqual(cw45["accounts"], 2)
		self.assertEqual(cw45["wasted"], 20.0)
		self.assertEqual(cw45["budgets"], 0.8)
		self.assertEqual(rows[1]["accounts"], 0)


class IntegrationTestExpiredBudget(IntegrationTestCase):
	"""Runs the report against the database: two accounts, one task, two past calendar weeks."""

	def setUp(self):
		frappe.set_user("Administrator")
		frappe.db.delete("Claude Task")
		for name in (STD, PREM):
			if frappe.db.exists("Claude Account", name):
				frappe.delete_doc("Claude Account", name, force=True)
		if not frappe.db.exists("Claude Team", TEAM):
			frappe.get_doc({"doctype": "Claude Team", "team_name": TEAM}).insert()

		monday = week_start(now_datetime())
		self.week_a = add_days(monday, -14)  # no task in the pool
		self.week_b = add_days(monday, -7)  # one task waiting from Monday to Friday

		self.make_account(STD, "Standard", [(add_to_date(self.week_a, days=2, hours=10), 70), (add_to_date(self.week_b, days=3, hours=10), 100)])
		self.make_account(PREM, "Premium", [(add_to_date(self.week_a, days=4, hours=9), 90), (add_to_date(self.week_b, days=1, hours=10), 40)])

		task = frappe.get_doc({"doctype": "Claude Task", "title": "Test task", "prompt": "Do something", "status": "In Progress"})
		task.claimed_at = add_to_date(self.week_b, days=4)
		task.insert()
		frappe.db.set_value("Claude Task", task.name, "creation", add_to_date(self.week_b, hours=1), update_modified=False)

	def make_account(self, email, seat, weeks):
		doc = frappe.get_doc({"doctype": "Claude Account", "email": email, "seat_type": seat, "claude_team": TEAM})
		for reset, peak in weeks:
			doc.append("weeks", {"week_reset": reset, "week_peak": peak})
		doc.insert()

	def test_by_employee(self):
		columns, rows, message = execute({"view": "Employee", "claude_team": TEAM})
		self.assertIn("pool", [c["fieldname"] for c in columns])
		self.assertEqual([(r["account"], r["open"]) for r in rows], [(PREM, 1), (PREM, 0), (STD, 0)])
		self.assertEqual(rows[0]["budgets"], 3.0)
		self.assertTrue(message)

	def test_by_pool(self):
		columns, rows, message = execute({"view": "Pool", "claude_team": TEAM})
		self.assertEqual(len(rows), WEEKS - 1)  # every past week except week B
		self.assertNotIn(self.week_b.date(), [r["from_date"] for r in rows])
		week_a = next(r for r in rows if r["from_date"] == self.week_a.date())
		self.assertEqual((week_a["accounts"], week_a["wasted"], week_a["budgets"]), (2, 20.0, 0.8))
		self.assertIn("0.8", message)

	def test_team_role_without_account_sees_nothing(self):
		user = "tlo-team-member@example.com"
		if not frappe.db.exists("User", user):
			frappe.get_doc(
				{"doctype": "User", "email": user, "first_name": "Team Member", "send_welcome_email": 0, "roles": [{"role": "Claude Usage Team"}]}
			).insert(ignore_permissions=True)
		frappe.set_user(user)
		try:
			columns, rows, message = execute({"view": "Employee"})
		finally:
			frappe.set_user("Administrator")
		self.assertEqual(rows, [])
		self.assertTrue(message)
