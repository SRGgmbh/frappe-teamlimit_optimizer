// Copyright (c) 2026, SRG - Systemhaus GmbH and contributors
// For license information, please see LICENSE

function tl_copy_buttons($root) {
	$root.find("pre").each(function () {
		const $pre = $(this);
		if ($pre.parent().hasClass("tl-code")) return;
		$pre.wrap('<div class="tl-code" style="position: relative"></div>');
		const $btn = $(
			`<button class="btn btn-xs btn-default" style="position: absolute; top: 6px; right: 6px">${__("Copy")}</button>`
		);
		$btn.on("click", () => {
			frappe.utils.copy_to_clipboard($pre.text());
			$btn.text(__("Copied"));
			setTimeout(() => $btn.text(__("Copy")), 1500);
		});
		$pre.parent().append($btn);
	});
}

frappe.ui.form.on("Teamlimit Guide", {
	refresh(frm) {
		const editing = !!frm.__teamlimit_edit || frm.is_new();
		frm.toggle_display("content", editing);
		frm.toggle_display(["title", "language", "audience", "sort_order"], editing);
		const $w = frm.get_field("content_view").$wrapper;
		$w.html(
			editing
				? ""
				: `<div class="teamlimit-guide" style="max-width: 860px; font-size: 15px; line-height: 1.6">${frappe.markdown(frm.doc.content || "")}</div>`
		);
		if (!editing) tl_copy_buttons($w);
		// guides shipped with the app are re-imported on every update
		if (frappe.user.has_role("System Manager") && (frm.doc.name || "").startsWith("TLG-")) {
			frm.set_intro(
				__("This guide is part of the app and is overwritten on every update. Changes made here will be lost; create a new guide instead."),
				"orange"
			);
		}
		if (frappe.user.has_role("System Manager")) {
			frm.add_custom_button(editing ? __("View") : __("Edit"), () => {
				frm.__teamlimit_edit = !editing;
				frm.refresh();
			});
		}
	},
});
