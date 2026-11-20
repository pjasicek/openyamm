#!/usr/bin/env bash
# The Harvester's runtime GLB (Meshy route, after hes_turrets_claude/scripts/build_runtime.sh). Steps: parts.py ->
# prepare_uv.py (xatlas in work/xatlas_venv; deterministic: it rebuilds the retexture's upload) -> adopt_retexture.py
# (the retexture's own mesh and UVs) -> dump_tris.py -> compose.py -> build_actor.py (added glow pieces, rig, clips,
# LOD0 + authored LOD1..3) -> prepare_actor_glb -> link LODs + shadow LODs (link_lods.py) -> shadow LODs tucked
# inside -> emission: the hull's orange seams (claude_shared/emission.py, seam mask) and HS_Glow_Harvester. Exports stay in export/ (the Hesper stage binds export/hes_harvester.glb).
# Usage: TOK=<lease token> scripts/build_runtime.sh
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
name=$(basename "$here")
cd "$here"
blend() {   # blend <script>: run through the lease wrapper, fail on a traceback
  local log
  log=$(cd "$repo" && tools/run_creature_blender.sh --token "$TOK" "level_generation/creatures/$name/scripts/$1" 2>&1 | grep "Blender log" | awk '{print $3}')
  if grep -qE "Traceback|script failed" "$log"; then grep -B3 -A12 -E "Traceback|script failed" "$log"; echo "STEP FAILED: $1"; exit 1; fi
  grep -E "PART_TRIS|XATLAS|ADOPT part|LOD_TRIS|FLOOR" "$log" || true
}
out=hes_harvester
blend parts.py; blend prepare_uv.py; blend adopt_retexture.py; blend dump_tris.py
python3 scripts/compose.py | tail -1
blend build_actor.py
python3 "$repo/tools/prepare_actor_glb.py" export/${out}_lod0.glb export/${out}_runtime_lod0.glb | tail -2
python3 scripts/link_lods.py export/${out}_runtime_lod0.glb export/${out}_authored_lods.glb export/${out}_lods.glb Harvester
MESH=Harvester python3 scripts/shrink_shadow_lods.py export/${out}_lods.glb export/${out}.glb
# the hull's orange seams (compose.py's seam mask; emission.py matches the prefix HS_Harvester, hence the glow
# material's name HS_Glow_Harvester; it clamps each channel at 1, so strength 1 keeps the orange), then the glow's strength
for f in export/${out}.glb export/${out}_lod0.glb; do
  python3 "$repo/level_generation/creatures/claude_shared/emission.py" $f $f --material HS_Harvester \
      --mask textures/harvester_seam_mask.png --color 1.0,0.42,0.1 --strength 1.0 | tail -1
done
python3 scripts/set_emissive.py export/${out}.glb export/${out}_lod0.glb
mv export/lods.json export/${out}_lods.json
python3 scripts/check_key_times.py export/${out}.glb
blend floor_check.py
python3 "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/${out}.glb | tail -2
ls -la export/${out}.glb
