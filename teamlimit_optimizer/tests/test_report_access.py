# Copyright (c) 2026, SRG - Systemhaus GmbH and contributors
# For license information, please see LICENSE

import frappe
from frappe.desk.query_report import run
from frappe.tests import IntegrationTestCase

TEAM = "_Test Access Team"
CLAUDE_ROLES = ("Claude Usage Manager", "Claude Usage User", "Claude Usage Team")


def make_user(role):
	email = "tlo-" + role.lower().replace(" ", "-") + "@example.com"
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{"doctype": "User", "email": email, "first_name": role, "send_welcome_email": 0, "roles": [{"role": role}]}
		).insert(ignore_permissions=True)
	# team members only see their own team, so they need a linked Claude account
	if not frappe.db.exists("Claude Account", {"frappe_user": email}):
		frappe.get_doc({"doctype": "Claude Account", "email": email, "frappe_user": email, "claude_team": TEAM}).insert(ignore_permissions=True)
	return email


class IntegrationTestReportAccess(IntegrationTestCase):
	"""Every report must open for every Claude role it is shared with, through the regular desk endpoint."""

	def setUp(self):
		frappe.set_user("Administrator")
		if not frappe.db.exists("Claude Team", TEAM):
			frappe.get_doc({"doctype": "Claude Team", "team_name": TEAM}).insert()

	def tearDown(self):
		frappe.set_user("Administrator")

	def test_reports_open_for_their_roles(self):
		reports = frappe.get_all("Report", filters={"module": "Teamlimit Optimizer"}, pluck="name")
		self.assertTrue(reports)
		for role in CLAUDE_ROLES:
			user = make_user(role)
			for report in reports:
				if role not in [r.role for r in frappe.get_doc("Report", report).roles]:
					continue
				with self.subTest(role=role, report=report):
					frappe.set_user(user)
					try:
						result = run(report, filters={})
					finally:
						frappe.set_user("Administrator")
					self.assertIn("result", result)

	def test_reports_closed_for_other_users(self):
		email = "tlo-no-role@example.com"
		if not frappe.db.exists("User", email):
			frappe.get_doc({"doctype": "User", "email": email, "first_name": "No Role", "send_welcome_email": 0}).insert(ignore_permissions=True)
		frappe.set_user(email)
		self.assertRaises(frappe.PermissionError, run, "Expired Budget", filters={})
