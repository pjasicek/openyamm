#!/usr/bin/env bash
# Head-protected reduction (decimate_tex.py REA_PROTECT_HEAD=1 REA_PROTECT_ZMIN=1.43 REA_TAG=h, step h65): the head
# faces are the installed head's own, so the installed head texture set is reused (copy_head_uv.py + the installed
# head_retexture_v1 job in compose); only the body is retextured (meshy/body_retexture_h65).
# Order before it: swap_body.py -- h65, export_uploads.py, copy_head_uv.py, the Meshy body job.
set -euo pipefail
cd "$(dirname "$0")/.."
B() { /snap/bin/blender --background --factory-startup --threads 8 --python-exit-code 1 --python "$@"; }
B scripts/transfer_uv.py -- work/rig_v5h.blend meshy/body_retexture_h65 work/rig_v6.blend 2>&1 | grep -E "UVTRANSFER|Error|Traceback" || true
B scripts/fill_holes.py -- work/rig_v6.blend work/rig_v6.blend 2>&1 | grep -E "FILL|Error|Traceback" || true
for l in UVMap HeadUV; do B scripts/uv_raster.py -- work/rig_v6.blend $l 1024 2>&1 | grep -E "Error|Traceback" || true; done
B scripts/bake_ao_natm.py -- work/rig_v6.blend 1024 2>&1 | grep -E "^AO|Error|Traceback" || true
BODY_JOB=meshy/body_retexture_h65 HEAD_JOB=../mm6_natm_claude/meshy/head_retexture_v1 python3 scripts/compose_natm.py 2>&1 | tail -4
bash scripts/build_runtime.sh 2>&1 | grep -E "SPLIT|MERGE|Error|Traceback"
