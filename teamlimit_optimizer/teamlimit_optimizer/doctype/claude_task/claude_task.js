// Copyright (c) 2026, SRG - Systemhaus GmbH and contributors
// For license information, please see LICENSE

// Hand-over block from Claude or other AI assistants:
// === TEAMLIMIT-TASK === … --- PROMPT --- … === END ===  (English or German keys and markers)
const TL_EFFORT = {
	S: "S – up to 25 % of a 5-h window",
	M: "M – up to 50 % of a 5-h window",
	L: "L – a full 5-h window",
};
const TL_PRIORITY = { hoch: "High", high: "High", mittel: "Medium", medium: "Medium", niedrig: "Low", low: "Low" };
async function tl_parse_block(text) {
	const t = (text || "").replace(/\r/g, "");
	if (!t.includes("--- PROMPT ---")) {
		frappe.throw(__("No hand-over block found. It must contain “--- PROMPT ---”."));
	}
	const head = t.split("--- PROMPT ---")[0];
	const prompt = (t.split("--- PROMPT ---")[1].split(/=== (ENDE|END) ===/)[0] || "").trim();
	const get = (...keys) => {
		for (const k of keys) {
			const m = head.match(new RegExp("^[ \t]*" + k + "[ \t]*:[ \t]*(.*)$", "mi"));
			if (m && m[1].trim()) return m[1].trim();
		}
		return "";
	};
	const v = { prompt };
	const title = get("Titel", "Title");
	if (title) v.title = title;
	const pr = TL_PRIORITY[get("Priorität", "Priority").toLowerCase()];
	if (pr) v.priority = pr;
	const ef = TL_EFFORT[(get("Aufwand", "Effort")[0] || "").toUpperCase()];
	if (ef) v.effort = ef;
	const due = get("Fällig bis", "Due date", "Due").match(/(\d{1,2})\.(\d{1,2})\.(\d{4})|(\d{4})-(\d{2})-(\d{2})/);
	if (due) v.due_date = due[1] ? `${due[3]}-${due[2].padStart(2, "0")}-${due[1].padStart(2, "0")}` : `${due[4]}-${due[5]}-${due[6]}`;
	const mo = ["Chat", "Cowork", "Claude Code"].find((x) => x.toLowerCase() === get("Starten in", "Start in").toLowerCase());
	if (mo) v.mode = mo;
	const pre = get("Voraussetzungen", "Prerequisites");
	if (pre) v.prerequisites = pre;
	const proj = get("Claude-Projekt", "Claude Project");
	const link = get("Projekt-Link", "Project Link");
	v._unmatched = "";
	if (proj && (await frappe.db.exists("Claude Project", proj))) {
		v.claude_project = proj;
	} else if (link.startsWith("http")) {
		const id = (link.match(/project\/([0-9a-f-]{36})/i) || [, link])[1];
		const hit = await frappe.db.get_list("Claude Project", { filters: { url: ["like", "%" + id + "%"] }, limit: 1 });
		if (hit.length) v.claude_project = hit[0].name;
		else v._unmatched = proj || link;
	} else if (proj) {
		v._unmatched = proj;
	}
	const team = get("Claude Team");
	if (team && (await frappe.db.exists("Claude Team", team))) v.claude_team = team;
	return v;
}
function tl_import_dialog(on_values) {
	const d = new frappe.ui.Dialog({
		title: __("Import from AI text"),
		fields: [
			{
				fieldname: "text",
				fieldtype: "Long Text",
				label: __("Paste the block from “=== TEAMLIMIT-TASK ===” to “=== END ===”"),
				reqd: 1,
			},
		],
		primary_action_label: __("Import"),
		async primary_action(r) {
			const v = await tl_parse_block(r.text);
			d.hide();
			on_values(v);
			if (v._unmatched) {
				frappe.msgprint(
					__("The project “{0}” is not in the project list yet. Please add it under Administration > Claude Projects and select it.", [v._unmatched])
				);
			} else {
				frappe.show_alert({ message: __("Fields imported – please check and save."), indicator: "green" });
			}
		},
	});
	d.show();
}

const TL_MODE = { Chat: "claude://claude.ai/new", Cowork: "claude://cowork/new", "Claude Code": "claude://code/new" };

