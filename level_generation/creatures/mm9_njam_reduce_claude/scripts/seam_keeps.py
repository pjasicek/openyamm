#!/usr/bin/env python3
"""Two more exact sets (b55 close-up, Baron face-front shot at 1.5x): the collar V at the throat showed a larger grey notch, and the
fur mantle's lower front edge a light wedge (larger smooth-shaded triangles over the rim fold).
- neck seam (NECK m, default 0.015): body faces with a vertex within NECK of a head-set vertex (where the head's neck tube
  meets the shirt collar; the brief keeps the neck seam exact);
- mantle rim (RIM rings, default 2): mantle (part 8) faces within RIM face rings of the mantle sheet's open border;
- throat (THROAT=1): the shirt's front centre seam under the collar V (torso faces with |x| < 2 cm, 1.40-1.66 m up, front
  half): the grey notch mark at the V grew when the thin mirror-seam faces there were merged (c55).
Usage: seam_keeps.py <in set tag> <out set tag> -> work/glb_sets_<out>.npz"""
import os, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
src, dst = sys.argv[1:3]
NECK = float(os.environ.get('NECK', '0.015')); RIM = int(os.environ.get('RIM', '2'))
S = dict(np.load(HERE / 'work' / f'glb_sets_{src}.npz')); part = S['part']; mat = S['mat']
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_njam.glb', 'Njam')
PR = ['Njam', 'NjTorso', 'NjHead']; nf = [len(D[k]['T']) for k in PR]; off = np.cumsum([0] + nf)
headv = D['NjHead']['P']; tree = cKDTree(headv)
extra = np.zeros(off[-1], bool)
for k, name in enumerate(PR[:2]):
    P, T = D[name]['P'], D[name]['T']
    d, _ = tree.query(P); near = d < NECK
    extra[off[k]:off[k + 1]] |= near[T].any(1)
print('NECK faces', int(extra.sum()))
k = 1; P, T = D['NjTorso']['P'], D['NjTorso']['T']; sl = slice(off[1], off[2]); m8 = part[sl] == 8
_, wv = np.unique(np.round(P, 6), axis=0, return_inverse=True); wv = wv.ravel(); FT = wv[T]
sub = np.flatnonzero(m8); ed = np.sort(np.vstack([FT[sub][:, [0, 1]], FT[sub][:, [1, 2]], FT[sub][:, [2, 0]]]), 1)
u, c = np.unique(ed, axis=0, return_counts=True)
hot = np.zeros(wv.max() + 1, bool); hot[u[c == 1].ravel()] = True
rim = m8 & hot[FT].any(1)
for _ in range(RIM - 1):
    hot[FT[rim].ravel()] = True; rim = m8 & hot[FT].any(1)
print('RIM faces', int(rim.sum()), 'of mantle', int(m8.sum()))
extra[sl] |= rim
if os.environ.get('THROAT', '0') == '1':
    tc = P[T].mean(1); th = (np.abs(tc[:, 0]) < 0.02) & (tc[:, 1] > 1.40) & (tc[:, 1] < 1.66) & (tc[:, 2] > 0)
    extra[sl] |= th; print('THROAT faces', int(th.sum()))
new = extra & ~S['keep']
S['keep'] = S['keep'] | extra; S['group'] = np.where(S['keep'], 0, S['group'])
np.savez(HERE / 'work' / f'glb_sets_{dst}.npz', **S)
print('SET', dst, 'keep', int(S['keep'].sum()), f'(+{int(new.sum())})')
