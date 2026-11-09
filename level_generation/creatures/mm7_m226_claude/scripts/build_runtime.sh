#!/usr/bin/env bash
# m226 runtime GLBs from the gated master (rebuild.sh -> rig_v5; texture chain export_uploads -> transfer_uv -> rig_v6):
# clips synced into rig_v6 -> export -> prepare -> LODs -> shadow fix -> colour variants (cloth + hair regions) ->
# falchion split into an attachment -> head merged into the body. NOTHING is installed (batch A: the user installs later;
# the commands are in the README).
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
: "${TOKEN:?set TOKEN to the workspace lease token}"
cd "$repo"
B() { local s=$1; shift; local out log; out=$("$repo/tools/run_creature_blender.sh" --token "$TOKEN" "level_generation/creatures/mm7_m226_claude/scripts/$s" "$@" 2>&1) || true
      log=$(echo "$out" | grep -o '/tmp/openyamm-creature-blender-[A-Za-z0-9]*\.log' | head -1)
      if grep -q "Error: script failed\|Traceback" "$log"; then grep -A12 Traceback "$log" | tail -14; echo "STEP FAILED: $s"; exit 1; fi
      grep -E "SYNC|PROP|EXPORTED" "$log" | cut -c1-200 || true; }
cd "$here"
B sync_actions.py "$here/work/rig_v5.blend" "$here/work/rig_v6.blend"
B export_runtime.py
python3 "$repo/tools/prepare_actor_glb.py" export/mm7_m226_lod0.glb export/mm7_m226_runtime_lod0.glb
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/mm7_m226_runtime_lod0.glb" \
  "$here/export/mm7_m226_lods.glb" --mesh-node M226 2>&1 | grep "LOD triangles"
python3 scripts/shrink_shadow_lods.py export/mm7_m226_lods.glb export/mm7_m226_lods_shadowfix.glb
python3 ../claude_shared/region_variants.py export/mm7_m226_lods_shadowfix.glb export/mm7_m226.glb textures/m226_ramps.json \
  --extra M226 openyamm_specular=1 --extra M226 openyamm_specular_mask=true --extra M226 pbr.metallicFactor=0 \
  --extra M226Head openyamm_specular=1 --extra M226Head openyamm_specular_mask=true --extra M226Head pbr.metallicFactor=0 \
  --extra Falchion openyamm_specular=1 --extra Falchion openyamm_specular_mask=true --extra Falchion pbr.metallicFactor=0
python3 "$repo/tools/split_attachment.py" export/mm7_m226.glb --joint Sword --body export/mm7_m226.glb \
  --attachment export/mm7_m226_sword.glb
python3 "$repo/tools/merge_head_material.py" export/mm7_m226.glb export/mm7_m226.glb
rm -f export/mm7_m226_lods.geometry.glb
ls -la export/mm7_m226.glb export/mm7_m226_sword.glb
