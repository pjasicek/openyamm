#!/usr/bin/env python3
"""Per-component class of the installed LOD0 (work/survey.npz): body shell, head shell, hands, staff, bark (crown branches, wrist
vines: brown paint, R >= G), leaf cards (the rest). Prints the class totals and the protected-share estimate; writes work/classes.npz
(per GLB face, prims concatenated: cls 0 body shell, 1 head shell, 2 hands, 3 staff, 4 bark, 5 leaf; colour)."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_greenman.glb', 'GreenMan')
s = np.load(HERE / 'work' / 'survey.npz'); jn = [str(x) for x in s['jnames']]
PR = list(D)
col = []
for name in PR:
    im = np.asarray(Image.open(HERE / 'work' / f'tex_{name}_B.png').convert('RGB'), np.float64); H, W = im.shape[:2]
    uv = D[name]['UV'][D[name]['T']].mean(1)
    col.append(im[np.clip((uv[:, 1] * H).astype(int), 0, H - 1), np.clip((uv[:, 0] * W).astype(int), 0, W - 1)])
col = np.concatenate(col)
comp, mat, joint, csize = s['comp'], s['mat'], s['joint'], s['csize']
cls = np.full(len(comp), 5)
names = ['body shell', 'head shell', 'hands', 'staff', 'bark', 'leaf']
for c in np.unique(comp):
    m = comp == c; j = np.bincount(joint[m], minlength=len(jn)); jt = jn[j.argmax()]
    cc = col[m].mean(0); n = m.sum()
    if mat[m][0] == 0 and n > 1000: k = 0
    elif mat[m][0] == 1 and n > 1000 and jt == 'Bip01 Head': k = 1
    elif 'Bone01' in jt: k = 3
    elif n > 300 and ('Hand' in jt or 'Forearm' in jt or 'Finger' in jt or 'Thumb' in jt): k = 2
    elif cc[0] >= cc[1]: k = 4
    else: k = 5
    cls[m] = k
for k, nm in enumerate(names):
    for mi in (0, 1):
        m = (cls == k) & (mat == mi)
        if m.any():
            print(f'{nm:11s} prim {mi}: {m.sum():5d} faces in {len(np.unique(comp[m])):3d} comps, mean colour {col[m].mean(0).round()}')
np.savez(HERE / 'work' / 'classes.npz', cls=cls, col=col, names=np.array(names))
