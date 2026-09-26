#!/usr/bin/env bash
# Exposes the local LabSync backend through a Cloudflare tunnel and writes the
# matching server (.env) and iOS (LabSyncConfig.plist) configs. Safe to re-run.
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
CREDENTIALS="$CF_DIR/$ID.json"
[ -f "$CREDENTIALS" ] || fail "Tunnel '$TUNNEL' belongs to another machine (no $CREDENTIALS here).
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
credentials-file: $CREDENTIALS

ingress:
  - hostname: $HOST
    service: http://127.0.0.1:8000
    originRequest:
      httpHostHeader: localhost
  - service: http_status:404
EOF
  echo "Wrote $CF_CONFIG."
fi

step "Server token $ENV_FILE"
if grep -q '^API_SECRET_KEY=.' "$ENV_FILE" 2>/dev/null; then
  echo "Keeping the existing API_SECRET_KEY."
else
  NEW_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
  {
    grep -v '^API_SECRET_KEY=' "$ENV_FILE" 2>/dev/null || true
    echo "API_SECRET_KEY=$NEW_TOKEN"
  } >"$ENV_FILE.tmp"
  mv "$ENV_FILE.tmp" "$ENV_FILE"
  echo "Generated a new API_SECRET_KEY."
fi
chmod 600 "$ENV_FILE"
TOKEN="$(sed -n 's/^API_SECRET_KEY=//p' "$ENV_FILE" | tail -n 1 | tr -d '\r')"

step "iOS config $PLIST"
[ -f "$PLIST" ] || cp "$PLIST_TEMPLATE" "$PLIST"
plutil -replace BaseURL -string "https://$HOST" "$PLIST"
plutil -replace APIToken -string "$TOKEN" "$PLIST"
echo "Set BaseURL to https://$HOST and APIToken to match .env."

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
