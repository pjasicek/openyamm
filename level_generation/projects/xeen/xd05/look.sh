#!/bin/bash
# Build, install into the private root and take a tour: look.sh <shot list .py> <out dir name> [seconds]
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
R=$OYR; O=$R/openyamm-studio/build/oymap; L=$R/devdocs/xeen/briefs/xd05/L4; X=$R/output/studio_cal/xd05
cd $R
$O fmt $L >/dev/null
$O build $L --assets $X/root --out $X/build 2>&1 | grep -v "is named\|placeholder not built\|gate_bar rises" | tail -5
$O install $L --build $X/build --root $X/root >/dev/null || exit 1
mkdir -p $X/$2
python3 $OYR/level_generation/projects/xeen/xd05/history/tools/tour.py $X/$1 $X/$2.yml $X/$2
SDL_AUDIODRIVER=dummy "$OYR/tools/heavy.sh" 6 tools/run_game.sh --isolated xd05look$RANDOM --world mm7 --map xeen_xd05.blv --assets $X/root --set debug.screenshot_tour_path=$X/$2.yml --warmup 4 --seconds ${3:-300} > $X/$2.log 2>&1
echo "tour exit $?"; ls $X/$2 | wc -l
python3 $X/sheet.py $X/$2_sheet.jpg "$X/$2/*.png"
