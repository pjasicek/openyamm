#!/usr/bin/env bash
# Render the proposal mockups to previews/ with headless Chrome through a local HTTP server
# (the fonts do not load from file://). Usage: tools/render_mockups.sh [port]
set -euo pipefail
study="$(cd "$(dirname "$0")/.." && pwd)"
repo="$(cd "$study/../../.." && pwd)"
port="${1:-8931}"
out="$study/previews"
mkdir -p "$out"
python3 -m http.server "$port" --bind 127.0.0.1 --directory "$repo" > /dev/null 2>&1 &
server=$!
trap 'kill $server' EXIT
sleep 1
base="http://127.0.0.1:$port/level_generation/ui/mm9_talk_dialogue_study_20261102/mockups"
profile="$(mktemp -d)"

shot()
{
    local page="$1" query="$2" name="$3" width="${4:-1600}"
    google-chrome --headless=new --disable-gpu --hide-scrollbars --user-data-dir="$profile" \
        --force-device-scale-factor=1 --window-size="$width,900" --virtual-time-budget=3000 \
        --screenshot="$out/$name.png" "$base/$page?$query" > /dev/null 2>&1
    echo "$out/$name.png"
}

for state in typical many long service; do
    shot a_conversation_bar.html "state=$state" "a_$state"
    shot b_audience_frame.html "state=$state" "b_$state"
done
for state in typical many long; do
    shot c_chronicle.html "state=$state" "c_$state"
done
# Aspect and touch checks of the recommended proposal: 4:3 and a 19.5:9 phone, both with the many-choices state.
shot a_conversation_bar.html "state=many&w=1200" a_many_4x3 1200
shot a_conversation_bar.html "state=many&w=1950&touch=1" a_many_phone_touch 1950
shot a_conversation_bar.html "state=long&w=1200" a_long_4x3 1200
rm -rf "$profile"
# Overview sheet: each proposal's typical and many-choices states side by side.
python3 - "$out" <<'PY'
import sys
from pathlib import Path
from PIL import Image
out = Path(sys.argv[1])
names = [["a_typical", "a_many"], ["b_typical", "b_many"], ["c_typical", "c_many"]]
sheet = Image.new("RGB", (1600, 1350), (5, 9, 10))
for row, pair in enumerate(names):
    for column, name in enumerate(pair):
        sheet.paste(Image.open(out / f"{name}.png").convert("RGB").resize((800, 450), Image.LANCZOS),
                    (column * 800, row * 450))
sheet.save(out / "overview.jpg", quality=90)
PY
