#!/usr/bin/env bash
# Runs the in-game tours of tag $1 (P1 and P2 at once: two game processes), waiting on exact PIDs.
cd /home/pjasicek/github/OpenYAMM
D=level_generation/decorations/xeen_planedevices_claude/work/ingame
pids=()
for p in p1 p2; do
    ./tools/run_game.sh --isolated xs11-dev-$1-$p --binary build-xeen/game/openyamm --world xeen --map xeen_$p.blv \
        --warmup 3 --seconds 70 --set debug.menu_input_tour_path=$PWD/$D/$1_$p.yml > $D/$1_$p.log 2>&1 &
    pids+=($!)
done
for p in "${pids[@]}"; do while kill -0 "$p" 2>/dev/null; do sleep 2; done; done
echo QUEUE_DONE
