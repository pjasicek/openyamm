#!/usr/bin/env python3
"""Per-face and per-vertex labels of the installed LOD0 (before/mm9_peasantf4.glb, node PeasantF4; primitives PeasantF4_A body,
PeasantF4Head head set) from the PeasantF4 build's final asm: ../mm9_peasantf4_claude/work/uv_tex2.npz (co, tri, uv, orig = asm row,
comp, inner) and work/asm_frozen.npz (f4_rim, f4_twin_face, f4_twin_v, f4_param). The runtime GLB = the uv npz mirrored and y-up:
glTF (x, y, z) = (-X, Z, -Y) (checked: 0 mm). GLB vertices are matched to uv vertices by position + UV.
Writes work/glb_labels.npz: per GLB face (prims concatenated): mat, comp, inner, rim, lining (twin outer GLB face or -1);
per GLB vertex (concatenated): asm, comp, param, twin (lining vertex -> outer asm vertex)."""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as g  # noqa: E402
SRC = HERE.parent / 'mm9_peasantf4_claude' / 'work'
d, b = g.read(HERE / 'before' / 'mm9_peasantf4.glb')
node = next(n for n in d['nodes'] if n.get('name') == 'PeasantF4' and 'mesh' in n)
prims = g.prims(d, b, node['mesh'])
U = np.load(SRC / 'uv_tex2.npz'); A = np.load(SRC / 'asm_frozen.npz')
co = U['co']; X = np.c_[-co[:, 0], co[:, 2], -co[:, 1]]
names = [str(x) for x in U['names']]
uvs = U['uv']
out = dict(mat=[], comp=[], inner=[], rim=[], fasm=[], vasm=[], vcomp=[], vparam=[], vtwin=[], voff=[])
# asm face lookup by sorted vertex triple
akey = {tuple(sorted(t)): i for i, t in enumerate(A['tri'])}
voff = 0
for k, pr in enumerate(prims):
    P = pr['POSITION'].astype(np.float64); UV = pr['TEXCOORD_0'].astype(np.float64)
    sel = np.where(U['mat'] == k)[0]; uvv = np.unique(U['tri'][sel])
    # GLB v = 1 - npz v, or the same: try both
    best = None
    for flip in (False, True):
        uu = uvs[uvv].copy()
        if flip: uu[:, 1] = 1 - uu[:, 1]
        dd, j = cKDTree(np.c_[X[uvv], uu * 0.01]).query(np.c_[P, UV * 0.01])
        if best is None or dd.max() < best[0]: best = (dd.max(), uvv[j], flip)
    print(pr['material'], 'match max', best[0], 'flip v', best[2])
    assert best[0] < 1e-5
    vu = best[1]; va = U['orig'][vu]
    T = pr['T']; fa = []
    for t in va[T]:
        fa.append(akey.get(tuple(sorted(t)), -1))
    fa = np.array(fa)
    fcomp = U['comp'][vu[T[:, 0]]]
    print('  faces', len(T), 'unmatched to asm', int((fa < 0).sum()), 'comps', {names[c]: int((fcomp == c).sum()) for c in np.unique(fcomp)})
    out['mat'].append(np.full(len(T), k)); out['comp'].append(fcomp)
    out['inner'].append(np.where(fa >= 0, A['f4_inner'][np.maximum(fa, 0)], False))
    out['rim'].append(np.where(fa >= 0, A['f4_rim'][np.maximum(fa, 0)], False))
    out['fasm'].append(fa); out['vasm'].append(va); out['vcomp'].append(U['comp'][vu]); out['vparam'].append(A['f4_param'][va])
    out['vtwin'].append(A['f4_twin_v'][va]); out['voff'].append(np.full(len(P), voff)); voff += len(P)
res = {k: np.concatenate(v) for k, v in out.items()}
res['names'] = np.array(names)
np.savez(HERE / 'work' / 'glb_labels.npz', **res)
for c, n in enumerate(names):
    s = res['comp'] == c
    print(f'{n:8s} faces {s.sum():5d} inner {int(res["inner"][s].sum()):4d} rim {int(res["rim"][s].sum()):4d}')
