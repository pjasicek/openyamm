#!/usr/bin/env bash
# work/half$SUF.glb (scripts/rig.sh) -> runtime GLB: prepare -> LODs -> shadow fix -> ramps -> tier head images -> winding -> floor -> mirror -> install.
# Project folder: scripts/build_runtime.sh human|elf [--install]
#   human: export/mm9_peasantgirl.glb (no elf ears; variants pg_g2 = MM9 PeasantGirl2, pg_g3 = PeasantGirl3), from work/half_h.glb
#   elf:   export/mm9_peasantgirl1e.glb (elf ears; variant pg_g1e = MM9 PeasantGirl1e), from work/half_e.glb
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"; cd "$here"
G="$repo/level_generation/creatures/claude_shared/gltf_venv/bin/python"; L=../claude_shared; export PYTHONPATH=/usr/lib/python3/dist-packages
if [[ "$1" == human ]]; then n=mm9_peasantgirl; S=_h; V="pg_g2 pg_g3"; else n=mm9_peasantgirl1e; S=_e; V="pg_g1e"; fi
mkdir -p export
"$G" -W ignore scripts/split_ramps.py textures/pg_ramps.json textures/pg_ramps$S.json $V | tail -1
"$G" -W ignore "$repo/tools/prepare_actor_glb.py" work/half$S.glb export/${n}_runtime_lod0.glb 2>&1 | tail -1
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/${n}_runtime_lod0.glb" "$here/export/${n}_lods.glb" --mesh-node PeasantGirl --max-influences 4 2>&1 | grep -E "LOD triangles|Error"
"$G" -W ignore ../mm9_skeletonwarrior_claude/scripts/shrink_shadow_lods.py export/${n}_lods.glb export/${n}_lods_shadowfix.glb PeasantGirl 2>&1 | tail -1
"$G" -W ignore $L/region_variants.py export/${n}_lods_shadowfix.glb work/${n}_rv.glb textures/pg_ramps$S.json --extra PeasantGirl openyamm_specular=0 --extra PeasantGirl pbr.metallicFactor=0 2>&1 | tail -1
"$G" -W ignore scripts/tier_images_pg.py work/${n}_rv.glb export/${n}_skins.glb textures/tier_images$( [[ $1 == elf ]] && echo _elf ).json 2>&1 | tail -1
"$G" -W ignore scripts/fix_winding.py export/${n}_skins.glb export/${n}_skins2.glb 2>&1 | tail -1
"$G" -W ignore $L/floor/floor_fix.py export/${n}_skins2.glb export/${n}_lift.glb $(cat scripts/floor_lift.txt) 2>&1 | tail -1
"$G" -W ignore $L/floor/floor_fix.py export/${n}_lift.glb export/${n}_floor.glb $(cat scripts/floor_ops.txt) --ground-death Death Dead 2>&1 | tail -2
"$G" -W ignore ../mm9_lich_claude/scripts/mirror_glb.py export/${n}_floor.glb export/${n}.glb 2>&1 | tail -1
"$G" -W ignore "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/${n}.glb | tail -1
if [[ "${2:-}" == "--install" ]]; then python3 "$repo/tools/install_model.py" export/${n}.glb --world mm9 2>&1 | tail -2; fi
ls -la export/${n}.glb
