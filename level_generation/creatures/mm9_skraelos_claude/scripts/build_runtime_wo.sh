#!/usr/bin/env bash
# work/half.glb (scripts/rig_wo.sh) -> runtime GLB: prepare -> LODs -> shadow fix -> material extras (specular 0, metallic 0) -> winding ->
# floor (Yrsa's ops: wyrd_old's clips are Yrsa's) -> mirror (true handedness) -> install. Project folder: scripts/build_runtime_wo.sh [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"; cd "$here"
n=mm9_wyrdold; G="$repo/level_generation/creatures/claude_shared/gltf_venv/bin/python"; L=../claude_shared; export PYTHONPATH=/usr/lib/python3/dist-packages
mkdir -p export
"$G" -W ignore "$repo/tools/prepare_actor_glb.py" ${HALF:-work/half.glb} export/${n}_runtime_lod0.glb 2>&1 | tail -1
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/${n}_runtime_lod0.glb" "$here/export/${n}_lods.glb" --mesh-node Igrid --max-influences 4 2>&1 | grep -E "LOD triangles|Error"
"$G" -W ignore ../mm9_skeletonwarrior_claude/scripts/shrink_shadow_lods.py export/${n}_lods.glb export/${n}_lods_shadowfix.glb Igrid 2>&1 | tail -1
python3 ../mm9_yrsa_claude/v2/scripts/set_material_extras.py export/${n}_lods_shadowfix.glb work/${n}_extras.glb openyamm_specular=0 pbr.metallicFactor=0 2>&1 | tail -1
"$G" -W ignore scripts/fix_winding.py work/${n}_extras.glb export/${n}_skins2.glb 2>&1 | tail -1
# (r12: --smooth Death 0.07 -> 0.035 in floor_ops.txt: with the legs pulled in, the wider smoothing let the fall dip 2.8 cm under the floor)
# the robe chains bend up in the fall and corpse only to within 10 cm of the floor (full bends put the shoes through the robe), then the body is grounded
# the lower legs shrink into the robe once she falls and their Calf joints move 80 % toward the Pelvis (legs_hide.py: MM9 has no legs under
# its robe; review r9 robe gate Death/Dead 7.8 cm; shrinking alone left Death 6.0 cm at 0.3-0.46 s)
"$G" -W ignore scripts/legs_hide.py export/${n}_skins2.glb export/${n}_legs.glb Death:0.05:0.3:0.05:0.8 Dead:0:0:0.05:0.8 2>&1 | tail -1
"$G" -W ignore $L/floor/floor_fix.py export/${n}_legs.glb export/${n}_lift.glb $(cat scripts/floor_lift.txt) 2>&1 | tail -1
"$G" -W ignore $L/floor/floor_fix.py export/${n}_lift.glb export/${n}_floor1.glb $(cat scripts/floor_ops.txt) --ground-death Death Dead 2>&1 | tail -2
"$G" -W ignore $L/floor/floor_fix.py export/${n}_floor1.glb export/${n}_floor.glb $(cat scripts/floor_ops_hit.txt) 2>&1 | tail -1
"$G" -W ignore ../mm9_lich_claude/scripts/mirror_glb.py export/${n}_floor.glb export/${n}.glb 2>&1 | tail -1
"$G" -W ignore "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/${n}.glb | tail -1
if [[ "${1:-}" == "--install" ]]; then python3 "$repo/tools/install_model.py" export/${n}.glb --world mm9 2>&1 | tail -2; fi
ls -la export/${n}.glb
