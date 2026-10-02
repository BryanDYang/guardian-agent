#!/usr/bin/env bash
# Checks the LabSync backend end to end: configs, local server, and tunnel.
# Usage: scripts/check_tunnel.sh [--shared] [hostname]
# --shared skips the local server and transcriber checks.
set -uo pipefail

SHARED=0
if [ "${1:-}" = "--shared" ]; then
  SHARED=1
  shift
fi
if [ "$#" -gt 1 ] || [[ "${1:-}" = -* ]]; then
  echo "Usage: scripts/check_tunnel.sh [--shared] [hostname]" >&2
  exit 2
fi
HOST="${1:-api.guardianagent.dev}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PLIST="$ROOT/ios/MeetingApp/MeetingApp/LabSyncConfig.plist"
FAILED=0

pass() { printf 'PASS  %s\n' "$1"; }
fail() { printf 'FAIL  %s\n      %s\n' "$1" "$2"; FAILED=1; }
status() { curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$@"; }

if [ "$SHARED" = 1 ]; then
  SETUP="scripts/use_shared_backend.sh $HOST"
else
  SETUP="scripts/setup_tunnel.sh $HOST"
fi
env_value() { sed -n "s/^$1=//p" "$ROOT/.env" 2>/dev/null | tail -n 1 | tr -d '\r'; }
plist_value() { plutil -extract "$1" raw "$PLIST" 2>/dev/null || true; }
APP_URL="$(plist_value BaseURL)"
APP_SUPABASE="$(plist_value SupabaseURL)"
APP_KEY="$(plist_value SupabaseAnonKey)"

if [ "$APP_URL" = "https://$HOST" ]; then
  pass "iOS BaseURL is https://$HOST"
else
  fail "iOS BaseURL is https://$HOST" "Found '$APP_URL'. Run $SETUP, then rebuild the app"
fi
case "$APP_SUPABASE" in
  "") fail "iOS SupabaseURL is a hosted project" "Run $SETUP, then rebuild the app" ;;
  *127.0.0.1* | *localhost*) fail "iOS SupabaseURL is a hosted project" "Found $APP_SUPABASE. Phones and teammates can't reach local Supabase" ;;
  *) pass "iOS SupabaseURL is a hosted project" ;;
esac
if [ -n "$APP_KEY" ]; then
  pass "iOS SupabaseAnonKey is set"
else
  fail "iOS SupabaseAnonKey is set" "Run $SETUP, then rebuild the app"
fi

if [ "$SHARED" = 0 ]; then
  # The server only accepts tokens issued by the Supabase project in its .env.
  if [ -n "$APP_SUPABASE" ] && [ "$(env_value SUPABASE_URL)" = "$APP_SUPABASE" ]; then
    pass "Server and app use the same Supabase"
  else
    fail "Server and app use the same Supabase" "Set SUPABASE_URL in .env, re-run $SETUP, rebuild the app, restart the server"
  fi

  if [ -f "$ROOT/contexts/meeting_transcriber-master/meeting_transcriber.py" ]; then
    pass "CCB transcriber source present"
  else
    fail "CCB transcriber source present" "Add contexts/meeting_transcriber-master (see docs/ccb-transcriber.md)"
  fi

  CODE="$(status http://127.0.0.1:8000/api/health)"
  if [ "$CODE" = 200 ]; then
    pass "Local server is running"
  else
    fail "Local server is running" "HTTP $CODE: start it with uv run --locked --env-file .env --extra audio --extra server labsync serve --whisper-backend mlx --whisper-model medium"
  fi
fi

CODE="$(status "https://$HOST/api/health")"
case "$CODE" in
  200) pass "Tunnel reaches the server" ;;
  400) fail "Tunnel reaches the server" "400: add httpHostHeader: localhost to ~/.cloudflared/config.yml" ;;
  502) fail "Tunnel reaches the server" "502: the tunnel is up but the local server is not running" ;;
  530) fail "Tunnel reaches the server" "530: run cloudflared tunnel run <tunnel-name>" ;;
  *) fail "Tunnel reaches the server" "HTTP $CODE from https://$HOST" ;;
esac

CODE="$(status "https://$HOST/api/v1/me")"
if [ "$CODE" = 401 ]; then
  pass "Tunnel turns away requests without a sign-in"
else
  fail "Tunnel turns away requests without a sign-in" "HTTP $CODE: pull the latest code and restart the server"
fi

exit "$FAILED"