function tl_act(frm, action, extra) {
	return frappe
		.call({ method: "teamlimit_optimizer.api.task", args: Object.assign({ task: frm.doc.name, action }, extra || {}) })
		.then(() => frm.reload_doc());
}

function tl_prompt(frm) {
	const url = `${window.location.origin}${frappe.utils.get_form_link("Claude Task", frm.doc.name)}`;
	return (
		`[${__("Teamlimit task")} ${frm.doc.name}: ${frm.doc.title}]\n` +
		`${__("Task in the pool")}: ${url}\n\n` +
		`${frm.doc.prompt || ""}\n\n` +
		__("When the task is done, use the skill “pool-task-complete”.")
	);
}

// Taking the prompt means taking the task.
function tl_take(frm) {
	if (frm.doc.status === "Open") return tl_act(frm, "claim").then(() => true);
	if (frm.doc.status === "In Progress" && frm.doc.claimed_by !== frappe.session.user) {
		frappe.msgprint(__("{0} is already working on this task.", [frm.doc.claimed_by]));
		return Promise.resolve(false);
	}
	return Promise.resolve(true);
}

frappe.ui.form.on("Claude Task", {
	refresh(frm) {
		if (frm.is_new() || frm.doc.status === "Open") {
			frm.add_custom_button(__("Import from AI text"), () =>
				tl_import_dialog((v) => {
					for (const [k, val] of Object.entries(v)) if (!k.startsWith("_")) frm.set_value(k, val);
				})
			);
		}
		if (frm.is_new()) return;

		const can_run = frm.doc.status !== "Done";
		const pid = ((frm.doc.project_url || "").match(/project\/([0-9a-f-]{36})/i) || [])[1];
		const mode = frm.doc.mode || "Chat";
		if (can_run) {
			frm.add_custom_button(__("Start in Claude"), () => {
				const text = tl_prompt(frm);
				const in_project = mode === "Chat" && pid;
				// copy before waiting, while the click still counts as a user gesture
				if (in_project) frappe.utils.copy_to_clipboard(text);
				tl_take(frm).then((ok) => {
					if (!ok) return;
					if (in_project) {
						// Claude Desktop cannot prefill a prompt inside a project, so it goes via the clipboard
						window.location.href = `claude://claude.ai/project/${pid}`;
						frappe.msgprint({
							title: __("Opening the project"),
							indicator: "blue",
							message: __("The prompt is in the clipboard. Paste it in the Claude project with Ctrl+V and send it."),
						});
					} else {
						window.location.href = `${TL_MODE[mode]}?q=${encodeURIComponent(text)}`;
					}
				});
			}).addClass("btn-primary");
			frm.add_custom_button(
				__("Copy prompt"),
				() => {
					frappe.utils.copy_to_clipboard(tl_prompt(frm));
					tl_take(frm);
				},
				__("Claude")
			);
		}
		if (frm.doc.project_url) {
			frm.add_custom_button(__("Open project"), () => window.open(frm.doc.project_url, "_blank"), __("Claude"));
		}

		const st = frm.doc.status;
		if (st === "Open") {
			frm.add_custom_button(__("Only take"), () => tl_act(frm, "claim"));
		}
		if (st === "In Progress" || st === "Question") {
			frm.add_custom_button(__("Done"), async () => {
				const acc = await frappe.xcall("teamlimit_optimizer.api.my_claude_account");
				frappe.prompt(
					[
						{
							fieldname: "claude_email",
							label: __("Your Claude account (e-mail)"),
							fieldtype: "Data",
							options: "Email",
							reqd: 1,
							default: acc || "",
						},
						{
							fieldname: "result_url",
							label: __("Result link (shared chat, artifact or file)"),
							fieldtype: "Data",
							reqd: 1,
						},
						{
							fieldname: "summary",
							label: __("Result summary (from the skill “pool-task-complete”)"),
							fieldtype: "Small Text",
						},
					],
					(v) => tl_act(frm, "done", v),
					__("Complete task")
				);
			}).addClass("btn-primary");
			frm.add_custom_button(__("Question"), () => {
				frappe.prompt(
					{ fieldname: "text", label: __("What is unclear?"), fieldtype: "Small Text", reqd: 1 },
					(v) => tl_act(frm, "question", { text: v.text }),
					__("Question to the requester")
				);
			});
			frm.add_custom_button(__("Release"), () => tl_act(frm, "release"));
		}
	},
});
