#!/usr/bin/env bash
# Register the shepherd native messaging host with every Chromium-family
# browser config dir that exists. Re-run after moving the checkout.
set -euo pipefail

NAME="io.github.d1rewolf.shepherd"
EXTENSION_ID="dnbdkoldcnmedlanooaaflemdhldiapg"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOST="$HERE/shepherd-native-host"
CONFIG="${XDG_CONFIG_HOME:-$HOME/.config}"

chmod +x "$HOST"

installed=0
for browser in chromium google-chrome google-chrome-beta BraveSoftware/Brave-Browser; do
  [[ -d "$CONFIG/$browser" ]] || continue
  dir="$CONFIG/$browser/NativeMessagingHosts"
  mkdir -p "$dir"
  cat >"$dir/$NAME.json" <<EOF
{
  "name": "$NAME",
  "description": "Shepherd URL router",
  "path": "$HOST",
  "type": "stdio",
  "allowed_origins": ["chrome-extension://$EXTENSION_ID/"]
}
EOF
  echo "Installed $dir/$NAME.json"
  installed=1
done

if ((!installed)); then
  echo "No Chromium-family config dir found under $CONFIG" >&2
  exit 1
fi

cat <<EOF

Now load the extension in each profile:
  - one profile: chrome://extensions -> Developer mode -> Load unpacked -> $(dirname "$HERE")/browser-extension
  - every profile (Chromium only): add it to --load-extension in ~/.config/chromium-flags.conf
    (comma-separate it from any extensions already listed there; a second
    --load-extension line replaces the first)
EOF
