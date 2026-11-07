#!/usr/bin/env bash
# Teamlimit Optimizer – reporting script for Linux
# Reads the Claude usage of the current user and reports it to Frappe.
# The Claude token never leaves the device; only e-mail, seat tier and percentages are sent.
# Requires: bash, curl, python3. Run manually with visible output:  teamlimit-report.sh --test
set -u
FRAPPE_URL="__FRAPPE_URL__"
INGEST_AUTH="__INGEST_AUTH__"

LOG_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/teamlimit-optimizer"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/report.log"
TEST=0; [ "${1:-}" = "--test" ] && TEST=1
log() { local line; line="$(date '+%Y-%m-%d %H:%M:%S')  $*"; echo "$line" >> "$LOG"; [ $TEST -eq 1 ] && echo "$line"; return 0; }

CRED="$HOME/.claude/.credentials.json"
CFG="$HOME/.claude.json"
[ -f "$CRED" ] || { log "No Claude Code sign-in found, skipped."; exit 0; }

read -r TOKEN EXPIRES SUB TIER < <(python3 - "$CRED" <<'PY'
import json, sys
o = json.load(open(sys.argv[1])).get("claudeAiOauth", {})
print(o.get("accessToken", "-"), o.get("expiresAt", 0), o.get("subscriptionType") or "-", o.get("rateLimitTier") or "-")
PY
)
[ "$TOKEN" = "-" ] && { log "Sign-in file without token, skipped."; exit 0; }
NOW_MS=$(( $(date +%s) * 1000 ))
[ "$EXPIRES" -lt "$NOW_MS" ] && { log "Token expired. Start Claude Code once, then try again."; exit 0; }

EMAIL=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("oauthAccount",{}).get("emailAddress",""))' "$CFG" 2>/dev/null)
[ -n "$EMAIL" ] || { log "E-mail not found in .claude.json (oauthAccount.emailAddress)."; exit 1; }

USAGE=$(curl -fsS --max-time 30 https://api.anthropic.com/api/oauth/usage \
  -H "Authorization: Bearer $TOKEN" -H "anthropic-beta: oauth-2025-04-20" -H "User-Agent: claude-code/2.1.0") \
  || { log "Error: usage request failed."; exit 1; }
[ $TEST -eq 1 ] && log "Usage response: $USAGE"

BODY=$(TL_USAGE="$USAGE" python3 - "$EMAIL" "$SUB" "$TIER" <<'PY'
import json, os, sys
from datetime import datetime
u = json.loads(os.environ["TL_USAGE"])
def local(iso):
    if not iso: return None
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone().strftime("%Y-%m-%d %H:%M:%S")
f, w = u.get("five_hour") or {}, u.get("seven_day") or {}
b = {"email": sys.argv[1], "subscription_type": sys.argv[2], "rate_limit_tier": sys.argv[3],
     "five_pct": f.get("utilization"), "five_reset": local(f.get("resets_at")),
     "week_pct": w.get("utilization"), "week_reset": local(w.get("resets_at"))}
x = u.get("extra_usage") or {}
if x.get("used_credits") is not None: b["extra_used"] = x["used_credits"]
print(json.dumps(b))
PY
)
curl -fsS --max-time 30 -X POST "$FRAPPE_URL/api/method/teamlimit_optimizer.api.report" \
  -H "Authorization: $INGEST_AUTH" -H "Content-Type: application/json" -d "$BODY" > /dev/null \
  && log "Reported: $EMAIL" || { log "Error: report to Frappe failed."; exit 1; }
