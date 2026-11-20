#!/bin/sh
# In-game captures of one template's skins (README.md, "In-game checks"), 1600x900, MAW solo run.
# Usage: scripts/run_ingame.sh <template> <outdoor|indoor> [tag] [tiers, default "0 1 2 3 4"]
# Per tier (0: the plain template) and our ground model: idle and two moments of a swing (the bow: drawing and at full
# draw; the shield, held alone: raised block and a blocked hit). Writes ingame/<tag>/<template>_<place>/<tier>_<pose>.png
# (tier t0..t4 or ours, pose idle|swing|swing2); scripts/to_viewer.py turns them into the review JPEGs.
cd "$(dirname "$0")/../../../../.." || exit 1
P=$PWD/level_generation/props/items_claude/oblivion_weapon_skins_20261114
NAME=$1; PLACE=$2; TAG=${3:-v1}; TIERS=${4:-"0 1 2 3 4"}
FILE=$NAME.glb; SHIELD=0
case $NAME in
  w_longsword) SET=onehand; OURS=item001; A="onehandattackleft 0.15"; B="onehandattackright 0.30" ;;
  w_shortsword) SET=onehand; OURS=item011; A="onehandattackleft 0.15"; B="onehandattackright 0.30" ;;
  w_dagger) SET=onehand; OURS=item021; A="onehandattackleft 0.15"; B="onehandattackright 0.30" ;;
  # Heads (maces, axes, hammers) show in the right-hand swing's backswing and blow (ingame/posetest, 2026-11-14).
  w_mace) SET=onehand; OURS=item066; A="onehandattackright 0.25"; B="onehandattackright 0.4" ;;
  w_waraxe) SET=onehand; OURS=item031; A="onehandattackright 0.25"; B="onehandattackright 0.4" ;;
  w_claymore) SET=twohand; OURS=item006; A="twohandattackleft 0.15"; B="twohandattackright 0.30" ;;
  w_battleaxe) SET=twohand; OURS=item036; A="twohandattackleft 0.25"; B="twohandattackright 0.3" ;;
  w_warhammer) SET=twohand; OURS=item073; A="twohandattackleft 0.25"; B="twohandattackright 0.3" ;;
  # The game holds the staff as w_staff_grip (the same mesh and paint, gripped near its butt).
  w_staff) SET=twohand; FILE=w_staff_grip.glb; OURS=item079; A="twohandattackleft 0.15"; B="twohandattackright 0.30" ;;
  w_bow) SET=bow; OURS=item056; A="bowattack 0.9"; B="bowattack 1.37" ;;
  s_steelshield) SET=onehand; FILE=none; SHIELD=1; OURS=item099; A="blockidle 0.5"; B="blockhit 0.15" ;;
  *) echo "unknown template $NAME"; exit 1 ;;
esac
out=$P/ingame/$TAG/${NAME}_$PLACE
mkdir -p "$out"
tour=$out/tour.yml
{
  echo "output_dir: $out"
  echo "exit: true"
  echo "steps:"
  echo "  - wait: 3"
  echo "  - console: viewmodel kit $SET $FILE $SHIELD"
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
} > "$tour"
case $PLACE in
  outdoor) where="--map oute3.odm" ;;
  indoor) where="--map 6d05.blv" ;;
esac
# shellcheck disable=SC2086
SDL_AUDIODRIVER=dummy ./tools/run_game.sh --isolated "oblskin_${TAG}_${NAME}_$PLACE" --world mm6 $where \
  --ruleset maw:solo --set video.resolution=1600x900 --set video.window_mode=windowed --set debug.console=true \
  --set gameplay.enemy_health_bars=off --set debug.menu_input_tour_path="$tour" --seconds 200 \
  > "$out/run.log" 2>&1
echo "$NAME $PLACE exit $? $(ls "$out" | grep -c png) png"
