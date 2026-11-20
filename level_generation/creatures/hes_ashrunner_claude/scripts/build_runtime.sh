#!/usr/bin/env bash
# Ashrunners runtime GLBs (from the Landfall guard, hes_guard_claude), NOT installed: clips synced from the gated chain
# (rig_v5) into the textured master (rig_v6) -> LOD0 reduction -> export -> prepare -> LODs -> shadow fix -> tier
# variants -> one attachment per gun / gear bone (glow parts their own) -> head material merged -> key-time gate
# (check_key_times.py: finite, strictly increasing keys on every channel). face_fix.py polishes the master's face once.
# Exports stay in export/.
# Usage: TOK=<lease token> scripts/build_runtime.sh
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
name=$(basename "$here")
cd "$here"
OUT=hes_ashrunner; PFX=har; MESH=HAR
export MESH
B() { local out log; out=$(cd "$repo" && tools/run_creature_blender.sh --token "$TOK" "level_generation/creatures/$name/scripts/$1" "${@:2}" 2>&1) || true
      log=$(echo "$out" | grep "Blender log" | awk '{print $3}')
      [ -n "$log" ] || { echo "$out" | tail -n 3; echo "STEP FAILED (no Blender log): $1"; exit 1; }
      grep -E '^[A-Z][A-Z0-9_]+[ :]' "$log" | grep -v -E '^(Blender|FBX|Read|Info|INFO)' | cut -c1-300 || true
      if grep -q "Traceback\|script failed" "$log"; then grep -A12 Traceback "$log" | head -20; echo "STEP FAILED: $1"; exit 1; fi; }
B sync_actions.py "$here/work/rig_v5.blend" "$here/work/rig_v6.blend"
B face_fix.py "$here/work/rig_v6.blend"   # hood lip off the left eye, goggles over the hood (idempotent)
RATIO=${RATIO:-0.9} FACE=B_Head PROTECT=B_Head B halve_lod0.py "$here/work/rig_v6.blend" "$here/work/rig_v6h.blend"
B export_actor.py
python3 "$repo/tools/prepare_actor_glb.py" export/${OUT}_lod0.glb export/${OUT}_runtime_lod0.glb
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/${OUT}_runtime_lod0.glb" \
  "$here/export/${OUT}_lods.glb" --mesh-node $MESH 2>&1 | grep "LOD triangles"
python3 scripts/shrink_shadow_lods.py export/${OUT}_lods.glb export/${OUT}_lods_shadowfix.glb
EX=()
for m in $MESH Rifle Carbine Pistol ChestPlate Buckler; do
  EX+=(--extra $m openyamm_specular=1 --extra $m openyamm_specular_mask=true --extra $m pbr.metallicFactor=0)
done
python3 ../claude_shared/region_variants.py export/${OUT}_lods_shadowfix.glb export/${OUT}.glb textures/${PFX}_ramps.json "${EX[@]}"
for j in RifleGlow:rifle_glow Rifle:rifle CarbineGlow:carbine_glow Carbine:carbine PistolGlow:pistol_glow Pistol:pistol \
         BucklerGlow:buckler_glow Buckler:buckler ChestPlate:chest_plate; do
  python3 "$repo/tools/split_attachment.py" export/${OUT}.glb --joint ${j%%:*} --body export/${OUT}.glb --attachment export/${OUT}_${j##*:}.glb
done
python3 scripts/clamp_uv.py export/${OUT}.glb   # LOD rounding at the atlas edge (see the script)
python3 "$repo/tools/merge_head_material.py" export/${OUT}.glb export/${OUT}.glb
rm -f export/${OUT}_lods.geometry.glb
# far LODs (2026-10-22): LOD2/LOD3 and their shadows by the lod_repair_claude route (lodrep/ = unchanged copies of its
# scripts with repair_glb.py taking an explicit GLB): own UVs and 512/256 px textures filled from LOD0 (region mask RGBA),
# first ladder step passing the switch gate; rerun whenever LOD0's textures change. LOD_REPAIR_PYTHON: pymeshlab, xatlas
cp export/${OUT}.glb work/${OUT}_nearlods.glb
LOD_REPAIR_PYTHON=${LOD_REPAIR_PYTHON:?set LOD_REPAIR_PYTHON (venv with pymeshlab xatlas numpy scipy pillow)} \
  python3 lodrep/repair_glb.py work/${OUT}_nearlods.glb work/lodrep export/${OUT}.glb | grep -E "^r[0-9]|RESULT"
python3 scripts/check_key_times.py export/${OUT}.glb export/${OUT}_lod0.glb export/${OUT}_pistol.glb export/${OUT}_pistol_glow.glb \
  export/${OUT}_rifle.glb export/${OUT}_rifle_glow.glb export/${OUT}_carbine.glb export/${OUT}_carbine_glow.glb \
  export/${OUT}_buckler.glb export/${OUT}_buckler_glow.glb export/${OUT}_chest_plate.glb
ls -la export/${OUT}*.glb
