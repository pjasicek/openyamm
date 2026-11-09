#!/usr/bin/env bash
# Turret actor runtime GLBs: build (scripts/build_turret_actor.py, LOD0 and authored LOD1..3) -> prepare -> link the
# authored LODs and their shadow LODs (scripts/link_lods.py) -> shadow LODs
# tucked inside -> material extras (no creature edge darkening, so the head matches its undarkened mount
# decoration). Exports stay in export/. Usage: TOK=<lease token> scripts/build_runtime.sh
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
name=$(basename "$here")
cd "$here"
for spec in hes_ward_turret_actor:WardTurret hes_gate_bastion_actor:GateBastion; do
  out=${spec%%:*}; mesh=${spec##*:}
  log=$(cd "$repo" && tools/run_creature_blender.sh --token "$TOK" "level_generation/creatures/$name/scripts/build_turret_actor.py" $out 2>&1 | grep "Blender log" | awk '{print $3}')
  grep -q "^EXPORTED" "$log" || { grep -A12 Traceback "$log"; echo "STEP FAILED: build $out"; exit 1; }
  python3 "$repo/tools/prepare_actor_glb.py" export/${out}_lod0.glb export/${out}_runtime_lod0.glb | tail -1
  python3 scripts/link_lods.py export/${out}_runtime_lod0.glb export/${out}_authored_lods.glb \
    export/${out}_lods.glb $mesh
  MESH=$mesh python3 scripts/shrink_shadow_lods.py export/${out}_lods.glb export/${out}_lods_shadowfix.glb
  python3 scripts/set_extras.py export/${out}_lods_shadowfix.glb export/${out}.glb HS_ openyamm_edge_darkening=0
  mv export/lods.json export/${out}_lods.json
  ls -la export/${out}.glb
done
