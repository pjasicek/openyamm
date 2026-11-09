#!/usr/bin/env bash
# Candidate runtime GLB from a pose-aware step (Ghost; adapted from mm9_banshee_reduce_claude): swap the LOD0 index buffers
# into the Ghost's own pre-mirror runtime LOD0, then the Ghost's runtime tail exactly as its build_runtime.sh runs it (LODs,
# shadow shrink, tiers, eye glow, floor, mirror, robe lining + blend order), then splice.py puts the new meshes into the
# installed GLB so everything but geometry stays byte for byte.
# Usage: build_cand.sh <tag> [plain]   (work/mp_<tag>.npz -> export/mm9_ghost_<tag>.glb; "plain" = tools/build_actor_lods.py
# with its defaults as the Ghost was built, else scripts/build_lods.py with per-material ratios and protected points)
set -euo pipefail
tag=$1; mode=${2:-ratios}
P="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$P/../../.." && pwd)"
B="$repo/level_generation/creatures/mm9_ghost_claude"
V="$repo/level_generation/creatures/claude_shared/gltf_venv/bin/python"
E="$P/work/build_$tag"; mkdir -p "$E"
cd "$P"
if [[ "$tag" == r100 ]]; then cp "$B/export/mm9_ghost_runtime_lod0.glb" "$E/runtime_lod0.glb"
else python3 scripts/swap_mp.py "$B/export/mm9_ghost_runtime_lod0.glb" work/mp_$tag.npz "$E/runtime_lod0.glb"; fi
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1"
if [[ "$mode" == plain ]]; then
  $BL --python "$repo/tools/build_actor_lods.py" -- "$E/runtime_lod0.glb" "$E/lods.glb" --mesh-node Ghost --max-influences 4 2>&1 | grep -E "LOD triangles|Error"
else
  (cd scripts && python3 lod_ratios.py "$E/runtime_lod0.glb" "$B/export/mm9_ghost_lods.glb" "$E/lod_ratios.json")
  $BL --python scripts/build_lods.py -- "$E/runtime_lod0.glb" "$E/lods.glb" "$E/lod_ratios.json" 2>&1 | grep -E "LOD triangles|PROTECTED|Error"
fi
cd "$B"
"$V" -W ignore scripts/shrink_shadow_lods.py "$E/lods.glb" "$E/lods_shadowfix.glb" Ghost | tail -1
"$V" -W ignore scripts/ghost_variants.py "$E/lods_shadowfix.glb" "$E/skins.glb" | tail -1
"$V" -W ignore ../claude_shared/emission.py "$E/skins.glb" "$E/glow.glb" --material GhostHead --mask textures/ghost_eye_mask.png \
  --color ghost_a=0,0,0 --color ghost_b=0.2,1.0,0.3 --color ghost_c=0.2,0.55,1.0 --strength 1.2 --pulse 0.12,2.3 | tail -1 | cut -c1-160
"$V" -W ignore ../claude_shared/floor/floor_fix.py "$E/glow.glb" "$E/floored.glb" $(set -f; cat scripts/floor_ops.txt) | tail -4 | cut -c1-200
"$V" -W ignore scripts/mirror_glb.py "$E/floored.glb" "$E/mirrored.glb"
"$V" -W ignore scripts/finish_blend.py "$E/mirrored.glb" "$E/finished.glb" | tail -5 | cut -c1-160
cd "$P"
python3 scripts/splice.py "$repo/assets_source/worlds/mm9/models/mm9_ghost.glb" "$E/finished.glb" export/mm9_ghost_$tag.glb
python3 "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/mm9_ghost_$tag.glb | tail -1
ls -la export/mm9_ghost_$tag.glb
