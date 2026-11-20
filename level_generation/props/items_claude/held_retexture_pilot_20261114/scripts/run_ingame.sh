#!/bin/sh
# In-game captures of the four pilot swords (README.md, "In-game checks"), one game at a time, 1600x900.
# Usage: scripts/run_ingame.sh <phase: before|after> [outdoor|indoor|ground ...]
# Writes ingame/<phase>/<place>/NN_<name>.png.
cd "$(dirname "$0")/../../../../.." || exit 1
P=$PWD/level_generation/props/items_claude/held_retexture_pilot_20261114
PHASE=$1; shift
PLACES=${*:-outdoor indoor ground}
ICONS="item001 7item010 item005 7item012"
IDS="1 812 5 814"
for place in $PLACES; do
  out=$P/ingame/$PHASE/$place
  mkdir -p "$out"
  tour=$P/ingame/tours/${PHASE}_$place.yml
  {
    echo "output_dir: $out"
    echo "exit: true"
    echo "steps:"
    echo "  - wait: 3"
    echo "  - console: loc"
    if [ "$place" = ground ]; then
      x=-9930
      for id in $IDS; do echo "  - console: item drop $id $x -11200 200"; echo "  - wait: 2"; x=$((x + 70)); done
      echo "  - wait: 1"
      echo "  - capture: 00_ground"
    else
      n=1
      for icon in $ICONS; do
        echo "  - console: viewmodel held $icon"
        echo "  - wait: 1.2"
        echo "  - capture: ${n}0_${icon}_idle"
        echo "  - console: viewmodel pose onehandattackleft 0.15"
        echo "  - wait: 0.4"
        echo "  - capture: ${n}1_${icon}_swing"
        echo "  - console: viewmodel pose onehandattackright 0.30"
        echo "  - wait: 0.4"
        echo "  - capture: ${n}2_${icon}_swing2"
        echo "  - console: viewmodel pose off"
        n=$((n + 1))
      done
    fi
  } > "$tour"
  case $place in
    outdoor) where="--map oute3.odm" ;;
    indoor) where="--map 6d05.blv" ;;
    ground) where="--map oute3.odm --position -9728 -11319 161 --yaw-radians 1.5708 --pitch-degrees -45" ;;
  esac
  # shellcheck disable=SC2086
  SDL_AUDIODRIVER=dummy ./tools/run_game.sh --isolated "heldtex_${PHASE}_$place" --world mm6 $where \
    --ruleset maw:solo --set video.resolution=1600x900 --set video.window_mode=windowed --set debug.console=true \
    --set gameplay.enemy_health_bars=off --set debug.menu_input_tour_path="$tour" --seconds 150 \
    > "$out/run.log" 2>&1
  echo "$place exit $?"
done
