#!/usr/bin/env bash
# hvm runtime GLBs from the gated master (rebuild.sh -> rig_v5; texture chain export_uploads -> transfer_uv -> rig_v6):
# clips synced into rig_v6 -> export -> prepare -> LODs -> shadow fix -> colour variants (tunic, hair, beard regions; 9 variants) ->
# head merged into the body (hvm: no prop). NOTHING is installed (batch A: the user installs later;
# the commands are in the README).
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
: "${TOKEN:?set TOKEN to the workspace lease token}"
cd "$repo"
B() { local s=$1; shift; local out log; out=$("$repo/tools/run_creature_blender.sh" --token "$TOKEN" "level_generation/creatures/hes_villager_m_claude/scripts/$s" "$@" 2>&1) || true
      log=$(echo "$out" | grep -o '/tmp/openyamm-creature-blender-[A-Za-z0-9]*\.log' | head -1)
      if grep -q "Error: script failed\|Traceback" "$log"; then grep -A12 Traceback "$log" | tail -14; echo "STEP FAILED: $s"; exit 1; fi
      grep -E "SYNC|PROP|EXPORTED" "$log" | cut -c1-200 || true; }
cd "$here"
B sync_actions.py "$here/work/rig_v5.blend" "$here/work/rig_v6.blend"
B export_runtime.py
python3 "$repo/tools/prepare_actor_glb.py" export/hes_hvm_lod0.glb export/hes_hvm_runtime_lod0.glb
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/hes_hvm_runtime_lod0.glb" \
  "$here/export/hes_hvm_lods.glb" --mesh-node HVM 2>&1 | grep "LOD triangles"
python3 scripts/shrink_shadow_lods.py export/hes_hvm_lods.glb export/hes_hvm_lods_shadowfix.glb
python3 ../claude_shared/region_variants.py export/hes_hvm_lods_shadowfix.glb export/hes_hvm.glb textures/hvm_ramps.json \
  --extra HVM openyamm_specular=1 --extra HVM openyamm_specular_mask=true --extra HVM pbr.metallicFactor=0 \
  --extra HVMHead openyamm_specular=1 --extra HVMHead openyamm_specular_mask=true --extra HVMHead pbr.metallicFactor=0
python3 "$repo/tools/merge_head_material.py" export/hes_hvm.glb export/hes_hvm.glb
rm -f export/hes_hvm_lods.geometry.glb
ls -la export/hes_hvm.glb
