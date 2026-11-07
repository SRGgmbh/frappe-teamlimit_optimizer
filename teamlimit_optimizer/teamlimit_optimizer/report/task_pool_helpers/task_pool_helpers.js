// Copyright (c) 2026, SRG - Systemhaus GmbH and contributors
// For license information, please see LICENSE

frappe.query_reports["Task Pool Helpers"] = {
	get_datatable_options(options) {
		return Object.assign(options, { layout: "fluid" });
	},
	filters: [
		{ fieldname: "period", label: __("Period"), fieldtype: "Select", options: "This Week\nLast 4 Weeks\nThis Year", default: "This Week" },
	],
	formatter(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (data && data.rank === 1 && column.fieldname === "account") return `🏆 <b>${value}</b>`;
		return value;
	},
};
