#!/usr/bin/env bash
# work/clips.glb (scripts/rig_sk.sh) -> runtime GLB: prepare -> LODs -> shadow fix -> material extras (specular 0, metallic 0) -> winding ->
# robe strips lifted off the floor in the fall -> floor -> eye emission -> mirror (true handedness) -> winding check -> install.
# Project folder: scripts/build_runtime_sk.sh [--install]   (after Igrid's build_runtime_wo.sh, without its legs_hide: Skraelos has no legs)
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"; cd "$here"
n=mm9_skraelos; G="$repo/level_generation/creatures/claude_shared/gltf_venv/bin/python"; L=../claude_shared; export PYTHONPATH=/usr/lib/python3/dist-packages
mkdir -p export
"$G" -W ignore "$repo/tools/prepare_actor_glb.py" ${CLIPS:-work/clips_arm.glb} export/${n}_runtime_lod0.glb 2>&1 | tail -1
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/${n}_runtime_lod0.glb" "$here/export/${n}_lods.glb" --mesh-node Skraelos --max-influences 4 2>&1 | grep -E "LOD triangles|Error"
"$G" -W ignore ../mm9_skeletonwarrior_claude/scripts/shrink_shadow_lods.py export/${n}_lods.glb export/${n}_lods_shadowfix.glb Skraelos 2>&1 | tail -1
python3 ../mm9_yrsa_claude/v2/scripts/set_material_extras.py export/${n}_lods_shadowfix.glb work/${n}_extras.glb openyamm_specular=0 pbr.metallicFactor=0 2>&1 | tail -1
"$G" -W ignore scripts/fix_winding.py work/${n}_extras.glb export/${n}_skins1.glb 2>&1 | tail -1
"$G" -W ignore scripts/double_body.py export/${n}_skins1.glb export/${n}_skins2.glb 2>&1 | tail -1
"$G" -W ignore $L/floor/floor_fix.py export/${n}_skins2.glb export/${n}_lift.glb --lift-joints Death Dead --lift-only 'x*' --tolerance 0.10 2>&1 | tail -1
"$G" -W ignore $L/floor/floor_fix.py export/${n}_lift.glb export/${n}_floor.glb $(cat scripts/floor_ops.txt) --ground-death Death Dead 2>&1 | tail -2
# second pass: the staff tip reached 5.4 cm under the floor mid-fall (1.33 s) after the corpse grounding; raise those keys, smoothed
"$G" -W ignore $L/floor/floor_fix.py export/${n}_floor.glb export/${n}_floor2.glb --raise Death --smooth Death 0.05 2>&1 | tail -1
"$G" -W ignore $L/emission.py export/${n}_floor2.glb export/${n}_glow.glb --material SkraelosHead --mask textures/sk_head_glow.png --color 1.0,0.16,0.03 --strength 1.4 --pulse 0.15,2.5 2>&1 | tail -1
"$G" -W ignore ../mm9_lich_claude/scripts/mirror_glb.py export/${n}_glow.glb export/${n}.glb 2>&1 | tail -1
"$G" -W ignore "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/${n}.glb | tail -1
if [[ "${1:-}" == "--install" ]]; then python3 "$repo/tools/install_model.py" export/${n}.glb --world mm9 2>&1 | tail -2; fi
ls -la export/${n}.glb
