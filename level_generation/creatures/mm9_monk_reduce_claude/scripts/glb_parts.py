#!/usr/bin/env python3
"""Per-face labels of the installed LOD0 (before/mm9_monk.glb) from the creature project's final textured mesh
(../mm9_monk_claude/work/uv_tex.npz: part per vertex, `inner` per face = hood lining, sleeve cups, hem cap).
tweak.py moved the waist/belt/sleeves after the UVs, so faces are matched by their UV triple per material (UVs are
unchanged); the few UV-ambiguous faces (degenerate or repeated) by nearest centroid among the UV matches.
Writes work/glb_parts.npz: per GLB face (Monk_A primitive, then MonkHead) mat, part, inner, src npz face, centroid (GLB rest)."""
import sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
doc, binary, nd, D = glbio.load(sys.argv[1] if len(sys.argv) > 1 else HERE / 'before' / 'mm9_monk.glb')
d = np.load(HERE.parent / 'mm9_monk_claude' / 'work' / 'uv_tex.npz', allow_pickle=True)
uv = d['uv'] * [1, -1] + [0, 1]; tri, mat = d['tri'], d['mat']
co = np.c_[d['co'][:, 0], d['co'][:, 2], -d['co'][:, 1]]          # npz (Blender) -> glTF
names = [str(x) for x in d['names']]; fpart = d['comp'][tri[:, 0]]
out = dict(mat=[], part=[], inner=[], src=[], cen=[])
for k, name in enumerate(['Monk_A', 'MonkHead']):
    U, T, P = D[name]['UV'], D[name]['T'], D[name]['P']
    idx = {}
    for f in np.where(mat == k)[0]:
        idx.setdefault(tuple(sorted(map(tuple, np.round(uv[tri[f]], 4)))), []).append(f)
    gc = P[T].mean(1); multi = 0
    for i, t in enumerate(T):
        c = idx[tuple(sorted(map(tuple, np.round(U[t], 4))))]
        if len(c) > 1:
            multi += 1
            # glTF is the mirrored export: compare |x|, y, z
            q = np.abs(co[tri[c]].mean(1)) * [1, 0, 0] + co[tri[c]].mean(1) * [0, 1, 1]
            c = [c[int(np.argmin(np.linalg.norm(q - (np.abs(gc[i]) * [1, 0, 0] + gc[i] * [0, 1, 1]), axis=1)))]]
        out['src'].append(c[0])
    out['mat'] += [k] * len(T); out['cen'].append(gc)
    print(name, len(T), 'faces, UV-ambiguous', multi)
src = np.array(out['src']); cen = np.vstack(out['cen'])
part = fpart[src]; inner = d['inner'][src]; matg = np.array(out['mat'])
for i, n in enumerate(names):
    s = part == i; print(f'{n:6s} {s.sum():6d} inner {inner[s].sum():5d}')
np.savez(HERE / 'work' / 'glb_parts.npz', mat=matg, part=part, inner=inner, src=src, cen=cen, names=np.array(names))
