// Copyright (c) 2026, SRG - Systemhaus GmbH and contributors
// For license information, please see license.txt

frappe.ui.form.on("Teamlimit Settings", {
	refresh(frm) {
		frm.get_field("ingest_help").$wrapper.html(
			`<p class="text-muted">${__(
				"The reporting scripts send the usage of each Claude account to this site. They sign in as a separate ingest user that may only report and cannot read anything. Set it up once, then download the scripts – the address of this site and the key are already filled in. Keep the scripts internal."
			)}</p>`
		);
		frm.add_custom_button(
			frm.doc.ingest_api_key ? __("Renew ingest key") : __("Set up ingest user"),
			() =>
				frappe.confirm(
					frm.doc.ingest_api_key
						? __("A new key invalidates all scripts already distributed. Continue?")
						: __("Create the ingest user now?"),
					() =>
						frappe.call("teamlimit_optimizer.api.setup_ingest_user").then(() => {
							frm.reload_doc();
							frappe.show_alert({ message: __("Ingest user is ready."), indicator: "green" });
						})
				),
			__("Reporting scripts")
		);
		const dl = (kind) => window.open(`/api/method/teamlimit_optimizer.api.download_script?kind=${kind}`);
		frm.add_custom_button(__("Download Windows script"), () => dl("windows"), __("Reporting scripts"));
		frm.add_custom_button(__("Download Linux script"), () => dl("linux"), __("Reporting scripts"));
		frm.add_custom_button(__("Download scheduled task (XML)"), () => dl("task"), __("Reporting scripts"));
	},
});
