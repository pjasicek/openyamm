#!/bin/bash
# shoot_direct.sh <tour>: a tour run of the game binary directly (run_game.sh's own preparation fails while the 15:52
# binary dumps core at the end of a headless run). Settings and a startup save copied from an earlier wrapper run.
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
R=$OYR; X=$R/output/studio_cal/xd10; D=/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/0674fbdb-13f6-4cef-9ab2-0b4fbd022550/scratchpad/tourrun
sed -i "/^screenshot_tour_path=/d; s#^\[debug\]#[debug]\nscreenshot_tour_path=$X/shots/$1.yml#" $D/settings.ini
cd $D
OPENYAMM_START_MINIMIZED=1 SDL_AUDIODRIVER=dummy timeout ${SECS:-240} "$OYR/tools/heavy.sh" 6 $R/build-xeen/game/openyamm --world xeen > $X/shots/$1.log 2>&1 &
P=$!; wait $P; echo "exit $? ; $(ls $X/shots/$1 2>/dev/null | wc -l) shots"
