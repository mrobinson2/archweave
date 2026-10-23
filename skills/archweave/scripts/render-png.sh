#!/usr/bin/env bash
# ArchWeave: render SVG to PNG on macOS or Linux.
# Usage: render-png.sh <diagram.svg> [scale]   (default scale 1.3)
# Prefers rsvg-convert (brew install librsvg); falls back to headless Chrome or Edge.
set -euo pipefail
SVG="${1:?usage: render-png.sh <diagram.svg> [scale]}"
SCALE="${2:-1.3}"
OUT="${SVG%.svg}.png"
W=$(grep -oE '<svg[^>]*\bwidth="[0-9]+' "$SVG" | grep -oE '[0-9]+$' | head -1)
H=$(grep -oE '<svg[^>]*\bheight="[0-9]+' "$SVG" | grep -oE '[0-9]+$' | head -1)
[ -n "$W" ] && [ -n "$H" ] || { echo "SVG root needs numeric width and height" >&2; exit 1; }

if command -v rsvg-convert >/dev/null 2>&1; then
  PW=$(python3 -c "print(int($W*$SCALE))")
  rsvg-convert -w "$PW" "$SVG" -o "$OUT"
  echo "PNG $OUT ($(wc -c < "$OUT" | tr -d ' ') bytes) via rsvg-convert at ${PW}px wide"
  exit 0
fi

for B in "${ARCHWEAVE_BROWSER:-}" \
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge" \
  "/Applications/Chromium.app/Contents/MacOS/Chromium" \
  "$(command -v google-chrome || true)" "$(command -v chromium || true)" "$(command -v microsoft-edge || true)"; do
  [ -n "$B" ] && [ -x "$B" ] || continue
  PROFILE=$(mktemp -d)
  ABS=$(cd "$(dirname "$SVG")" && pwd)/$(basename "$SVG")
  "$B" --headless=new --disable-gpu --hide-scrollbars --no-first-run --user-data-dir="$PROFILE" \
       --window-size="$W,$H" --force-device-scale-factor="$SCALE" --screenshot="$OUT" "file://$ABS" >/dev/null 2>&1 || true
  rm -rf "$PROFILE"
  [ -f "$OUT" ] && { echo "PNG $OUT ($(wc -c < "$OUT" | tr -d ' ') bytes) via $(basename "$B")"; exit 0; }
done
echo "No renderer found. Install librsvg (brew install librsvg) or set ARCHWEAVE_BROWSER." >&2
exit 1
