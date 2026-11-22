#!/bin/bash
# Build, install into the scratch root and take the tour given as $1 (a tour yml); log $2.
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
R=$OYR
O=$R/openyamm-studio/build/oymap
L=$R/devdocs/xeen/briefs/xd04/L4
X=$R/output/studio_cal/xd04
cd $R
$O fmt $L >/dev/null
$O build $L --assets assets_dev --out $X/build 2>&1 | grep -v "is named\|placeholder not built" | tail -5
$O install $L --build $X/build --root $X/root >/dev/null || exit 1
SDL_AUDIODRIVER=dummy "$OYR/tools/heavy.sh" 6 tools/run_game.sh --isolated xd04look$RANDOM --world mm7 --map xeen_xd04.blv --assets $X/root --set debug.screenshot_tour_path=$1 --warmup 4 --seconds ${3:-240} > $2 2>&1
echo "tour exit $?"
