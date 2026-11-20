#!/usr/bin/env bash
# Reduced runtime GLB from the picked ladder step (f, Cand_62): kept normals -> export_cand -> swap_lod0 (onto the
# batch I export: materials, variants, region mask, clips, Socket_Arrow_Release byte for byte) -> floor points ->
# LODs (protected extremes and Death/Dead floor contacts) -> shadow LODs tucked inside (the batch I project's own
# step) -> colour variants carried to every LOD/shadow primitive. Bow and arrow attachments are byte-identical copies.
# Usage: TOKEN=<lease> scripts/build_reduced.sh [out.glb]
set -euo pipefail
cd "$(dirname "$0")/.."; out=${1:-export/mm7_m282.glb}; ROOT=$(cd ../../.. && pwd)
B() { local o log; o=$("$ROOT/tools/run_creature_blender.sh" --token "$TOKEN" "level_generation/creatures/mm7_m282_reduce_claude/scripts/$@" 2>&1)
      log=$(echo "$o" | grep -o '/tmp/openyamm-creature-blender-[A-Za-z0-9]*\.log' | head -1)
      grep -E "EXPORTED|KEPTNORMALS|FLOOR|PROTECTED|LOD triangles|Traceback|Error:" "$log" || true; }
REA_KEPT_NORMALS=1 scripts/cand_glb.sh f Cand_62 kn
cp work/glb_f_62kn.glb work/pick_lod0.glb
REA_NODE=M282 REA_FLOOR_N=${REA_FLOOR_N:-40} B floor_points.py "$PWD/work/pick_lod0.glb"
B build_lods.py "$PWD/work/pick_lod0.glb" "$PWD/work/pick_lods.glb"
python3 scripts/shrink_shadow_lods.py work/pick_lods.glb work/pick_lods_shadowfix.glb
cp work/pick_lods_shadowfix.glb "$out"; python3 scripts/carry_variants.py "$out"
cmp -s export/mm7_m282_bow.glb ../mm7_m282_claude/export/mm7_m282_bow.glb || cp ../mm7_m282_claude/export/mm7_m282_bow.glb export/
cmp -s export/mm7_m282_arrow.glb ../mm7_m282_claude/export/mm7_m282_arrow.glb || cp ../mm7_m282_claude/export/mm7_m282_arrow.glb export/
ls -la "$out" export/mm7_m282_bow.glb export/mm7_m282_arrow.glb
