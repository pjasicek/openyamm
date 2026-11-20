#!/bin/sh
# Capture the mockups at 1024 x 768 with headless Chrome into previews/.
cd "$(dirname "$0")"
mkdir -p previews
shot()
{
  google-chrome --headless --disable-gpu --hide-scrollbars --virtual-time-budget=4000 --window-size=1024,768 \
    --screenshot="$PWD/previews/$1.png" "file://$PWD/$2" >/dev/null 2>&1
}
shot a mockup_a.html
shot a_tip_sweeping 'mockup_a.html?tip=row:sweeping'
shot a_tip_cleave 'mockup_a.html?tip=row:cleave'
shot a_tip_frenzy 'mockup_a.html?tip=row:frenzy'
shot a_tip_multishot 'mockup_a.html?tip=row:multishot'
shot a_tip_slot4 'mockup_a.html?tip=ks:3'
shot a_tip_archon 'mockup_a.html?tip=ks:2'
shot a_slot3_open 'mockup_a.html?slot3=open&tip=ks:2'
shot b mockup_b.html
shot b_choose 'mockup_b.html?slot3=open'
shot b_slot4 'mockup_b.html?pick=3'
shot b_trees 'mockup_b.html?view=trees'
shot b_trees_tip 'mockup_b.html?view=trees&tip=row:sweeping'
