#!/usr/bin/env bash
# v2 turret actor runtime GLBs (Meshy route). Steps per turret: parts.py -> prepare_uv.py (deterministic: they rebuild the
# uploads of the retextures) -> adopt_retexture.py (the retexture's own mesh and UVs) -> dump_tris.py -> compose.py -> build_actor_v2.py
# (mount decoration, LOD0 + authored LOD1..3, rig, clips) -> prepare_actor_glb -> link LODs + shadow LODs
# (scripts/link_lods.py) -> shadow LODs tucked inside -> extras (no creature edge darkening, like its undarkened mount)
# -> emission on the _Energy material (scripts/set_emissive.py: the factor; EMISSIVE_TEXTURE=1 adds the texture once
# the cook accepts it). Exports stay in export/; the mount goes to
# level_generation/props/hesper_decorations/work/hard_surface/. Usage: TOK=<lease token> scripts/build_runtime.sh
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
name=$(basename "$here")
cd "$here"
blend() {   # blend <script> <arg>: run through the lease wrapper, fail on a traceback
  local log
  log=$(cd "$repo" && tools/run_creature_blender.sh --token "$TOK" "level_generation/creatures/$name/scripts/$1" "$2" 2>&1 | grep "Blender log" | awk '{print $3}')
  if grep -qE "Traceback|script failed" "$log"; then grep -B3 -A12 -E "Traceback|script failed" "$log"; echo "STEP FAILED: $1 $2"; exit 1; fi
}
for spec in ward_turret:WardTurret gate_bastion:GateBastion; do
  n=${spec%%:*}; mesh=${spec##*:}; out=hes_${n}_actor
  blend parts.py $n; blend prepare_uv.py $n; blend adopt_retexture.py $n; blend dump_tris.py $n
  python3 scripts/compose.py $n
  blend build_actor_v2.py $n
  python3 "$repo/tools/prepare_actor_glb.py" export/${out}_lod0.glb export/${out}_runtime_lod0.glb | tail -2
  python3 scripts/link_lods.py export/${out}_runtime_lod0.glb export/${out}_authored_lods.glb export/${out}_lods.glb $mesh
  MESH=$mesh python3 scripts/shrink_shadow_lods.py export/${out}_lods.glb export/${out}_lods_shadowfix.glb
  python3 scripts/set_extras.py export/${out}_lods_shadowfix.glb export/${out}.glb HS_ openyamm_edge_darkening=0
  python3 scripts/set_emissive.py ${EMISSIVE_TEXTURE:+--texture} export/${out}.glb export/${out}_lod0.glb
  mv export/lods.json export/${out}_lods.json
  ls -la export/${out}.glb
done
