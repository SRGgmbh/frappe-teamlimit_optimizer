#!/usr/bin/env bash
# Teamlimit Optimizer – one-line installer for Linux (run as the user whose Claude usage is reported, no root needed)
#
#   curl -fsSL https://raw.githubusercontent.com/SRGgmbh/frappe-teamlimit_optimizer/version-16/scripts/install-linux.sh \
#     | bash -s -- --url "https://erp.example.com" --auth "token <api_key>:<api_secret>"
#
# Installs the reporting script to ~/.local/bin, stores address and ingest key in ~/.config/teamlimit-optimizer/config
# and sets up a systemd user timer (or a cron job if systemd is not available). Running it again updates everything.
set -euo pipefail
URL=""; AUTH=""; BRANCH="version-16"; INTERVAL=60; REPO="SRGgmbh/frappe-teamlimit_optimizer"
while [ $# -gt 0 ]; do
  case "$1" in
    --url) URL="$2"; shift 2;;
    --auth) AUTH="$2"; shift 2;;
    --branch) BRANCH="$2"; shift 2;;
    --interval) INTERVAL="$2"; shift 2;;
    --repo) REPO="$2"; shift 2;;
    *) echo "Unknown option: $1" >&2; exit 1;;
  esac
done
[ -n "$URL" ] && [ -n "$AUTH" ] || { echo "Usage: install-linux.sh --url <frappe-url> --auth 'token <key>:<secret>' [--branch version-16] [--interval 60]" >&2; exit 1; }
for c in curl python3; do command -v "$c" >/dev/null || { echo "Missing: $c" >&2; exit 1; }; done

BIN="$HOME/.local/bin"; CONF_DIR="$HOME/.config/teamlimit-optimizer"
mkdir -p "$BIN" "$CONF_DIR"
curl -fsSL "https://raw.githubusercontent.com/$REPO/$BRANCH/scripts/linux/teamlimit-report.sh" -o "$BIN/teamlimit-report.sh"
chmod +x "$BIN/teamlimit-report.sh"
umask 077
printf 'FRAPPE_URL=%q\nINGEST_AUTH=%q\n' "${URL%/}" "$AUTH" > "$CONF_DIR/config"
echo "Reporting script installed: $BIN/teamlimit-report.sh"

if command -v systemctl >/dev/null && systemctl --user show-environment >/dev/null 2>&1; then
  UNIT="$HOME/.config/systemd/user"; mkdir -p "$UNIT"
  cat > "$UNIT/teamlimit.service" <<UNIT_EOF
[Unit]
Description=Teamlimit Optimizer report

[Service]
Type=oneshot
ExecStart=%h/.local/bin/teamlimit-report.sh
UNIT_EOF
  cat > "$UNIT/teamlimit.timer" <<UNIT_EOF
[Unit]
Description=Teamlimit Optimizer report every ${INTERVAL} minutes

[Timer]
OnBootSec=5min
OnUnitActiveSec=${INTERVAL}min

[Install]
WantedBy=timers.target
UNIT_EOF
  systemctl --user daemon-reload
  systemctl --user enable --now teamlimit.timer >/dev/null
  echo "systemd user timer 'teamlimit.timer' enabled (every ${INTERVAL} minutes)."
else
  if [ "$INTERVAL" -ge 60 ]; then SPEC="0 */$((INTERVAL / 60)) * * *"; else SPEC="*/${INTERVAL} * * * *"; fi
  { crontab -l 2>/dev/null | grep -v teamlimit-report.sh || true; echo "$SPEC $BIN/teamlimit-report.sh"; } | crontab -
  echo "cron job added (every ${INTERVAL} minutes)."
fi
echo "Test with:  $BIN/teamlimit-report.sh --test"
