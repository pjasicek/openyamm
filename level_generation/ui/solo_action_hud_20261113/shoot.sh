#!/bin/sh
# Capture every view to previews/ with headless Chrome (stage only, 1600 x 900).
cd "$(dirname "$0")"
for v in a2 r a b c d today bar talents portrait; do
  google-chrome --headless --disable-gpu --hide-scrollbars --virtual-time-budget=4000 --window-size=1600,900 \
    --screenshot="$PWD/previews/$v.png" "file://$PWD/index.html?view=$v&export=1" >/dev/null 2>&1
done
google-chrome --headless --disable-gpu --hide-scrollbars --virtual-time-budget=4000 --window-size=1700,1500 \
  --screenshot="$PWD/previews/page_r.png" "file://$PWD/index.html?view=r" >/dev/null 2>&1
