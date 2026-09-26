#!/usr/bin/env bash
# Points the iOS app at Will's backend. Ask Will privately for the API key.
#
# Usage: scripts/use_shared_backend.sh [hostname]   (defaults to api.guardianagent.dev)
set -euo pipefail

HOST="${1:-api.guardianagent.dev}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PLIST="$ROOT/ios/MeetingApp/MeetingApp/LabSyncConfig.plist"
PLIST_TEMPLATE="$ROOT/ios/MeetingApp/LabSyncConfig.example.plist"

command -v plutil >/dev/null || { echo "Error: this script requires macOS." >&2; exit 1; }

echo "This app uses Will's backend at https://$HOST."
echo "You need Will's API key (API_SECRET_KEY). Ask him for it privately; never commit it."
read -r -s -p "Paste the API key: " TOKEN
echo
[ -n "$TOKEN" ] || { echo "Error: no key entered." >&2; exit 1; }

[ -f "$PLIST" ] || cp "$PLIST_TEMPLATE" "$PLIST"
plutil -replace BaseURL -string "https://$HOST" "$PLIST"
plutil -replace APIToken -string "$TOKEN" "$PLIST"
echo "Saved to ios/MeetingApp/MeetingApp/LabSyncConfig.plist (gitignored)."

CODE="$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 \
  -H "Authorization: Bearer $TOKEN" "https://$HOST/api/health" || true)"
case "$CODE" in
  200) echo "OK: the key works and Will's backend is online." ;;
  401) echo "The key was rejected. Check it with Will." ;;
  502|530) echo "Will's backend is offline right now (HTTP $CODE). Ask him to start it." ;;
  *) echo "Could not reach https://$HOST (HTTP $CODE)." ;;
esac

echo "Next: open ios/MeetingApp/MeetingApp.xcodeproj and rebuild the app."
