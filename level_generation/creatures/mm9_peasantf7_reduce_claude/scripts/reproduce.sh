#!/usr/bin/env bash
# Rebuild the picked candidate (set f, step r45) from the installed GLB in before/. Run from anywhere; one Blender at a time.
set -euo pipefail
cd "$(dirname "$0")/.."
G="../claude_shared/gltf_venv/bin/python -W ignore"
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
REA_GLB=level_generation/creatures/mm9_peasantf7_reduce_claude/before/mm9_peasantf7.glb REA_NODE=PeasantF7 $BL -P scripts/import_source.py
REA_PROTECT=Head $BL -P scripts/dump_mesh.py
$G scripts/tex_extract.py                                   # guard images: body base colour + region mask, head tiers A and B
$G scripts/pf7_parts.py                                     # part labels from ../mm9_peasantf7_claude/work/uv_lined.npz
SOLE=0.012 $G scripts/make_sets_pf7.py a                    # classes (needed by the leg-top keep below)
$G - <<'PY'
import sys, json; sys.path.insert(0, 'scripts'); import glbio, numpy as np
doc, b, nd, D = glbio.load('before/mm9_peasantf7.glb', 'PeasantF7')
s = np.load('work/glb_sets_a.npz'); C = json.load(open('work/classes.json'))['names']
P, T = D['PeasantF7_A']['P'], D['PeasantF7_A']['T']; n = len(T)
top = np.zeros(len(s['cls']), bool); top[:n] = (s['cls'][:n] == C.index('legs')) & (P[T][:, :, 1].max(1) > -0.71)
np.save('work/legtop.npy', top); print('LEGTOP', top.sum())
PY
SOLE=0.012 KEEP_EXTRA=legtop $G scripts/make_sets_pf7.py f
MPQEM=mpqem_chart.py MP_CHART=1 MP_ANISO=1.6 MP_W5=4 SETS=f MP_SEAM_GROUPS=1,2,3 \
  MP_GROUPS=1:0.5,2:0.75,3:0.5,4:0.4,5:0.55,6:0.4,7:0.6 MP_TEX_MAX=70 MP_TEX_MEAN=30 scripts/run_mp.sh f 0.45
SOLE=0.012 scripts/build_mp.sh mp_f_r45 export/mm9_peasantf7.glb
