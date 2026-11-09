#!/usr/bin/env bash
# Forad runtime GLB (2026-10-30 rework, playbook rig): rig_v5 -> export_runtime.py -> prepare -> LODs -> shadow fix ->
# material extras -> floor fix -> winding check [-> install --world mm9]. Usage: TOKEN=<lease> scripts/build_runtime_forad.sh [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../../.." && pwd)"
: "${TOKEN:?set TOKEN}"
cd "$here"
out=$(cd "$repo" && tools/run_creature_blender.sh --token "$TOKEN" level_generation/creatures/mm9_forad_claude/v2/scripts/export_runtime.py 2>&1) || true
log=$(echo "$out" | grep -o '/tmp/openyamm-creature-blender-[A-Za-z0-9]*\.log' | head -1)
if [ -z "$log" ] || grep -q "Traceback" "$log"; then grep -A12 Traceback "$log" | tail -14; echo "STEP FAILED: export"; exit 1; fi
grep EXPORTED "$log" | cut -c1-300
python3 "$repo/tools/prepare_actor_glb.py" export/mm9_forad_lod0.glb export/mm9_forad_runtime_lod0.glb
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/mm9_forad_runtime_lod0.glb" \
  "$here/export/mm9_forad_lods.glb" --mesh-node Forad --max-influences 4 2>&1 | grep "LOD triangles"
python3 scripts/shrink_shadow_lods.py export/mm9_forad_lods.glb export/mm9_forad_lods_shadowfix.glb Forad
python3 scripts/set_material_extras.py export/mm9_forad_lods_shadowfix.glb export/mm9_forad_extras.glb \
  openyamm_specular=0 pbr.metallicFactor=0
python3 ../../claude_shared/floor/floor_fix.py export/mm9_forad_extras.glb export/mm9_forad.glb --ground-loop Standing \
  --ground-loop Walking --ground-loop Fidget --ground-loop Talk --ground-loop Bow --ground-loop AttackMelee --ground-loop Hit \
  --raise Running --ground-death Death Dead
rm -f export/mm9_forad_lods.geometry.glb
python3 "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/mm9_forad.glb | tail -1
if [[ "${1:-}" == "--install" ]]; then
  python3 "$repo/tools/install_model.py" export/mm9_forad.glb --world mm9
fi
ls -la export/mm9_forad.glb
