#!/bin/bash
# Play a playtest headless against xeen_root with X2's mount in front. walk.sh <x1|x2> <n> [playtest file]
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
export SDL_AUDIODRIVER=dummy OPENYAMM_START_MINIMIZED=1   # agent game runs: silent, minimised
cd "$OYR"
K=$1; N=${2:-1}; T=${3:-$PWD/devdocs/xeen/briefs/$K/L4/playtest.yml}
C=$PWD/output/studio_cal/x2
STAMP=$(date +%s%N)
U=$C/run/user_${K}_${N}_$STAMP
mkdir -p "$U"
SDL_AUDIODRIVER=dummy "$OYR/tools/heavy.sh" 6 $PWD/build/game/openyamm --asset-root "$PWD/output/studio_play/xeen_root" --extra-mount "${MOUNT:-$C/mount}" \
  --world mm7 --user-data "$U" --headless-run-scenario "$T" --scenario-no-color \
  > $C/run/walk_${K}_$N.log 2>&1
echo "exit $?" >> $C/run/walk_${K}_$N.log
