#!/bin/sh
# In-game captures of the pole set (README.md "In-game checks"), 1600x900, MAW solo run. Real items go into the new
# knight's hands with `viewmodel equip <id> 0` (the real kit path: the main hand's held.yml kind picks the pole set and
# held_tiers.yml's kind template the model): Steel Spear (42, spear), Titanic Trident (1643, trident) and Light Poleaxe
# (1630, poleaxe: the halberd template). Per kind and tier (`viewmodel tier`): the idle, then held poses: the jab at
# its Hit (`swing`), the sweep at its Hit, the overhead chop at its Hit and the power lunge at its Hit.
# Usage: scripts/run_ingame.sh <outdoor|indoor> [tag] [tiers "1 2 3 4"] [kinds "spear trident halberd"]
# ARMS=<absolute arms.glb>: hold arms from disk ([debug] view_model_path, its weapons beside it) instead of the
# engine's. POSES="name@clip@seconds ...": other held poses. LIVE=1: instead of held poses, `viewmodel trace on` and
# Attack pressed five times (one round of the combo: jab, jab, sweep, chop, lunge), captures 0.15 and 0.35 s after
# each press.
# Writes ingame/<tag>/<kind>_<place>/<t1..t4>_<pose>.png (the weapons project's to_viewer.py layout).
cd "$(dirname "$0")/../../../../.." || exit 1
P=$PWD/level_generation/props/items_claude/pole_set_20261114
PLACE=$1; TAG=${2:-v1}; TIERS=${3:-"1 2 3 4"}; KINDS=${4:-"spear trident halberd"}
POSES=${POSES:-"swing@poleattackright@0.333 sweep@poleattackright_chop@0.333 chop@poleattackleft_chop@0.233 lunge@poleattackpower@0.633"}
case $PLACE in
  outdoor) where="--map oute3.odm" ;;
  indoor) where="--map 6d05.blv --position 1664 -1920 0 --yaw-radians 3.1416 --pitch-degrees 0" ;;  # into the cave
  *) echo "unknown place $PLACE"; exit 2 ;;
esac
# The tour goes to a temporary file: level_generation's rules would admit a .yml under ingame/ into git.
tour=$(mktemp --suffix=.yml) || exit 1
trap 'rm -f "$tour"' EXIT
mkdir -p "$P/ingame/$TAG"
{
  echo "output_dir: $P/ingame/$TAG"
  echo "exit: true"
  echo "steps:"
  echo "  - wait: 3"
  for kind in $KINDS; do
    case $kind in
      spear) item=42 ;;
      trident) item=1643 ;;
      halberd) item=1630 ;;
      *) echo "unknown kind $kind" >&2; exit 2 ;;
    esac
    mkdir -p "$P/ingame/$TAG/${kind}_$PLACE"
    echo "  - console: viewmodel equip $item 0"
    echo "  - wait: 2"
    if [ -n "$LIVE" ]; then
      echo "  - console: viewmodel trace on"
      for blow in 1 2 3 4 5; do
        echo "  - action: attack"
        echo "  - wait: 0.15"
        echo "  - capture: ${kind}_$PLACE/live${blow}_a"
        echo "  - wait: 0.2"
        echo "  - capture: ${kind}_$PLACE/live${blow}_b"
        echo "  - wait: 0.25"
      done
      continue
    fi
    for t in $TIERS; do
      echo "  - console: viewmodel tier $t"
      echo "  - wait: 1.5"
      echo "  - capture: ${kind}_$PLACE/t${t}_idle"
      for pose in $POSES; do
        name=${pose%%@*}; rest=${pose#*@}; clip=${rest%@*}; seconds=${rest#*@}
        echo "  - console: viewmodel pose $clip $seconds"
        echo "  - wait: 0.6"
        echo "  - capture: ${kind}_$PLACE/t${t}_$name"
      done
      echo "  - console: viewmodel pose off"
    done
    echo "  - console: viewmodel tier auto"
  done
} > "$tour"
arms=""
[ -n "$ARMS" ] && arms="--set debug.view_model_path=$ARMS"
# shellcheck disable=SC2086
SDL_AUDIODRIVER=dummy ./tools/run_game.sh --isolated "pole_${TAG}_$PLACE" --world mm6 $where \
  --ruleset maw:solo --set video.resolution=1600x900 --set video.window_mode=windowed --set debug.console=true \
  --set gameplay.enemy_health_bars=off --set debug.menu_input_tour_path="$tour" $arms $SETS --seconds 240 \
  > "$P/ingame/$TAG/run_$PLACE.log" 2>&1
echo "$PLACE exit $? $(find "$P/ingame/$TAG" -name '*.png' -path "*_$PLACE/*" | wc -l) png"
