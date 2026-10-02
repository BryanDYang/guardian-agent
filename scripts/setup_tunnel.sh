#!/usr/bin/env bash
# Exposes the local LabSync backend through a Cloudflare tunnel and points the
# iOS app (LabSyncConfig.plist) at it and at the Supabase project in .env.
# Safe to re-run.
#
# Usage: scripts/setup_tunnel.sh [hostname] [tunnel-name]
#   hostname     defaults to api.guardianagent.dev
#   tunnel-name  defaults to labsync
set -euo pipefail

HOST="${1:-api.guardianagent.dev}"
TUNNEL="${2:-labsync}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CF_DIR="$HOME/.cloudflared"
CF_CONFIG="$CF_DIR/config.yml"
ENV_FILE="$ROOT/.env"
PLIST="$ROOT/ios/MeetingApp/MeetingApp/LabSyncConfig.plist"
PLIST_TEMPLATE="$ROOT/ios/MeetingApp/LabSyncConfig.example.plist"

step() { printf '\n==> %s\n' "$1"; }
fail() { printf '\nError: %s\n' "$1" >&2; exit 1; }

command -v cloudflared >/dev/null || fail "cloudflared is not installed. Run: brew install cloudflared"
command -v plutil >/dev/null || fail "plutil not found. This script requires macOS."

step "Cloudflare login"
if [ -f "$CF_DIR/cert.pem" ]; then
  echo "Already logged in."
else
  cloudflared tunnel login
fi

tunnel_id() {
  cloudflared tunnel list --name "$TUNNEL" -o json |
    python3 -c 'import json, sys; t = json.load(sys.stdin) or []; print(t[0]["id"] if t else "")'
}

step "Tunnel '$TUNNEL'"
ID="$(tunnel_id)"
if [ -z "$ID" ]; then
  cloudflared tunnel create "$TUNNEL"
  ID="$(tunnel_id)"
else
  echo "Reusing tunnel $ID."
fi
# Path to the local Cloudflare credentials file, not a credential value.
CREDENTIALS_FILE="$CF_DIR/$ID.json"
[ -f "$CREDENTIALS_FILE" ] || fail "Tunnel '$TUNNEL' belongs to another machine (no $CREDENTIALS_FILE here).
Pick your own names, for example: $0 api-yourname.guardianagent.dev labsync-yourname"

step "DNS route $HOST"
cloudflared tunnel route dns "$TUNNEL" "$HOST" ||
  fail "Could not route $HOST to '$TUNNEL'. If another tunnel already uses $HOST, pick a different hostname."

step "Tunnel config $CF_CONFIG"
if [ -f "$CF_CONFIG" ] &&
  grep -q "hostname: $HOST" "$CF_CONFIG" &&
  grep -q "$ID" "$CF_CONFIG" &&
  grep -q "httpHostHeader: localhost" "$CF_CONFIG"; then
  echo "Already configured."
else
  if [ -f "$CF_CONFIG" ]; then
    BACKUP="$CF_CONFIG.bak.$(date +%Y%m%d%H%M%S)"
    mv "$CF_CONFIG" "$BACKUP"
    echo "Moved the previous config to $BACKUP."
  fi
  cat >"$CF_CONFIG" <<EOF
tunnel: $ID
credentials-file: $CREDENTIALS_FILE

ingress:
  - hostname: $HOST
    service: http://127.0.0.1:8000
    originRequest:
      httpHostHeader: localhost
  - service: http_status:404
EOF
  echo "Wrote $CF_CONFIG."
fi

step "Supabase settings in $ENV_FILE"
[ -f "$ENV_FILE" ] || fail "Create .env first: cp .env.example .env"
env_value() { sed -n "s/^$1=//p" "$ENV_FILE" | tail -n 1 | tr -d '\r'; }
SUPABASE_URL="$(env_value SUPABASE_URL)"
ANON_KEY="$(env_value SUPABASE_ANON_KEY)"
if [ -z "$SUPABASE_URL" ] || [ -z "$ANON_KEY" ]; then
  fail "Set SUPABASE_URL and SUPABASE_ANON_KEY in .env (Supabase dashboard: Project Settings > API), then re-run."
fi
case "$SUPABASE_URL" in
  *127.0.0.1* | *localhost*) echo "Warning: $SUPABASE_URL is local Supabase. Phones and teammates can't sign in through it." ;;
esac
chmod 600 "$ENV_FILE"

step "iOS config $PLIST"
[ -f "$PLIST" ] || cp "$PLIST_TEMPLATE" "$PLIST"
plutil -replace BaseURL -string "https://$HOST" "$PLIST"
plutil -replace SupabaseURL -string "$SUPABASE_URL" "$PLIST"
plutil -replace SupabaseAnonKey -string "$ANON_KEY" "$PLIST"
echo "Set BaseURL to https://$HOST and the Supabase settings to match .env."

if [ ! -f "$ROOT/contexts/meeting_transcriber-master/meeting_transcriber.py" ]; then
  printf '\nWarning: contexts/meeting_transcriber-master is missing, so uploads will fail at\n'
  printf 'transcription. See docs/ccb-transcriber.md.\n'
fi

cat <<EOF

Setup complete. Next:
  1. Terminal 1:  cd "$ROOT" && uv run --locked --env-file .env --extra audio --extra server labsync serve --whisper-backend mlx --whisper-model medium
  2. Terminal 2:  cloudflared tunnel run $TUNNEL
  3. Rebuild the iOS app in Xcode so it bundles the updated LabSyncConfig.plist.
  4. Verify:      scripts/check_tunnel.sh $HOST
EOF
