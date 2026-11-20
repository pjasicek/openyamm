#!/usr/bin/env python3
"""Per-face keep / group sets on the installed Basilisk LOD0 (one primitive, Basilisk_A) for mpqem.py:
work/glb_sets_<tag>.npz (keep, group, lining, lined; one entry per GLB face). Prio-1 relaxed keep set
(REDUCTION_BRIEF_20261104), classes by dominant bone (survey.py) and the region mask (R = red: frill, mouth, claws):
- exact: separate pieces (eyes, teeth, gum strips: every component but the body), the whole jaw (lower jaw skin, mouth floor),
  the face (head-weighted faces in front of FACE_Z: snout, nostrils, lips, eyes and lids, brow ridges), the soles (faces within
  SOLE m of the floor), the claws (red-mask toe faces: CLAW=1 any corner red, CLAW=centroid centroid red), optional extra keep files work/keep_extra_<name>.npy;
- group 1: toes and thumbs (Xf/Xm/Xr fing/thumb dominant, claws excluded) at MP_GROUPS 1:<r>;
- group 2: frill plates (Xfin dominant, or head-weighted red faces behind FACE_Z) at 2:<r>;
- group 3: cranium, crown and neck top (head-weighted faces behind FACE_Z, not frill) at 3:<r>; crown horns (head faces behind FACE_Z within HORN_X of the
  centre line reaching above HORN_Y) are kept when HORNS=keep, else group 4;
- group 0: body, legs, tail, neck at the ladder ratio.
Usage: basil_sets.py <tag> [extra keep names...]"""
import os, sys
from collections import Counter
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as gb  # noqa: E402
E = lambda k, d: os.environ.get(k, d)
FACE_Z = float(E('FACE_Z', '1.36')); SOLE = float(E('SOLE', '0.012')); HORN_Y = float(E('HORN_Y', '1.02'))
CLAW = E('CLAW', '1') == '1'; HORNS = E('HORNS', 'keep')
tag = sys.argv[1]; extras = sys.argv[2:]
doc, b = gb.read(HERE / 'before' / 'mm9_basilisk.glb')
node = next(n for n in doc['nodes'] if n.get('name') == 'Basilisk' and 'mesh' in n)
p = gb.prims(doc, b, node['mesh'])[0]
P, T = p['POSITION'].astype(float), p['T']; nF = len(T); C = P[T].mean(1)
S = np.load(HERE / 'work' / 'survey.npz'); cls = S['cls']; red = S['mask'][:, 0] > 100
# red at any corner too (claw tips are small)
from PIL import Image
mask = np.asarray(Image.open(HERE / 'work' / 'tex_Basilisk_M.png').convert('RGB'))
H_, W_ = mask.shape[:2]; UV = p['TEXCOORD_0']
x = np.clip((UV[T][..., 0] % 1) * W_, 0, W_ - 1).astype(int); y = np.clip((UV[T][..., 1] % 1) * H_, 0, H_ - 1).astype(int)
red_any = red | (mask[y, x][..., 0] > 100).any(1)
body = S['comp_size'] > 1000
piece = ~body
jaw = body & (cls == 'jaw')
headish = body & (cls == 'head')
face = headish & (C[:, 2] > FACE_Z)
HORN_X = float(E('HORN_X', '0.13'))
horn = headish & ~face & (np.abs(C[:, 0]) < HORN_X) & (P[T][:, :, 1].max(1) > HORN_Y)
frill = body & ((cls == 'frill') | (headish & ~face & red)) & ~horn
cran = headish & ~face & ~frill & ~horn
toes = body & (cls == 'toes')
claw = (toes & (red if E('CLAW', '1') == 'centroid' else red_any)) if CLAW or E('CLAW', '1') == 'centroid' else np.zeros(nF, bool)
sole = body & (P[T][:, :, 1].min(1) < P[:, 1].min() + SOLE)
keep = piece | jaw | face | sole | claw | (horn if HORNS == 'keep' else np.zeros(nF, bool))
for name in extras:
    k = np.load(HERE / 'work' / f'keep_extra_{name}.npy'); keep |= k; print('extra', name, int(k.sum()))
group = np.zeros(nF, int)
group[toes & ~keep] = 1; group[frill & ~keep] = 2; group[cran & ~keep] = 3; group[horn & ~keep] = 4
print(f'faces {nF}: pieces {int(piece.sum())}, jaw {int(jaw.sum())}, face {int(face.sum())}, soles {int(sole.sum())}, '
      f'claws {int(claw.sum())}, horns {int(horn.sum())}, frill {int(frill.sum())}, cranium {int(cran.sum())}, toes {int(toes.sum())}')
print(f'keep {int(keep.sum())} ({keep.mean() * 100:.1f} %); free per group', dict(Counter(group[~keep].tolist())))
print('free classes in group 0', Counter(cls[~keep & (group == 0)].tolist()).most_common())
np.savez(HERE / 'work' / f'glb_sets_{tag}.npz', keep=keep, group=group, lining=np.zeros(nF, bool), lined=np.zeros(nF, bool),
         claw=claw, face=face, horn=horn, frill=frill)
