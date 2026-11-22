#!/bin/bash
# Usage: svg2png.sh <key> ...  (A8 session 16, a copy of a8_s13/svg2png.sh). devdocs/xeen/mockups/act6_graphs/<key>.svg
# -> output/studio_cal/fd01/png/<key>.png (headless Chrome, own profile).
set -e
ROOT="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"
SVGDIR=${SVGDIR:-$ROOT/devdocs/xeen/mockups/act6_graphs}
prof=$ROOT/output/studio_cal/fd01/chrome_${PROFILE:-lead}
mkdir -p "$prof" $ROOT/output/studio_cal/fd01/png
for k in "$@"; do
  svg=$SVGDIR/$k.svg
  read W H < <(python3 -c "import re;s=open('$svg').read(3000);m=re.search(r'width=\"([0-9.]+)\" height=\"([0-9.]+)\"',s);print(int(float(m.group(1)))+16,int(float(m.group(2)))+16)")
  timeout 90 google-chrome --headless=new --disable-gpu --no-sandbox --user-data-dir="$prof" --hide-scrollbars \
    --window-size=$W,$H --screenshot=$ROOT/output/studio_cal/fd01/png/$k.png "file://$svg" >/dev/null 2>&1 || true
  echo "$k: $ROOT/output/studio_cal/fd01/png/$k.png ${W}x${H}"
done
