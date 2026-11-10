// Copyright (c) 2026, SRG - Systemhaus GmbH and contributors
// For license information, please see LICENSE

const EXPIRED_BUDGET_TABS = [
	{ value: "Employee", label: __("By Employee") },
	{ value: "Pool", label: __("By Pool") },
];

frappe.query_reports["Expired Budget"] = {
	get_datatable_options(options) {
		return Object.assign(options, { layout: "fluid" });
	},
	filters: [
		{ fieldname: "view", label: __("View"), fieldtype: "Select", options: EXPIRED_BUDGET_TABS, default: "Employee", hidden: 1 },
		{ fieldname: "claude_team", label: __("Claude Team"), fieldtype: "Link", options: "Claude Team" },
	],
	onload(report) {
		// tabs above the filters switch the hidden "view" filter
		const $tabs = $(`<ul class="nav nav-tabs teamlimit-tabs" style="margin: 0 var(--padding-md) var(--padding-sm);"></ul>`);
		EXPIRED_BUDGET_TABS.forEach((tab) => {
			$(`<li class="nav-item"><a class="nav-link" href="#" data-view="${tab.value}">${tab.label}</a></li>`).appendTo($tabs);
		});
		const mark = () => {
			const view = report.get_filter_value("view") || "Employee";
			$tabs.find(".nav-link").each((_, a) => $(a).toggleClass("active", a.dataset.view === view));
		};
		$tabs.on("click", ".nav-link", (e) => {
			e.preventDefault();
			report.set_filter_value("view", e.currentTarget.dataset.view);
			mark();
		});
		report.page.wrapper.find(".teamlimit-tabs").remove();
		$tabs.insertBefore(report.page.page_form);
		mark();
	},
	formatter(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (!data || data.pool === undefined) return value;
		// By employee: red = tasks were waiting at the reset (usable budget expired), green = pool was empty
		const color = data.open ? "red" : "green";
		if (column.fieldname === "pool") return `<span class="indicator-pill ${color}">${value}</span>`;
		if (column.fieldname === "wasted") return `<span style="color: var(--${color}-600); font-weight: 600;">${value}</span>`;
		return value;
	},
};
