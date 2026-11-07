frappe.listview_settings["Claude Account"] = {
	refresh(listview) {
		setTimeout(() => {
			frappe.db.get_value("Teamlimit Settings", "Teamlimit Settings", ["warn_pct", "crit_pct"]).then((r) => {
				const s = (r && r.message) || {};
				const warn = s.warn_pct || 60;
				const crit = s.crit_pct || 90;
				listview.$result.find(".progress-bar").each(function () {
					const w = parseFloat(this.style.width) || 0;
					this.style.backgroundColor =
						w >= crit ? "var(--red-500)" : w >= warn ? "var(--orange-500)" : "var(--green-500)";
				});
			});
		}, 400);
	},
};
