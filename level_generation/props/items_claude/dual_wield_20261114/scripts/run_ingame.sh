#!/bin/sh
# In-game captures of dual wielding (README.md), 1600x900, MAW solo run, the new knight given two weapons with
# `viewmodel equip` (the real kit path: GameApplication builds the Dual kit from the member's hands).
# Usage: scripts/run_ingame.sh <pair> <outdoor|indoor> [tag]
# pair: sword (Iron Longsword + Templar's Sword), daggersword (Dark Elven Longsword + Crystal Dagger),
#       axe (Battleaxe + Battle Hatchet), mace (Sturdy Mace + Temple Mace), minotaur (two battle axe templates by
#       `viewmodel kit dual`: the stock knight wields a two-handed axe two-handed, only a MAW Minotaur holds one in
#       each hand)
# Poses: idle, the right hand's cut, the left hand's cut and the cross slash, each near its Hit key.
# Writes ingame/<tag>/<pair>_<place>/NN_<pose>.png.
cd "$(dirname "$0")/../../../../.." || exit 1
P=$PWD/level_generation/props/items_claude/dual_wield_20261114
PAIR=$1; PLACE=$2; TAG=${3:-v1}
case $PAIR in
  sword) MAIN=1; OFF=4 ;;
  daggersword) MAIN=3; OFF=22 ;;
  axe) MAIN=33; OFF=32 ;;
  mace) MAIN=66; OFF=68 ;;
  minotaur) MAIN=0; OFF=0; KIT="viewmodel kit dual w_battleaxe.glb w_battleaxe.glb" ;;
  *) echo "unknown pair $PAIR"; exit 2 ;;
esac
RIGHT=${RIGHT:-"dualattackright 0.30"}
LEFT=${LEFT:-"dualattackleft 0.30"}
CROSS=${CROSS:-"dualattackpower 0.40"}
out=$P/ingame/$TAG/${PAIR}_$PLACE
mkdir -p "$out"
tour=$out/tour.yml
{
  echo "output_dir: $out"
  echo "exit: true"
  echo "steps:"
  echo "  - wait: 3"
  if [ -n "$KIT" ]; then echo "  - console: $KIT"; else echo "  - console: viewmodel equip $MAIN $OFF"; fi
  echo "  - wait: 2.5"
  echo "  - capture: idle"
  echo "  - console: viewmodel pose $RIGHT"
  echo "  - wait: 0.6"
  echo "  - capture: right"
  echo "  - console: viewmodel pose $LEFT"
  echo "  - wait: 0.6"
  echo "  - capture: left"
  echo "  - console: viewmodel pose $CROSS"
  echo "  - wait: 0.6"
  echo "  - capture: cross"
  for extra in $EXTRA; do
    clip=${extra%@*}; t=${extra#*@}
    echo "  - console: viewmodel pose $clip $t"
    echo "  - wait: 0.6"
    echo "  - capture: ${clip}_$t"
  done
  echo "  - console: viewmodel pose off"
} > "$tour"
case $PLACE in
  outdoor) where="--map oute3.odm" ;;
  indoor) where="--map 6d05.blv --position 1664 -1920 0 --yaw-radians 3.1416 --pitch-degrees 0" ;;  # into the cave from the entrance door
esac
# shellcheck disable=SC2086
SDL_AUDIODRIVER=dummy ./tools/run_game.sh --isolated "dual_${TAG}_${PAIR}_$PLACE" --world mm6 $where \
  --ruleset maw:solo --set video.resolution=1600x900 --set video.window_mode=windowed --set debug.console=true \
  --set gameplay.enemy_health_bars=off --set debug.menu_input_tour_path="$tour" --seconds 90 \
  > "$out/run.log" 2>&1
echo "$PAIR $PLACE exit $? $(ls "$out" | grep -c png) png"
