#!/bin/sh
# Rebakes every race's first-person arms from the pristine pre-dual copies (README.md "Baked clips"): the dual-wield
# clips (dual_wield_20261114/scripts/bake_dual_clips.py) and the crossbow set into scratch files, then the pole set
# (pole_set_20261114/scripts/bake_pole_clips.py) into reference/oblivion_poc/glb/arms_hd_<race>.glb, and installs the
# human arms as the engine's (tools/install_model.py --view-model: the source into assets_source/engine/view_model/,
# the cooked arms.glb and its text keys into assets_dev/engine/view_model/). Idempotent: run it again after changing any
# of the three bakes.
# Usage: scripts/rebake_arms.sh [race ...]   (default: all ten)
cd "$(dirname "$0")/../../../../.." || exit 1
P=reference/oblivion_poc/glb/pristine_predual
G=reference/oblivion_poc/glb
DUAL=level_generation/props/items_claude/dual_wield_20261114/scripts/bake_dual_clips.py
XBOW=level_generation/props/items_claude/crossbow_set_20261114/scripts/bake_crossbow_clips.py
POLE=level_generation/props/items_claude/pole_set_20261114/scripts/bake_pole_clips.py
TMP=$(mktemp -d) || exit 1
trap 'rm -rf "$TMP"' EXIT
RACES=${*:-"human darkelf dwarf elf goblin minotaur troll undead vampire zombie"}
for r in $RACES; do
  python3 $DUAL $P/arms_hd_$r.glb $P/arms_hd_$r.textkeys.json "$TMP/dual.glb" "$TMP/dual.textkeys.json" > /dev/null \
    || { echo "dual bake failed for $r"; exit 1; }
  python3 $XBOW "$TMP/dual.glb" "$TMP/dual.textkeys.json" "$TMP/xbow.glb" "$TMP/xbow.textkeys.json" \
    > "$TMP/$r.xbow.log" || { cat "$TMP/$r.xbow.log"; echo "crossbow bake failed for $r"; exit 1; }
  python3 $POLE "$TMP/xbow.glb" "$TMP/xbow.textkeys.json" $G/arms_hd_$r.glb $G/arms_hd_$r.textkeys.json \
    > "$TMP/$r.pole.log" || { cat "$TMP/$r.pole.log"; echo "pole bake failed for $r"; exit 1; }
  echo "$r: $(tail -1 "$TMP/$r.xbow.log" | sed 's/ and .*//'); pole: $(tail -1 "$TMP/$r.pole.log")"
  if [ "$r" = human ]; then
    python3 tools/install_model.py $G/arms_hd_human.glb --view-model --name arms.glb || { echo "install failed"; exit 1; }
    cp $G/arms_hd_human.textkeys.json assets_dev/engine/view_model/arms.textkeys.json
  fi
done
