#!/usr/bin/env bash
# After the two Meshy retexture downloads (meshy/{body,head}_retexture_r55): Meshy's body layout and the head layout onto
# the swapped r55 master, raster, AO, compose (the cannibal's compose_natm.py: skin repaint, region mask, tier ramps),
# then the cannibal's runtime chain (export, prepare, LODs, shadow LODs, region variants, attachments, head merge).
# Order before it: scripts/swap_body.py -- r55, scripts/export_uploads.py, the Meshy jobs.
set -euo pipefail
cd "$(dirname "$0")/.."
B() { /snap/bin/blender --background --factory-startup --threads 8 --python-exit-code 1 --python "$@"; }
B scripts/transfer_uv.py -- work/rig_v5h.blend meshy/body_retexture_r55 work/rig_v6a.blend 2>&1 | grep -E "UVTRANSFER|Error|Traceback" || true
B scripts/transfer_uv.py -- work/rig_v6a.blend meshy/head_retexture_r55 work/rig_v6.blend HeadUV 2>&1 | grep -E "UVTRANSFER|Error|Traceback" || true
for l in UVMap HeadUV; do B scripts/uv_raster.py -- work/rig_v6.blend $l 1024 2>&1 | grep -E "RASTER|Error|Traceback" || true; done
B scripts/bake_ao_natm.py -- work/rig_v6.blend 1024 2>&1 | grep -E "AO|Error|Traceback" || true
python3 scripts/compose_natm.py 2>&1 | tail -5
bash scripts/build_runtime.sh
