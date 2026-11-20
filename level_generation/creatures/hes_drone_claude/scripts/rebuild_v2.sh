#!/usr/bin/env bash
# Replay the hand-built drone (v2) end to end, credit-free: body -> rig -> gear -> AO -> textures -> clips -> runtime
# GLBs -> viewer. Usage: TOK=<lease token> scripts/rebuild_v2.sh
set -euo pipefail
cd "$(dirname "$0")/.."
: "${TOK:?set TOK}"
scripts/step.sh build_body.py
scripts/step.sh rig.py
scripts/step.sh gear.py
scripts/step.sh dump_uv3d.py
python3 scripts/components.py
scripts/step.sh bake_ao.py
python3 scripts/compose_v2.py
python3 scripts/tier_bake.py
scripts/step.sh anim.py
scripts/build_runtime.sh
python3 scripts/floor_check.py export/hes_drone.glb
for v in hdr_a hdr_b hdr_c; do
  scripts/step.sh viewer_export.py $v
  python3 scripts/fix_materials.py review/viewer/hes_drone_${v: -1}.glb review/viewer/hes_drone_${v: -1}.glb
done
python3 scripts/update_viewer_manifest.py
