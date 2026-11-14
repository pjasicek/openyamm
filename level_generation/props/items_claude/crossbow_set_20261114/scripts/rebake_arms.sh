#!/bin/sh
# Rebakes every race's first-person arms from the pristine pre-dual copies (README.md "Baked clips"): the dual-wield
# clips (dual_wield_20261114/scripts/bake_dual_clips.py) and the crossbow set into scratch files, then the pole set
# (pole_set_20261114/scripts/bake_pole_clips.py) into the arms in place ('wb' truncates the file, so its hard links
# stay one file: assets_dev/engine/view_model/arms.glb is reference/oblivion_poc/glb/arms_hd_human.glb). Idempotent:
# run it again after changing any of the three bakes.
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
done
