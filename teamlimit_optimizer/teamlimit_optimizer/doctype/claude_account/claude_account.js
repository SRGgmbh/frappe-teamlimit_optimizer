// Copyright (c) 2026, SRG - Systemhaus GmbH and contributors
// For license information, please see license.txt

function teamlimit_color_bars(root) {
	frappe.db.get_value("Teamlimit Settings", "Teamlimit Settings", ["warn_pct", "crit_pct"]).then((r) => {
		const s = (r && r.message) || {};
		const warn = s.warn_pct || 60;
		const crit = s.crit_pct || 90;
		$(root).find(".progress-bar").each(function () {
			const w = parseFloat(this.style.width) || 0;
			this.style.backgroundColor =
				w >= crit ? "var(--red-500)" : w >= warn ? "var(--orange-500)" : "var(--green-500)";
		});
	});
}

frappe.ui.form.on("Claude Account", {
	refresh(frm) {
		teamlimit_color_bars(frm.wrapper);
		setTimeout(() => teamlimit_color_bars(frm.wrapper), 600);
	},
});
