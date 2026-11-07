import frappe


def after_install():
	settings = frappe.get_single("Teamlimit Settings")
	for field, value in {"warn_pct": 60, "crit_pct": 90, "min_free_pct": 25, "stale_hours": 3}.items():
		if not settings.get(field):
			settings.set(field, value)
	settings.flags.ignore_permissions = True
	settings.save()
