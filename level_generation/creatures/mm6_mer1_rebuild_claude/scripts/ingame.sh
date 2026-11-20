#!/usr/bin/env bash
# In-game looks (playbook test spots, minimized, isolated): New Sorpigal (fight, death, corpse; tiers frozen facing the party),
# Agar's Laboratory (the same indoors). Usage: scripts/ingame.sh
set -uo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"; cd "$repo"
R=$here/review/ingame
OUT="--world mm6 --map oute3.odm --position -3718.493 3245.946 1 --yaw-radians 3.359 --pitch-degrees -13.751"
IN="--world mm6 --map 6d19.blv --position 1672.832 -2938.578 -46.896 --yaw-radians 3.132 --pitch-degrees -14.868"
S="--set debug.actor_models=true --set debug.immortal=true"
./tools/run_game.sh --isolated mer1-out $OUT $S --set debug.menu_input_tour_path=$R/out.yml --warmup 3 --seconds 40 > $R/out.log 2>&1
./tools/run_game.sh --isolated mer1-outfrozen $OUT $S --set debug.menu_input_tour_path=$R/out_frozen.yml --warmup 3 --seconds 25 > $R/out_frozen.log 2>&1
./tools/run_game.sh --isolated mer1-in $IN $S --set debug.menu_input_tour_path=$R/in.yml --warmup 3 --seconds 40 > $R/in.log 2>&1
./tools/run_game.sh --isolated mer1-infrozen $IN $S --set debug.menu_input_tour_path=$R/in_frozen.yml --warmup 3 --seconds 25 > $R/in_frozen.log 2>&1
echo INGAME DONE
