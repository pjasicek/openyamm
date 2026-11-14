#!/bin/sh
# In-game captures of one new template (README.md "In-game checks"), 1600x900, MAW solo run, MM6 New Sorpigal at
# 9 am or Corlagon's dungeon (6d05). Usage: scripts/run_ingame.sh <kind> <outdoor|indoor> [tag] [tiers "1 2 3 4"]
# Per tier and for our ground model (`viewmodel weapons ours` + `viewmodel held <icon>`): idle and two moments of the
# kind's attack. Writes ingame/<tag>/<kind>_<place>/<t1..t4|ours>_<idle|swing|swing2>.png.
cd "$(dirname "$0")/../../../../.." || exit 1
P=$PWD/level_generation/props/items_claude/view_model_weapons_20261114
KIND=$1; PLACE=$2; TAG=${3:-v1}; TIERS=${4:-"1 2 3 4"}
FILE=w_$KIND.glb
case $KIND in
  spear) SET=twohand; OURS=item042; A="twohandattackright 0.4"; B="twohandattackright 0.3" ;;
  trident) SET=twohand; OURS=trident1; A="twohandattackright 0.4"; B="twohandattackright 0.3" ;;
  halberd) SET=twohand; OURS=halberd1; A="twohandattackright 0.4"; B="twohandattackright 0.3" ;;
  wand) SET=onehand; OURS=wand1; A="onehandblockidle 0.5"; B="onehandattackright 0.30" ;;
  blaster) SET=onehand; OURS=raygun1; A="onehandblockidle 0.5"; B="onehandattackright 0.30" ;;
  # The crossbow's own set (crossbow_set_20261114): the recoil frame and mid-span.
  crossbow) SET=crossbow; OURS=crsbow1; A="crossbowattack 0.46"; B="crossbowattack 0.95" ;;
  # Held like the mace: the right-hand swing's backswing and blow show the head (oblivion_weapon_skins_20261114).
  club) SET=onehand; OURS=club1; A="onehandattackright 0.25"; B="onehandattackright 0.4" ;;
  *) echo "unknown kind $KIND"; exit 1 ;;
esac
[ -n "$SETOVERRIDE" ] && SET=$SETOVERRIDE
out=$P/ingame/$TAG/${KIND}_$PLACE
mkdir -p "$out"
tour=$out/tour.yml
{
  echo "output_dir: $out"
  echo "exit: true"
  echo "steps:"
  echo "  - wait: 3"
  echo "  - console: viewmodel kit $SET $FILE 0"
  echo "  - wait: 2"
  for t in $TIERS; do
    echo "  - console: viewmodel tier $t"
    echo "  - wait: 1.2"
    echo "  - capture: t${t}_idle"
    echo "  - console: viewmodel pose $A"
    echo "  - wait: 0.5"
    echo "  - capture: t${t}_swing"
    echo "  - console: viewmodel pose $B"
    echo "  - wait: 0.5"
    echo "  - capture: t${t}_swing2"
    echo "  - console: viewmodel pose off"
  done
  if [ -z "$NOOURS" ]; then
    echo "  - console: viewmodel tier auto"
    echo "  - console: viewmodel weapons ours"
    echo "  - console: viewmodel held $OURS"
    echo "  - wait: 2"
    echo "  - capture: ours_idle"
    echo "  - console: viewmodel pose $A"
    echo "  - wait: 0.5"
    echo "  - capture: ours_swing"
    echo "  - console: viewmodel pose $B"
    echo "  - wait: 0.5"
    echo "  - capture: ours_swing2"
  fi
} > "$tour"
case $PLACE in
  outdoor) where="--map oute3.odm" ;;
  indoor) where="--map 6d05.blv" ;;
esac
# shellcheck disable=SC2086
SDL_AUDIODRIVER=dummy ./tools/run_game.sh --isolated "vmw_${TAG}_${KIND}_$PLACE" --world mm6 $where \
  --ruleset maw:solo --set video.resolution=1600x900 --set video.window_mode=windowed --set debug.console=true \
  --set gameplay.enemy_health_bars=off --set debug.menu_input_tour_path="$tour" --seconds 200 \
  > "$out/run.log" 2>&1
echo "$KIND $PLACE exit $? $(ls "$out" | grep -c png) png"
