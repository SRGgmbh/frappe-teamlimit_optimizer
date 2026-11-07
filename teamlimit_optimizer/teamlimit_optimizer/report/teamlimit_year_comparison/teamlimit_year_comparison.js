// Copyright (c) 2026, SRG - Systemhaus GmbH and contributors
// For license information, please see license.txt

frappe.query_reports["Teamlimit Year Comparison"] = {
	get_datatable_options(options) {
		return Object.assign(options, { layout: "fluid" });
	},
};
