// Copyright (c) 2026, SRG - Systemhaus GmbH and contributors
// For license information, please see LICENSE

// Script reports have no tab component. The tabs below use the markup and styles of the Frappe form tabs
// (.form-tabs-list / .nav-link) and drive the filter "view", so the regular report refresh does the work.
// They live inside the filter area, which Frappe empties whenever another report is loaded – they cannot leak.
function tl_view_tabs() {
	return [
		{ value: "Employee", label: __("By Employee") },
		{ value: "Pool", label: __("By Pool") },
	];
}

function tl_setup_view_tabs(report) {
	const $area = report.page.page_form;
	$area.find(".tl-view-tabs").remove();
	const $tabs = $(
		`<div class="form-tabs-list tl-view-tabs" style="position: static; flex: 0 0 100%; margin-bottom: var(--margin-md)">
			<ul class="nav form-tabs" role="tablist"></ul>
		</div>`
	).prependTo($area);

	const show = (view) =>
		$tabs.find(".nav-link").each((_i, a) => {
			const active = a.dataset.view === view;
			$(a).toggleClass("active", active).attr("aria-selected", active);
		});

	tl_view_tabs().forEach((tab) => {
		$(`<li class="nav-item"><a class="nav-link" role="tab" href="#" data-view="${tab.value}">${tab.label}</a></li>`).appendTo(
			$tabs.find(".nav")
		);
	});
	$tabs.on("click", ".nav-link", (e) => {
		e.preventDefault();
		const view = e.currentTarget.dataset.view;
		if (view === report.get_filter_value("view")) return;
		show(view); // immediately, the filter value follows asynchronously
		report.set_filter_value("view", view);
	});

	show(report.get_filter_value("view") || "Employee");
	report.tl_show_view_tab = show;
}

frappe.query_reports["Expired Budget"] = {
	get_datatable_options(options) {
		return Object.assign(options, { layout: "fluid" });
	},
	filters: [
		{ fieldname: "view", label: __("View"), fieldtype: "Select", options: tl_view_tabs(), default: "Employee", hidden: 1 },
		{ fieldname: "claude_team", label: __("Claude Team"), fieldtype: "Link", options: "Claude Team" },
	],
	onload(report) {
		tl_setup_view_tabs(report);
	},
	after_datatable_render() {
		// keep the highlighted tab in line with the filter, e.g. after a route change
		const report = frappe.query_report;
		if (report && report.tl_show_view_tab) report.tl_show_view_tab(report.get_filter_value("view") || "Employee");
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
