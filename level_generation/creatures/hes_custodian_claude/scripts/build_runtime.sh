#!/usr/bin/env bash
# The Custodian's runtime GLB, NOT installed (the Hesper stage binds export/hes_custodian.glb through
# integration/actors.yml): parts -> reduce + UV -> (Meshy retexture) -> adopt -> compose -> glow geometry -> rig and
# clips -> export -> prepare -> LODs -> shadow LODs -> far LODs (lodrep/, the lod_repair_claude route) -> emission on
# the glow materials -> key times, winding.
# Usage: TOK=<lease> LOD_REPAIR_PYTHON=<venv python with pymeshlab xatlas numpy scipy pillow> scripts/build_runtime.sh
# (the Meshy steps are not rerun: prepare_uv.py must not run again after the retexture, whose maps are painted on
# that layout; Smart UV is deterministic, so a rerun reproduces it).
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
cd "$here"
S=scripts/run.sh
OUT=hes_custodian
$S adopt.py | grep ADOPT
$S dump_tris.py
python3 scripts/compose.py | grep -v "^VENTS"
$S build.py | grep "EYE\|BUILD"
$S rig_anim.py work/build.blend work/anim.blend | grep CLIP
$S export.py
python3 "$repo/tools/prepare_actor_glb.py" export/${OUT}_lod0.glb export/${OUT}_runtime_lod0.glb | tail -1
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/${OUT}_runtime_lod0.glb" \
  "$here/export/${OUT}_lods.glb" --mesh-node Custodian 2>&1 | grep "LOD triangles"
MESH=Custodian python3 scripts/shrink_shadow_lods.py export/${OUT}_lods.glb export/${OUT}_lods_shadowfix.glb
rm -f export/${OUT}_lods.geometry.glb
mkdir -p work
cp export/${OUT}_lods_shadowfix.glb work/${OUT}_nearlods.glb
LOD_REPAIR_PYTHON=${LOD_REPAIR_PYTHON:?set LOD_REPAIR_PYTHON (venv with pymeshlab xatlas numpy scipy pillow)} \
  python3 lodrep/repair_glb.py work/${OUT}_nearlods.glb work/lodrep work/${OUT}_farlods.glb | grep -E "^r[0-9]|RESULT"
# glow: the eye lens and vents orange-red as the sheet (a gentle pulse), the sensor lens blue-white; factor only (no emissive
# texture). emission.py clamps colour x strength per channel at 1, so the colours go in at strength 1 (a 1.6 strength
# turned the amber pale yellow in the viewer)
python3 ../claude_shared/emission.py work/${OUT}_farlods.glb work/${OUT}_glow1.glb --material Cust_Glow \
  --color 1.0,0.15,0.02 --pulse 0.2,2.0
python3 ../claude_shared/emission.py work/${OUT}_glow1.glb export/${OUT}.glb --material Cust_Lens --color 0.55,0.75,1.0
python3 scripts/check_key_times.py export/${OUT}.glb export/${OUT}_lod0.glb
python3 "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/${OUT}.glb | tail -1
ls -la export/${OUT}.glb
