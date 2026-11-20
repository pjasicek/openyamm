#!/usr/bin/env bash
# Candidate runtime GLB from a pose-aware step: swap the LOD0 index buffers into the Banshee's own pre-mirror runtime LOD0,
# then the Banshee's runtime tail exactly as build_runtime.sh runs it (LODs, shadow shrink, tiers, eye glow, floor, mirror,
# lining + blend order), then splice.py puts the new meshes into the installed GLB so everything but geometry stays byte
# for byte. Usage (from anywhere): build_cand.sh <tag, e.g. r55>  -> export/mm9_banshee_<tag>.glb
set -euo pipefail
tag=$1
P="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$P/../../.." && pwd)"
B="$repo/level_generation/creatures/mm9_banshee_claude"
V="$repo/level_generation/creatures/claude_shared/gltf_venv/bin/python"
E="$P/work/build_$tag"; mkdir -p "$E"
cd "$P"
python3 scripts/swap_mp.py "$B/export/mm9_banshee_runtime_lod0.glb" work/mp_$tag.npz "$E/runtime_lod0.glb"
(cd scripts && python3 lod_ratios.py "$E/runtime_lod0.glb" "$repo/assets_source/worlds/mm9/models/mm9_banshee.glb" "$E/lod_ratios.json")
scripts/cap.sh /snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python scripts/build_lods.py -- "$E/runtime_lod0.glb" "$E/lods.glb" "$E/lod_ratios.json" 2>&1 | grep -E "LOD triangles|PROTECTED|Error|moved"
cd "$B"
"$V" -W ignore scripts/shrink_shadow_lods.py "$E/lods.glb" "$E/lods_shadowfix.glb" Banshee | tail -1
"$V" -W ignore scripts/banshee_variants.py "$E/lods_shadowfix.glb" "$E/skins.glb" | tail -1
"$V" -W ignore ../claude_shared/emission.py "$E/skins.glb" "$E/glow.glb" --material BansheeHead --mask textures/banshee_eye_mask.png \
  --color banshee_a=0,0,0 --color banshee_b=0.9,0.28,0.08 --color banshee_c=0.15,1.0,0.3 --strength 1.3 --pulse 0.12,2.3 | tail -1 | cut -c1-160
"$V" -W ignore ../claude_shared/floor/floor_fix.py "$E/glow.glb" "$E/floored.glb" $(set -f; cat scripts/floor_ops.txt) | tail -4 | cut -c1-200
"$V" -W ignore scripts/mirror_glb.py "$E/floored.glb" "$E/mirrored.glb"
"$V" -W ignore scripts/finish_blend.py "$E/mirrored.glb" "$E/finished.glb" | tail -5 | cut -c1-160
cd "$P"
python3 scripts/splice.py "$repo/assets_source/worlds/mm9/models/mm9_banshee.glb" "$E/finished.glb" export/mm9_banshee_$tag.glb
python3 "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/mm9_banshee_$tag.glb | tail -1
ls -la export/mm9_banshee_$tag.glb
