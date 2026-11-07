// Copyright (c) 2026, SRG - Systemhaus GmbH and contributors
// For license information, please see license.txt

frappe.query_reports["Teamlimit Trend"] = {
	get_datatable_options(options) {
		return Object.assign(options, { layout: "fluid" });
	},
	filters: [
		{ fieldname: "granularity", label: __("Period"), fieldtype: "Select", options: "Week\nMonth", default: "Week" },
	],
};
