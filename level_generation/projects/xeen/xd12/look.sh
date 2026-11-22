#!/bin/bash
# Build a project folder ($1), install it into its own mount ($2) and take the tour $3 (log $4). Seconds $5.
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
R=$OYR
O=$R/openyamm-studio/build/oymap
P=$1; M=$2; T=$3; LOG=$4
X=$R/output/studio_cal/xd12
cd $R
$O fmt $P >/dev/null
$O build $P --assets output/studio_play/xeen_root --out $X/lookbuild 2>&1 | grep -v "is named\|placeholder not built" | tail -5
$O install $P --build $X/lookbuild --mount $M --assets output/studio_play/xeen_root >/dev/null || exit 1
SDL_AUDIODRIVER=dummy "$OYR/tools/heavy.sh" 6 tools/run_game.sh --isolated xd12look$RANDOM --world mm7 --map xeen_xd12.blv --assets $R/output/studio_play/xeen_root --extra-mount $M --set debug.screenshot_tour_path=$T --warmup 4 --seconds ${5:-200} > $LOG 2>&1
echo "tour exit $?"
