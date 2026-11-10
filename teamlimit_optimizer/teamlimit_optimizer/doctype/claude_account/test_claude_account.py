# Copyright (c) 2026, SRG - Systemhaus GmbH and contributors
# For license information, please see LICENSE

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase
from frappe.utils import add_to_date, get_datetime, now_datetime

from teamlimit_optimizer import api

EMAIL = "tlo-report@example.com"


class UnitTestClaudeAccount(UnitTestCase):
	def test_bucket_boundaries(self):
		self.assertEqual([api._bucket(p) for p in (0, 49.9, 50, 74.9, 75, 89.9, 90, 99.9, 100, 130)], [0, 0, 50, 50, 75, 75, 90, 90, 100, 100])

	def test_same_time_tolerance(self):
		base = get_datetime("2026-11-10 12:00:00")
		self.assertTrue(api._same_time(base, add_to_date(base, minutes=30)))
		self.assertFalse(api._same_time(base, add_to_date(base, minutes=31)))
		self.assertFalse(api._same_time(None, base))


class IntegrationTestClaudeAccount(IntegrationTestCase):
	"""The ingest endpoint `teamlimit_optimizer.api.report`."""

	def setUp(self):
		frappe.set_user("Administrator")
		if frappe.db.exists("Claude Account", EMAIL):
			frappe.delete_doc("Claude Account", EMAIL, force=True)
		self.week_reset = add_to_date(now_datetime(), days=3).replace(microsecond=0)
		self.five_reset = add_to_date(now_datetime(), hours=2).replace(microsecond=0)

	def send(self, five, week, five_reset=None, week_reset=None, tier="default_raven", jitter=0):
		return api.report(
			email=EMAIL.upper(),
			rate_limit_tier=tier,
			five_pct=five,
			week_pct=week,
			five_reset=str(add_to_date(five_reset or self.five_reset, minutes=jitter)),
			week_reset=str(add_to_date(week_reset or self.week_reset, minutes=jitter)),
		)

	def week_row(self):
		doc = frappe.get_doc("Claude Account", EMAIL)
		self.assertEqual(len(doc.weeks), 1)
		return doc, doc.weeks[0]

	def test_creates_account_with_seat_type(self):
		self.assertEqual(self.send(10, 5)["account"], EMAIL)  # e-mail is normalised to lower case
		self.assertEqual(frappe.db.get_value("Claude Account", EMAIL, "seat_type"), "Standard")
		self.send(10, 5, tier="default_claude_max_5x")
		self.assertEqual(frappe.db.get_value("Claude Account", EMAIL, "seat_type"), "Premium")

	def test_window_counts_once_in_highest_bucket(self):
		self.send(55, 10)
		self.send(80, 12, jitter=10)  # second device, same window, slightly different reset time
		self.send(60, 12)  # lower value later must not move the window back
		doc, row = self.week_row()
		self.assertEqual((row.windows, row.b50, row.b75, row.b90, row.b100), (1, 0, 1, 0, 0))
		self.assertEqual(doc.cur_window_bucket, 75)

	def test_new_window_is_counted_separately(self):
		self.send(95, 10)
		self.send(20, 15, five_reset=add_to_date(self.five_reset, hours=5))
		_doc, row = self.week_row()
		self.assertEqual((row.windows, row.b90), (2, 1))

	def test_week_peak_only_rises_and_new_week_adds_row(self):
		self.send(10, 40)
		self.send(10, 30)
		_doc, row = self.week_row()
		self.assertEqual(row.week_peak, 40)
		self.send(10, 5, week_reset=add_to_date(self.week_reset, days=7), five_reset=add_to_date(self.five_reset, days=7))
		self.assertEqual(len(frappe.get_doc("Claude Account", EMAIL).weeks), 2)

	def test_rejects_users_without_ingest_role(self):
		frappe.set_user("Guest")
		try:
			self.assertRaises(frappe.PermissionError, self.send, 10, 10)
		finally:
			frappe.set_user("Administrator")
