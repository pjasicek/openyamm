#!/usr/bin/env bash
# Full export chain from work/i85_lod0.glb: LODs (horn curve and floor-contact points protected), LOD1 UV clamp,
# compaction, variants on every LOD/shadow primitive, then the source-animation fixes (smooth_walk_bob.py sigma 5 on
# the 120 Hz Walking keys, fix_clips.py) and the winding check. Rerun after any re-export of the creature.
set -euo pipefail; cd "$(dirname "$0")/.."
blender -b -P scripts/build_lods.py -- "$PWD/work/i85_lod0.glb" "$PWD/work/lods_r85.glb" 2>&1 | grep "LOD tri"
rm -f work/lods.json work/lods_r85.geometry.glb
python3 scripts/clamp_lod_uv.py work/lods_r85.glb; python3 scripts/compact_glb.py work/lods_r85.glb
python3 scripts/carry_variants.py work/lods_r85.glb
cp work/lods_r85.glb work/mm8_m632_r85_pre_clipfix.glb
python3 scripts/smooth_walk_bob.py work/mm8_m632_r85_pre_clipfix.glb work/walk_s5.glb 5 | grep -E "PELVIS|LEG"
python3 scripts/fix_clips.py work/walk_s5.glb export/mm8_m632.glb
python3 scripts/compact_glb.py export/mm8_m632.glb
python3 ../../decorations/mm8_3d/animated/scripts/check_winding.py export/mm8_m632.glb | tail -1
