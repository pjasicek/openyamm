#!/bin/sh
# Capture every view to previews/ with headless Chrome (stage only, 1600 x 900).
cd "$(dirname "$0")"
for v in a b c std; do
  google-chrome --headless --disable-gpu --hide-scrollbars --virtual-time-budget=4000 --window-size=1600,900 \
    --screenshot="$PWD/previews/$v.png" "file://$PWD/index.html?view=$v&export=1" >/dev/null 2>&1
done
for t in 1 2; do
  google-chrome --headless --disable-gpu --hide-scrollbars --virtual-time-budget=4000 --window-size=1600,900 \
    --screenshot="$PWD/previews/b_tree$t.png" "file://$PWD/index.html?view=b&tree=$t&export=1" >/dev/null 2>&1
done
