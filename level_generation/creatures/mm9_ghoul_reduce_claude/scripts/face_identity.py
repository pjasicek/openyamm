#!/usr/bin/env python3
"""Every installed LOD0 face that the keep set held exact (face skin, teeth, eyes, plug; claws, flaps, lining, neck seam, soles)
must be in the candidate with byte-identical corner attributes (POSITION, NORMAL, TEXCOORD_0, JOINTS_0, WEIGHTS_0) in the same
primitive. Usage: face_identity.py <candidate.glb> <sets tag>"""
import sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as gb  # noqa: E402
SEM = ('POSITION', 'NORMAL', 'TEXCOORD_0', 'JOINTS_0', 'WEIGHTS_0')


def faces(path):
    d, b = gb.read(path); node = next(n for n in d['nodes'] if n.get('name') == 'Ghoul' and 'mesh' in n)
    out = {}
    for p in gb.prims(d, b, node['mesh']):
        corner = np.concatenate([p[s].astype(np.float64).reshape(len(p[s]), -1) for s in SEM], 1)
        rows = [b''.join(corner[t].tobytes() for t in tri) for tri in p['T']]
        out[p['material']] = rows
    return out


a = faces(HERE / 'before' / 'mm9_ghoul.glb'); c = faces(Path(sys.argv[1]))
keep = np.load(HERE / 'work' / f'glb_sets_{sys.argv[2]}.npz')['keep']
lab = np.load(HERE / 'work' / 'labels.npz')
off = 0
for name in ('Ghoul_A', 'GhoulHead_A'):
    rows = a[name]; k = keep[off:off + len(rows)]; off += len(rows)
    have = set(c[name])
    want = [r for r, kk in zip(rows, k) if kk]
    miss = sum(r not in have for r in want)
    print(f'{name}: exact faces {len(want)}, present byte-identical {len(want) - miss}, missing {miss}')
h = lab['head']; rows = a['GhoulHead_A']; have = set(c['GhoulHead_A'])
for part, nm in ((10, 'face skin'), (12, 'teeth'), (13, 'eyes'), (22, 'plug')):
    want = [r for r, l in zip(rows, h) if l == part]
    print(f'  {nm}: {len(want)}, missing {sum(r not in have for r in want)}')
