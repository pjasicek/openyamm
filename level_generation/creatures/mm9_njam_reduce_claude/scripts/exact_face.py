#!/usr/bin/env python3
"""Exactness check of the kept parts (Njam copy of PeasantM3's): every installed triangle of the head skin (part 20: face, ears,
scalp, neck tube), the hair lip (23), the belt (9) and buckle pieces (10), and every face kept by the set (work/glb_sets_<SET>.npz
keep) is present in the candidate with byte-identical corners (position, normal, UV, joints, weights), same winding. Also: every
candidate vertex is an installed vertex. Usage: [SET=a] exact_face.py <candidate.glb>"""
import sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import bglbio  # noqa: E402
import os
g = np.load(HERE / 'work' / 'glb_parts.npz'); S = np.load(HERE / 'work' / f"glb_sets_{os.environ.get('SET', 'a')}.npz")


def load(p):
    doc, b = bglbio.read(p); node = next(n for n in doc['nodes'] if n.get('name') == 'Njam' and 'mesh' in n)
    return bglbio.prims(doc, b, node['mesh'])


def rows(pr):
    a = [pr[k].astype(np.float64).reshape(len(pr['POSITION']), -1) for k in ('POSITION', 'NORMAL', 'TEXCOORD_0', 'JOINTS_0', 'WEIGHTS_0')]
    return np.concatenate(a, 1)


src, cand = load(HERE / 'before' / 'mm9_njam.glb'), load(sys.argv[1])
off = np.cumsum([0] + [len(p['T']) for p in src])
for k in range(3):
    R0, R1 = rows(src[k]), rows(cand[k])
    key0 = {r.tobytes(): i for i, r in enumerate(R0)}
    m = np.array([key0.get(r.tobytes(), -1) for r in R1])
    print(src[k]['material'], 'candidate vertices not installed:', int((m < 0).sum()), 'of', len(m))
    C = set(map(tuple, m[cand[k]['T']].tolist()))
    C |= {(t[1], t[2], t[0]) for t in C} | {(t[2], t[0], t[1]) for t in C}
    for label, sel in (('head skin 20 + lip 23 + belt 9 + buckle 10', np.isin(g['part'][off[k]:off[k + 1]], (20, 23, 9, 10))),
                       ('every kept face of the set', S['keep'][off[k]:off[k + 1]])):
        T0 = src[k]['T'][sel]
        miss = sum(tuple(t) not in C for t in T0.tolist())
        print(f'  {label}: {len(T0)} installed triangles, missing in candidate {miss}')
