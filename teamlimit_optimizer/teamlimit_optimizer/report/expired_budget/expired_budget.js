// Copyright (c) 2026, SRG - Systemhaus GmbH and contributors
// For license information, please see LICENSE

frappe.query_reports["Expired Budget"] = {
	get_datatable_options(options) {
		return Object.assign(options, { layout: "fluid" });
	},
	filters: [
		{ fieldname: "cause", label: __("Cause"), fieldtype: "Select", options: "All\nTasks open\nNo tasks in the pool", default: "All" },
	],
	formatter(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (!data) return value;
		if (data.is_total && ["account", "wasted", "budgets"].includes(column.fieldname)) value = `<b>${value}</b>`;
		if (column.fieldname === "cause") {
			return `<span class="indicator-pill ${data.is_total ? "gray" : "orange"}">${value}</span>`;
		}
		return value;
	},
};
