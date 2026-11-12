#!/usr/bin/env bash
# In-game looks (playbook test spots, minimized, isolated): New Sorpigal far + near, Agar's Laboratory. Repo root relative. Usage: scripts/ingame.sh
set -uo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"; cd "$repo"
R=$here/review/ingame
./tools/run_game.sh --isolated pfem-out --world mm6 --map oute3.odm --position -3718.493 3245.946 1 --yaw-radians 3.359 --pitch-degrees -13.751 \
  --set debug.actor_models=true --set debug.immortal=true --set debug.menu_input_tour_path=$R/out.yml --warmup 3 --seconds 40 > $R/out.log 2>&1
./tools/run_game.sh --isolated pfem-outnear --world mm6 --map oute3.odm --position -3718.493 3245.946 1 --yaw-radians 3.359 --pitch-degrees -13.751 \
  --set debug.actor_models=true --set debug.immortal=true --set debug.menu_input_tour_path=$R/out_near.yml --warmup 3 --seconds 40 > $R/out_near.log 2>&1
./tools/run_game.sh --isolated pfem-in --world mm6 --map 6d19.blv --position 1672.832 -2938.578 -46.896 --yaw-radians 3.132 --pitch-degrees -14.868 \
  --set debug.actor_models=true --set debug.immortal=true --set debug.menu_input_tour_path=$R/in.yml --warmup 3 --seconds 40 > $R/in.log 2>&1
echo INGAME DONE
