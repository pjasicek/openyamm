#!/bin/sh
# In-game captures of the crossbow set (README.md "In-game checks"), 1600x900, MAW solo run. The new knight's hands are
# emptied and a crossbow put in the bow slot with `viewmodel equip 0 0 <id>` (the real kit path: nothing in the main
# hand draws the bow slot, and its held.yml kind picks the crossbow set). Per tier (`viewmodel tier`): the idle, then
# held poses of crossbowattack: mid-raise, the aim just before the release, the recoil frame and mid-reload; then our
# ground model (`viewmodel weapons ours`) at idle and in the recoil.
# Usage: scripts/run_ingame.sh <outdoor|indoor> [tag] [tiers "1 2 3 4"]
# ARMS=<absolute arms.glb>: hold arms from disk ([debug] view_model_path, its weapons beside it) instead of the
# engine's. EXTRA="clip@seconds ...": more held poses. LIVE=1: instead of held poses, `viewmodel trace on` and Attack
# pressed four times (the real shot path: the clip fitted to the recovery, the bolt loosed at Release), captures 0.2,
# 0.55 and 1.2 s after each press; SETS="--set debug.time_scale=0.25" slows it to catch the raise, recoil and span.
# Writes ingame/<tag>/<place>/<t1..t4|ours|live>_<pose>.png.
cd "$(dirname "$0")/../../../../.." || exit 1
P=$PWD/level_generation/props/items_claude/crossbow_set_20261114
PLACE=$1; TAG=${2:-v1}; TIERS=${3:-"1 2 3 4"}
# Hunting Crossbow (MM6 item063): a crossbow of the crossbow kind in held.yml.
CROSSBOW=${CROSSBOW:-63}
POSES=${POSES:-"raise@crossbowattack@0.15 aim@crossbowattack@0.38 swing@crossbowattack@0.46 reload@crossbowattack@0.95"}
out=$P/ingame/$TAG/$PLACE
mkdir -p "$out"
tour=$out/tour.yml
{
  echo "output_dir: $out"
  echo "exit: true"
  echo "steps:"
  echo "  - wait: 3"
  echo "  - console: viewmodel equip 0 0 $CROSSBOW"
  echo "  - wait: 2"
  if [ -n "$LIVE" ]; then
    echo "  - console: viewmodel trace on"
    for shot in 1 2 3 4; do
      echo "  - action: attack"
      echo "  - wait: 0.2"
      echo "  - capture: live${shot}_a"
      echo "  - wait: 0.35"
      echo "  - capture: live${shot}_b"
      echo "  - wait: 0.65"
      echo "  - capture: live${shot}_c"
      echo "  - wait: 1.0"
    done
    TIERS=""; NOOURS=1
  fi
  for t in $TIERS; do
    echo "  - console: viewmodel tier $t"
    echo "  - wait: 2"
    echo "  - capture: t${t}_idle"
    for pose in $POSES; do
      name=${pose%%@*}; rest=${pose#*@}; clip=${rest%@*}; seconds=${rest#*@}
      echo "  - console: viewmodel pose $clip $seconds"
      echo "  - wait: 0.6"
      echo "  - capture: t${t}_$name"
    done
    for extra in $EXTRA; do
      clip=${extra%@*}; seconds=${extra#*@}
      echo "  - console: viewmodel pose $clip $seconds"
      echo "  - wait: 0.6"
      echo "  - capture: t${t}_${clip}_$seconds"
    done
    echo "  - console: viewmodel pose off"
  done
  if [ -z "$NOOURS" ]; then
    echo "  - console: viewmodel tier auto"
    echo "  - console: viewmodel weapons ours"
    echo "  - wait: 2"
    echo "  - capture: ours_idle"
    echo "  - console: viewmodel pose crossbowattack 0.46"
    echo "  - wait: 0.6"
    echo "  - capture: ours_swing"
    echo "  - console: viewmodel pose crossbowattack 0.95"
    echo "  - wait: 0.6"
    echo "  - capture: ours_reload"
  fi
} > "$tour"
case $PLACE in
  outdoor) where="--map oute3.odm" ;;
  indoor) where="--map 6d05.blv --position 1664 -1920 0 --yaw-radians 3.1416 --pitch-degrees 0" ;;  # into the cave
  *) echo "unknown place $PLACE"; exit 2 ;;
esac
arms=""
[ -n "$ARMS" ] && arms="--set debug.view_model_path=$ARMS"
# shellcheck disable=SC2086
SDL_AUDIODRIVER=dummy ./tools/run_game.sh --isolated "xbow_${TAG}_$PLACE" --world mm6 $where \
  --ruleset maw:solo --set video.resolution=1600x900 --set video.window_mode=windowed --set debug.console=true \
  --set gameplay.enemy_health_bars=off --set debug.menu_input_tour_path="$tour" $arms $SETS --seconds 150 \
  > "$out/run.log" 2>&1
echo "$PLACE exit $? $(ls "$out" | grep -c png) png"
