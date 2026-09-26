#!/usr/bin/env bash
# Checks the LabSync backend end to end: configs, local server, and tunnel.
# Usage: scripts/check_tunnel.sh [hostname]   (defaults to api.guardianagent.dev)
set -uo pipefail

HOST="${1:-api.guardianagent.dev}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PLIST="$ROOT/ios/MeetingApp/MeetingApp/LabSyncConfig.plist"
FAILED=0

pass() { printf 'PASS  %s\n' "$1"; }
fail() { printf 'FAIL  %s\n      %s\n' "$1" "$2"; FAILED=1; }
status() { curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$@"; }

TOKEN="$(sed -n 's/^API_SECRET_KEY=//p' "$ROOT/.env" 2>/dev/null | tail -n 1 | tr -d '\r')"
if [ -n "$TOKEN" ]; then
  pass ".env has API_SECRET_KEY"
else
  fail ".env has API_SECRET_KEY" "Run scripts/setup_tunnel.sh"
fi

APP_TOKEN="$(plutil -extract APIToken raw "$PLIST" 2>/dev/null || true)"
APP_URL="$(plutil -extract BaseURL raw "$PLIST" 2>/dev/null || true)"
if [ -n "$TOKEN" ] && [ "$APP_TOKEN" = "$TOKEN" ]; then
  pass "iOS APIToken matches .env"
else
  fail "iOS APIToken matches .env" "Run scripts/setup_tunnel.sh, then rebuild the app"
fi
if [ "$APP_URL" = "https://$HOST" ]; then
  pass "iOS BaseURL is https://$HOST"
else
  fail "iOS BaseURL is https://$HOST" "Found '$APP_URL'. Run scripts/setup_tunnel.sh $HOST"
fi

if [ -f "$ROOT/contexts/meeting_transcriber-master/meeting_transcriber.py" ]; then
  pass "CCB transcriber source present"
else
  fail "CCB transcriber source present" "Add contexts/meeting_transcriber-master (see docs/ccb-transcriber.md)"
fi

CODE="$(status -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8000/api/health)"
if [ "$CODE" = 200 ]; then
  pass "Local server answers with the token"
elif [ "$CODE" = 401 ]; then
  fail "Local server answers with the token" "401: restart the server with --env-file .env"
else
  fail "Local server answers with the token" "HTTP $CODE: start it with uv run --locked --env-file .env --extra audio --extra server labsync serve --whisper-backend mlx"
fi

CODE="$(status "https://$HOST/api/health")"
case "$CODE" in
  401) pass "Tunnel rejects requests without the token" ;;
  400) fail "Tunnel rejects requests without the token" "400: add httpHostHeader: localhost to ~/.cloudflared/config.yml" ;;
  502) fail "Tunnel rejects requests without the token" "502: the tunnel is up but the local server is not running" ;;
  530) fail "Tunnel rejects requests without the token" "530: run cloudflared tunnel run <tunnel-name>" ;;
  *) fail "Tunnel rejects requests without the token" "HTTP $CODE from https://$HOST" ;;
esac

CODE="$(status -H "Authorization: Bearer $TOKEN" "https://$HOST/api/health")"
if [ "$CODE" = 200 ]; then
  pass "Tunnel accepts requests with the token"
else
  fail "Tunnel accepts requests with the token" "HTTP $CODE from https://$HOST"
fi

exit "$FAILED"
