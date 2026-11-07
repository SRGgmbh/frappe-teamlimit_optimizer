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

frappe.listview_settings["Claude Task"] = {
	add_fields: ["status", "priority", "effort"],
	get_indicator(doc) {
		const c = { Open: "blue", "In Progress": "orange", Question: "red", Done: "green" }[doc.status] || "gray";
		return [__(doc.status), c, "status,=," + doc.status];
	},
	onload(listview) {
		listview.page.add_inner_button(__("Create from AI text"), () =>
			tl_import_dialog((v) => {
				const vals = {};
				for (const [k, val] of Object.entries(v)) if (!k.startsWith("_")) vals[k] = val;
				frappe.new_doc("Claude Task", vals);
			})
		);
	},
};
