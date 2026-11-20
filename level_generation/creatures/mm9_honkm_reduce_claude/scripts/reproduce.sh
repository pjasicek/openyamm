#!/usr/bin/env bash
# Rebuild the picked candidate (set n, ladder step r60: set l with the medallion exact, orchestrator 2026-11-04) from the installed GLB in before/. Run from anywhere.
set -euo pipefail
cd "$(dirname "$0")/.."
G="../claude_shared/gltf_venv/bin/python -W ignore"
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
REA_GLB=level_generation/creatures/mm9_honkm_reduce_claude/before/mm9_honkm.glb REA_NODE=HonkM $BL -P scripts/import_source.py
$BL -P scripts/dump_mesh.py
$G scripts/tex_extract.py
$G scripts/make_sets.py a                                    # classes + base keep set
$G scripts/neck_zone.py a neck                               # robe round the neckline
RING=0 $G scripts/paint_edges.py a paint0                    # robe faces across a paint/mask boundary
scripts/cap.sh $G scripts/honk_contact.py a contact          # faces under the hands (every clip)
python3 - <<'PY'
import json, numpy as np
s = np.load('work/glb_sets_a.npz'); C = json.load(open('work/classes.json'))['names']
np.save('work/contact_nomed.npy', np.load('work/contact.npy') & (s['cls'] != C.index('medallion')))
PY
FOREARM_GROUP=1 KEEP_EXTRA=neck,contact,paint0 $G scripts/make_sets.py d
$G scripts/extra_keeps.py d                                  # shoulder (unused), boottop (unused), tube
HATR=0 FOREARM_GROUP=1 KEEP_EXTRA=neck,contact,paint0,tube $G scripts/make_sets.py n
SETS=n MP_GROUPS=1:0.6,2:0.6,3:0.85,5:1.0,6:1.0 MP_SEAM_GROUPS=1 scripts/run_mp.sh n 0.6   # mpqem with texture + chart guards
scripts/build_mp.sh mp_n_r60 export/mm9_honkm.glb
$G scripts/uv_escape.py before/mm9_honkm.glb export/mm9_honkm.glb; $G scripts/face_exact.py export/mm9_honkm.glb n
(cd ../../.. && level_generation/creatures/claude_shared/gltf_venv/bin/python -W ignore level_generation/creatures/claude_shared/reduction_uv_audit.py \
  level_generation/creatures/mm9_honkm_reduce_claude/export/mm9_honkm.glb level_generation/creatures/mm9_honkm_reduce_claude/before/mm9_honkm.glb \
  --json level_generation/creatures/mm9_honkm_reduce_claude/review/uv_audit_n60.json)
