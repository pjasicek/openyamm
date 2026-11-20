#!/usr/bin/env bash
# Runtime GLB: rig fix -> textured export -> MM9 clips -> hand rest -> prepare -> LODs -> shadow fix -> tiers -> eye glow ->
# floor -> winding [-> install --world mm9]. Usage (repo root): TOKEN=<lease> level_generation/creatures/mm9_lich_claude/scripts/build_runtime.sh [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
V="$repo/level_generation/creatures/claude_shared/gltf_venv/bin/python"
: "${TOKEN:?set TOKEN}"
rel=level_generation/creatures/mm9_lich_claude
cd "$repo"
B() { local out log; out=$(tools/run_creature_blender.sh --token "$TOKEN" "$@" 2>&1) || true
      log=$(echo "$out" | grep -o '/tmp/openyamm-creature-blender-[A-Za-z0-9]*\.log' | head -1)
      if grep -q "Error: script failed\|Traceback" "$log"; then grep -A12 Traceback "$log" | tail -14; echo "STEP FAILED: $1"; exit 1; fi
      grep -E "EXPORTED|LIFT|SOCKETS" "$log" | cut -c1-160 || true; }
B $rel/scripts/rig_fix.py "$here/${MASTER:-work/uv_v1.blend}" "$here/work/rig_final.blend"
B $rel/scripts/build_export.py "$here/work/rig_final.blend" "$here/work/lich_body_tex.glb"
cd "$here"
"$V" -W ignore scripts/clips_mm9.py work/lich_body_tex.glb work/mm9_lich_clips.glb scripts/roles_lich.json work/clips.json | cut -c1-200
cur=work/mm9_lich_clips.glb
if [[ -f scripts/hand_rest_lich.txt ]]; then
  k=0
  while IFS= read -r line; do
    [[ -z "$line" || "$line" == \#* ]] && continue
    k=$((k + 1)); nxt=work/mm9_lich_rest${k}.glb
    eval "$V -W ignore scripts/hand_rest.py $cur $nxt $line" | cut -c1-200
    cur=$nxt
  done < scripts/hand_rest_lich.txt
fi
cp "$cur" export/mm9_lich_lod0.glb
python3 "$repo/tools/prepare_actor_glb.py" export/mm9_lich_lod0.glb export/mm9_lich_runtime_lod0.glb
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/mm9_lich_runtime_lod0.glb" \
  "$here/export/mm9_lich_lods.glb" --mesh-node Lich --max-influences 4 2>&1 | grep "LOD triangles"
"$V" -W ignore scripts/shrink_shadow_lods.py export/mm9_lich_lods.glb export/mm9_lich_lods_shadowfix.glb Lich
"$V" -W ignore ../claude_shared/region_variants.py export/mm9_lich_lods_shadowfix.glb export/mm9_lich_skins.glb textures/lich_ramps.json \
  --extra Lich openyamm_specular=0 --extra Lich pbr.metallicFactor=0
"$V" -W ignore ../claude_shared/emission.py export/mm9_lich_skins.glb export/mm9_lich_glow.glb --material LichHead \
  --mask textures/lich_eye_mask.png --color lich_a=1.0,0.13,0.03 --color lich_b=0.18,1.0,0.25 --strength 2.2 --pulse 0.12,2.3
"$V" -W ignore scripts/cloth_flat.py export/mm9_lich_glow.glb export/mm9_lich_flat.glb | tail -9 | cut -c1-120
"$V" -W ignore ../claude_shared/floor/floor_fix.py export/mm9_lich_flat.glb export/mm9_lich_floored.glb $(set -f; cat scripts/floor_ops.txt) --ground-death Death Dead | tail -4 | cut -c1-200
# convert_abc_model.py keeps LithTech's left-handed numbers, so MM9 GLBs are mirror images of the game's actor: last step, true-handed
"$V" -W ignore scripts/mirror_glb.py export/mm9_lich_floored.glb export/mm9_lich.glb
rm -f export/mm9_lich_lods.geometry.glb
python3 "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/mm9_lich.glb | tail -1
if [[ "${1:-}" == "--install" ]]; then
  python3 "$repo/tools/install_model.py" export/mm9_lich.glb --world mm9
fi
ls -la export/mm9_lich.glb
