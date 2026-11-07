app_name = "teamlimit_optimizer"
app_title = "Teamlimit Optimizer"
app_publisher = "SRG - Systemhaus GmbH"
app_description = "Makes full use of Claude Team plan limits – for Claude by Anthropic"
app_email = "consulting@srg.gmbh"
app_license = "mit"
required_apps = ["frappe"]

app_logo_url = "/assets/teamlimit_optimizer/images/logo.svg"

add_to_apps_screen = [
	{
		"name": "teamlimit_optimizer",
		"logo": "/assets/teamlimit_optimizer/images/logo.svg",
		"title": "Teamlimit Optimizer",
		"route": "/app/teamlimit-optimizer",
	}
]

after_install = "teamlimit_optimizer.install.after_install"

fixtures = [
	{"dt": "Role", "filters": [["name", "like", "Claude Usage %"]]},
	{"dt": "Number Card", "filters": [["module", "=", "Teamlimit Optimizer"]]},
	{"dt": "Dashboard Chart", "filters": [["module", "=", "Teamlimit Optimizer"]]},
	{"dt": "Notification", "filters": [["module", "=", "Teamlimit Optimizer"]]},
	{"dt": "Teamlimit Guide"},
]
