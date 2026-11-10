# Copyright (c) 2026, SRG - Systemhaus GmbH and contributors
# For license information, please see LICENSE

import frappe
from frappe.tests import IntegrationTestCase

from teamlimit_optimizer import api

HELPER = "tlo-helper@example.com"
OTHER = "tlo-other@example.com"


def make_user(email):
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{"doctype": "User", "email": email, "first_name": email.split("@")[0], "send_welcome_email": 0, "roles": [{"role": "Claude Usage User"}]}
		).insert(ignore_permissions=True)


class IntegrationTestClaudeTask(IntegrationTestCase):
	"""Task pool actions via `teamlimit_optimizer.api.task`."""

	def setUp(self):
		frappe.set_user("Administrator")
		make_user(HELPER)
		make_user(OTHER)
		self.task = frappe.get_doc({"doctype": "Claude Task", "title": "Summarise a document", "prompt": "Please summarise ..."}).insert().name

	def tearDown(self):
		frappe.set_user("Administrator")

	def act(self, user, action, **kwargs):
		frappe.set_user(user)
		return api.task(self.task, action, **kwargs)

	def test_claim_locks_task_for_others(self):
		self.assertEqual(self.act(HELPER, "claim"), {"status": "In Progress", "claimed_by": HELPER})
		self.assertEqual(self.act(HELPER, "claim")["status"], "In Progress")  # claiming again is harmless
		self.assertRaises(frappe.ValidationError, self.act, OTHER, "claim")

	def test_release_reopens_task(self):
		self.act(HELPER, "claim")
		self.act(HELPER, "release")
		doc = frappe.get_doc("Claude Task", self.task)
		self.assertEqual((doc.status, doc.claimed_by, doc.claimed_at), ("Open", None, None))

	def test_only_claimant_or_manager_can_release(self):
		self.act(HELPER, "claim")
		self.assertRaises(frappe.PermissionError, self.act, OTHER, "release")
		self.assertEqual(self.act("Administrator", "release")["status"], "Open")

	def test_website_user_cannot_act(self):
		email = "tlo-website@example.com"
		if not frappe.db.exists("User", email):
			frappe.get_doc({"doctype": "User", "email": email, "first_name": "Website", "user_type": "Website User", "send_welcome_email": 0}).insert(ignore_permissions=True)
		self.assertRaises(frappe.PermissionError, self.act, email, "claim")
		self.assertRaises(frappe.PermissionError, api.kpi, {"kpi": "open_tasks"})

	def test_my_claude_account(self):
		if not frappe.db.exists("Claude Account", HELPER):
			frappe.get_doc({"doctype": "Claude Account", "email": HELPER, "frappe_user": HELPER}).insert()
		frappe.set_user(HELPER)
		self.assertEqual(api.my_claude_account(), HELPER)
		frappe.set_user(OTHER)
		self.assertIsNone(api.my_claude_account())

	def test_done_requires_result_link(self):
		self.act(HELPER, "claim")
		self.assertRaises(frappe.ValidationError, self.act, HELPER, "done")
		self.act(HELPER, "done", result_url="https://claude.ai/share/x", summary="Done.", claude_email="TLO-Helper@Example.com")
		doc = frappe.get_doc("Claude Task", self.task)
		self.assertEqual(doc.status, "Done")
		self.assertEqual(doc.claude_email, "tlo-helper@example.com")
		self.assertTrue(doc.completed_at)

	def test_question_and_unknown_action(self):
		self.act(HELPER, "question", text="Which file?")
		self.assertEqual(frappe.db.get_value("Claude Task", self.task, ["status", "notes_question"]), ("Question", "Which file?"))
		self.assertRaises(frappe.ValidationError, self.act, HELPER, "explode")
