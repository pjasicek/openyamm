#!/usr/bin/env python3
"""Where a candidate LOD0 deviates from the installed one: both skinned (glb_pose) at every 3rd 30 fps frame of the given clips;
each installed vertex's distance to the candidate surface (dense surface samples, ~2 mm) and back; prints the worst frames and
the worst vertices with their set part and dominant joint. Usage: M=1 probe_err.py <cand_lod0.glb> <sets tag> [clips]"""
import os
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE / 'scripts'))
from glb_pose import Glb, Model  # noqa: E402
M_ = os.environ['M']
src = Model(Glb(str(HERE / 'before' / f'mm9_peasanthof{M_}.glb'))); cand = Model(Glb(sys.argv[1]))
sets = np.load(HERE / 'work' / f'hof{M_}' / f'glb_sets_{sys.argv[2]}.npz'); part = sets['part']
names = {0: 'dress', 1: 'hands', 2: 'braids', 3: 'hair', 4: 'boots', 5: 'legs', 6: 'forearms', 7: 'skirt', 8: 'lining', 9: 'rim',
         10: 'head skin', 11: 'ears', 12: 'kerchief', 13: 'small', 14: 'other'}
clips = sys.argv[3].split(',') if len(sys.argv) > 3 else src.clips
import bglbio as gb  # noqa: E402
def tris(path):
    d, b = gb.read(path); node = next(n for n in d['nodes'] if n.get('name') == 'PeasantHOF' and 'mesh' in n)
    return [p['T'] for p in gb.prims(d, b, node['mesh'])]
TS = tris(HERE / 'before' / f'mm9_peasanthof{M_}.glb'); TC = tris(sys.argv[1])
vpart = []
off = 0
for T in TS:
    vp = np.full(T.max() + 1, -1); vp[T.ravel()] = np.repeat(part[off:off + len(T)], 3); vpart.append(vp); off += len(T)
W = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1], [1, 1, 1], [2, 1, 1], [1, 2, 1], [1, 1, 2], [1, 1, 0], [0, 1, 1], [1, 0, 1]], float)
W /= W.sum(1, keepdims=True)
worst = []
for clip in clips:
    t1 = src.clip_times(clip)[-1]
    for t in np.arange(0, t1 + 1e-6, 0.1):
        ps = [p for p, _ in src.skinned_positions(src.world(src.sample(clip, t)))]
        pc = [p for p, _ in cand.skinned_positions(cand.world(cand.sample(clip, t)))]
        samp = np.concatenate([np.einsum('sk,fkc->fsc', W, P[T]).reshape(-1, 3) for P, T in zip(pc, TC)])
        tree = cKDTree(samp)
        for k, (P, T) in enumerate(zip(ps, TS)):
            used = np.unique(T); d, _ = tree.query(P[used])
            for i in np.argsort(-d)[:3]:
                worst.append((d[i], clip, round(t, 2), k, int(used[i]), names.get(int(vpart[k][used[i]]), '?'), P[used[i]].round(3)))
worst.sort(key=lambda x: -x[0])
print('WORST (mm, clip, t, prim, vertex, part, posed position)')
seen = set()
for w in worst[:60]:
    if (w[3], w[4]) in seen:
        continue
    seen.add((w[3], w[4])); print(f'  {w[0] * 1000:6.1f} {w[1]:12s} {w[2]:5} prim {w[3]} v {w[4]:5d} {w[5]:10s} {w[6]}')
