#!/usr/bin/env bash
# Points the iOS app at Will's backend and the Supabase project it signs users in
# with. Ask Will for the Supabase URL and anon key. Both are public: they ship in
# the app, and they let people sign in, not read data.
#
# Usage: scripts/use_shared_backend.sh [hostname]   (defaults to api.guardianagent.dev)
set -euo pipefail

HOST="${1:-api.guardianagent.dev}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PLIST="$ROOT/ios/MeetingApp/MeetingApp/LabSyncConfig.plist"
PLIST_TEMPLATE="$ROOT/ios/MeetingApp/LabSyncConfig.example.plist"

command -v plutil >/dev/null || { echo "Error: this script requires macOS." >&2; exit 1; }

echo "This app uses Will's backend at https://$HOST."
read -r -p "Supabase URL (https://<project>.supabase.co): " SUPABASE_URL
read -r -p "Supabase anon key: " ANON_KEY
if [ -z "$SUPABASE_URL" ] || [ -z "$ANON_KEY" ]; then
  echo "Error: enter both values." >&2
  exit 1
fi

[ -f "$PLIST" ] || cp "$PLIST_TEMPLATE" "$PLIST"
plutil -replace BaseURL -string "https://$HOST" "$PLIST"
plutil -replace SupabaseURL -string "$SUPABASE_URL" "$PLIST"
plutil -replace SupabaseAnonKey -string "$ANON_KEY" "$PLIST"
echo "Saved to ios/MeetingApp/MeetingApp/LabSyncConfig.plist (gitignored)."

CODE="$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 "https://$HOST/api/health" || true)"
case "$CODE" in
  200) echo "OK: Will's backend is online." ;;
  502|530) echo "Will's backend is offline right now (HTTP $CODE). Ask him to start it." ;;
  *) echo "Could not reach https://$HOST (HTTP $CODE)." ;;
esac

echo "Next: open ios/MeetingApp/MeetingApp.xcodeproj, rebuild the app, and sign up."
