#!/usr/bin/env bash
# Vampire runtime GLBs (mm7 batch F; the batch-B robed-caster build, adapted from mm6_natm_claude/scripts/build_runtime.sh), NOT installed:
# clips synced from the gated chain (rig_v5) into the textured master (rig_v6) -> export -> prepare -> LODs -> shadow
# fix -> colour variants (three regions: coat, cape+collar, hair) -> head material merged into the body. Exports stay in export/.
# Usage: TOK=<lease token> scripts/build_runtime.sh
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
name=$(basename "$here")
cd "$here"
OUT=$(python3 -c "import json;print(json.load(open('creature.json'))['out'])"); PFX=$(python3 -c "import json;print(json.load(open('creature.json'))['prefix'])"); MESH=$(python3 -c "import json;print(json.load(open('creature.json'))['mesh'])")
export MESH
B() { local out log; out=$(cd "$repo" && tools/run_creature_blender.sh --token "$TOK" "level_generation/creatures/$name/scripts/$1" "${@:2}" 2>&1) || true
      log=$(echo "$out" | grep "Blender log" | awk '{print $3}')
      grep -E '^[A-Z][A-Z0-9_]+[ :]' "$log" | grep -v -E '^(Blender|FBX|Read|Info|INFO)' | cut -c1-300 || true
      if grep -q "Traceback\|script failed" "$log"; then grep -A12 Traceback "$log" | head -20; echo "STEP FAILED: $1"; exit 1; fi; }
B sync_actions.py "$here/work/rig_v5.blend" "$here/work/rig_v6.blend"
B export_actor.py
python3 "$repo/tools/prepare_actor_glb.py" export/${OUT}_lod0.glb export/${OUT}_runtime_lod0.glb
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/${OUT}_runtime_lod0.glb" \
  "$here/export/${OUT}_lods.glb" --mesh-node $MESH 2>&1 | grep "LOD triangles"
python3 scripts/shrink_shadow_lods.py export/${OUT}_lods.glb export/${OUT}_lods_shadowfix.glb
python3 ../claude_shared/region_variants.py export/${OUT}_lods_shadowfix.glb export/${OUT}.glb textures/${PFX}_ramps.json \
  --extra $MESH openyamm_specular=1 --extra $MESH openyamm_specular_mask=true --extra $MESH pbr.metallicFactor=0
if python3 -c "import json,sys;sys.exit(0 if 'staff' in json.load(open('creature.json')) else 1)"; then
  python3 "$repo/tools/split_attachment.py" export/${OUT}.glb --joint Staff --body export/${OUT}.glb --attachment export/${OUT}_staff.glb
fi
python3 "$repo/tools/merge_head_material.py" export/${OUT}.glb export/${OUT}.glb
rm -f export/${OUT}_lods.geometry.glb
ls -la export/${OUT}.glb
