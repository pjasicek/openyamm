#!/usr/bin/env bash
# Drone runtime GLBs, NOT installed (exports stay in export/): export -> unlit/blend fixes -> prepare -> LODs ->
# shadow LODs tucked inside -> A/B/C skins (one shared skin, region ramps) -> the tier gear split into attachments.
# Usage: TOK=<lease token> scripts/build_runtime.sh
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
cd "$here"
TOK=${TOK:?set TOK} scripts/step.sh export.py
python3 scripts/fix_materials.py export/hes_drone_lod0.glb export/hes_drone_lod0.glb
python3 "$repo/tools/prepare_actor_glb.py" export/hes_drone_lod0.glb export/hes_drone_runtime_lod0.glb | tail -1
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/hes_drone_runtime_lod0.glb" \
  "$here/export/hes_drone_lods.glb" --mesh-node HDR 2>&1 | grep "LOD triangles"
MESH=HDR python3 "$here/../hes_turrets_claude/scripts/shrink_shadow_lods.py" export/hes_drone_lods.glb export/hes_drone_lods_shadowfix.glb
python3 ../claude_shared/region_variants.py export/hes_drone_lods_shadowfix.glb export/hes_drone_all.glb textures/hdr_ramps.json \
  --extra Casing openyamm_specular=0 --extra Casing pbr.metallicFactor=0 \
  --extra Glow openyamm_specular=0 --extra Glow pbr.metallicFactor=0 --extra Glow openyamm_edge_darkening=0 \
  --extra Thrust openyamm_specular=0 --extra Thrust pbr.metallicFactor=0 --extra Thrust openyamm_edge_darkening=0
# tier gear: B's twin emitter (barrel + glowing disc), C's shield ring (band + glowing cells)
cp export/hes_drone_all.glb export/hes_drone.glb
python3 "$repo/tools/split_attachment.py" export/hes_drone.glb --joint GearEmitter --body export/hes_drone.glb --attachment export/hes_drone_twin_emitter.glb
python3 "$repo/tools/split_attachment.py" export/hes_drone.glb --joint GearEmitterGlow --body export/hes_drone.glb --attachment export/hes_drone_twin_emitter_glow.glb
python3 "$repo/tools/split_attachment.py" export/hes_drone.glb --joint GearRing --body export/hes_drone.glb --attachment export/hes_drone_shield_ring.glb
python3 "$repo/tools/split_attachment.py" export/hes_drone.glb --joint GearRingGlow --body export/hes_drone.glb --attachment export/hes_drone_shield_ring_glow.glb
rm -f export/hes_drone_lods.geometry.glb
[ -f export/lods.json ] && mv export/lods.json export/hes_drone_lods.json
ls -la export/*.glb
