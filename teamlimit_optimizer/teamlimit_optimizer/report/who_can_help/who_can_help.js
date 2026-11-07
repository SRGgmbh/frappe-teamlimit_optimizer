// Copyright (c) 2026, SRG - Systemhaus GmbH and contributors
// For license information, please see license.txt

frappe.query_reports["Who Can Help"] = {
	get_datatable_options(options) {
		return Object.assign(options, { layout: "fluid" });
	},
	formatter(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (!data) return value;
		if (data._section) {
			return column.fieldname === "member" ? `<b class="text-muted">${__("No current information")}</b>` : "";
		}
		if (data._stale) {
			if (column.fieldname === "stage") return `<span class="indicator-pill gray">${value}</span>`;
			return `<span class="text-muted">${value}</span>`;
		}
		if (data._warn === undefined) return value;
		const used = { five: 1, week: 1 }[column.fieldname];
		const free = column.fieldname === "free";
		if (!used && !free) return value;
		let v = data[column.fieldname] || 0;
		if (free) v = 100 - v;
		const color = v >= data._crit ? "red" : v >= data._warn ? "orange" : "green";
		return `<span class="indicator-pill ${color}">${value}</span>`;
	},
};
