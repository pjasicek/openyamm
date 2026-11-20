#!/bin/sh
# Capture the mockups at 1280 x 720 with headless Chrome into previews/.
cd "$(dirname "$0")"
mkdir -p previews
shot()
{
  google-chrome --headless --disable-gpu --hide-scrollbars --virtual-time-budget=4000 --window-size=1280,720 \
    --screenshot="$PWD/previews/$1.png" "file://$PWD/$2" >/dev/null 2>&1
}
shot tree_knight_120 'mockup_tree.html?class=knight_2h&diff=nightmare&level=120&tip=ground_slam'
shot tree_knight_20 'mockup_tree.html?class=knight_2h&diff=nightmare&level=20&tip=cleave'
shot tree_archmage_500 'mockup_tree.html?class=archmage&diff=madness&level=500&tip=echo'
shot tree_archer_1000 'mockup_tree.html?class=archer&diff=madness&level=1000&tip=bow_training'
shot tree_empty_50 'mockup_tree.html?class=knight_sns&diff=doom&level=50&build=empty'
shot web_knight_120 'mockup_web.html?class=knight_2h&diff=nightmare&level=120&tip=sweeping_blows'
shot web_archer_500 'mockup_web.html?class=archer&diff=nightmare&level=500&tip=rain_of_arrows'
shot curve_typical_nightmare 'mockup_curve.html?class=typical&diff=nightmare'
shot curve_priest_madness 'mockup_curve.html?class=priest&diff=madness'
shot curve_dragon_nightmare 'mockup_curve.html?class=dragon&diff=nightmare'
