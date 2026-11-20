#!/usr/bin/env bash
# Runtime GLBs of the colony and Lattice machines, NOT installed (the Hesper stage binds export/ through
# integration/actors.yml). Per machine: build_machine.py (LOD0, rig, clips; the turret's mount) -> prepare_actor_glb
# (glTF normal convention) -> build_actor_lods (LOD1..3 + shadow LODs) -> shadow LODs tucked inside -> set_glow.py
# (factor-only emission, the dark copies' factor, edge darkening 0) -> far LODs by the lod_repair_claude route
# (lodrep/: copies of its scripts, repair_glb.py taking an explicit GLB) -> key-time check.
# Steps before it (once per Meshy return): parts.py, prepare_uv.py, adopt_retexture.py, dump_tris.py, compose.py
# (the conduit: UV_VERSION=v2 prepare_uv/adopt, mark_energy.py before compose).
# Usage: TOK=<lease token> LOD_REPAIR_PYTHON=<venv python> scripts/build_runtime.sh [name...]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
name=$(basename "$here")
cd "$here"
blend() {   # blend <script> <args...>: run through the lease wrapper, fail on a traceback
  local out log
  out=$(cd "$repo" && tools/run_creature_blender.sh --token "$TOK" "level_generation/creatures/$name/scripts/$1" "${@:2}" 2>&1) || true
  log=$(echo "$out" | grep "Blender log" | awk '{print $3}')
  [ -n "$log" ] || { echo "$out" | tail -n 3; echo "STEP FAILED (no Blender log): $1"; exit 1; }
  if grep -qE "Traceback|script failed" "$log"; then grep -B3 -A12 -E "Traceback|script failed" "$log"; echo "STEP FAILED: $1"; exit 1; fi
}
declare -A MESH=([starport_turret]=StarportTurret [capacitor_column]=CapacitorCell [throne_conduit]=ThroneConduit
                [test_emplacement]=TestEmplacement)
names=("$@"); [ ${#names[@]} -gt 0 ] || names=(starport_turret capacitor_column throne_conduit test_emplacement)
for n in "${names[@]}"; do
  out=hes_$n; mesh=${MESH[$n]}
  if [ $n = test_emplacement ]; then blend build_emplacement.py; else blend build_machine.py $n; fi
  python3 "$repo/tools/prepare_actor_glb.py" export/${out}_lod0.glb work/${out}_runtime_lod0.glb | tail -1
  /snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
    --python "$repo/tools/build_actor_lods.py" -- "$here/work/${out}_runtime_lod0.glb" "$here/work/${out}_lods.glb" \
    --mesh-node $mesh 2>&1 | grep "LOD triangles" || { echo "STEP FAILED: build_actor_lods $n"; exit 1; }
  MESH=$mesh python3 scripts/shrink_shadow_lods.py work/${out}_lods.glb work/${out}_near.glb | tail -1
  python3 scripts/set_glow.py $n work/${out}_near.glb
  rm -rf work/lodrep_$n
  ladder=; [ $n = throne_conduit ] && ladder=0.4:0.25   # the best reachable step: README "Far LODs"
  LOD_LADDER=$ladder LOD_REPAIR_PYTHON=${LOD_REPAIR_PYTHON:?set LOD_REPAIR_PYTHON (venv with pymeshlab xatlas numpy scipy pillow)} \
    python3 lodrep/repair_glb.py work/${out}_near.glb work/lodrep_$n export/${out}.glb | grep -E "^r[0-9]|RESULT|PASS|FAIL" || true
  python3 scripts/check_key_times.py export/${out}.glb export/${out}_lod0.glb
  ls -la export/${out}.glb
done
