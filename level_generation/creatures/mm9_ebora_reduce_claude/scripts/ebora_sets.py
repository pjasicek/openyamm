#!/usr/bin/env python3
"""Face sets in GLB order for mpqem.py (Ebora fix pass, after mm9_giant_reduce_claude/scripts/giant_sets.py): keep and group
from the round-2 masks on work/mesh_in.npz faces (keep_rflfs: face skin, eyes, mouth, horns, fringe/locks with copies, neck,
soles, small pieces, wings, skull cups, forearms, shoulder skin, shoulder drift lock; groups_r: 1 hair shell, 2 hands);
lining = the hair shell's reversed back copies (drop_r), lined = the shell faces they copy (UV-identical pairs).
Usage: ebora_sets.py <keep .npy> <groups .npy> <label>  -> work/glb_sets_<label>.npz"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bglbio as glbio  # noqa: E402
keep_f, grp_f, label = sys.argv[1:4]
d = np.load('work/mesh_in.npz'); cen = d['verts'][d['faces']].mean(1); wuv = d['wuv'].reshape(-1, 3, 2); mat = d['mat']
drop = np.load('work/drop_r.npy')
# originals of the dropped copies: the head face with the same UV triple
key = {}
for i in np.flatnonzero(mat == 1):
    key.setdefault(tuple(sorted(map(tuple, np.round(wuv[i], 6)))), []).append(i)
lined_in = np.zeros(len(cen), bool)
for i in np.flatnonzero(drop):
    others = [j for j in key[tuple(sorted(map(tuple, np.round(wuv[i], 6))))] if j != i]
    assert len(others) == 1; lined_in[others[0]] = True
doc, binary = glbio.read('before/mm9_ebora.glb')
node = next(n for n in doc['nodes'] if n.get('name') == 'Ebora' and 'mesh' in n)
prims = glbio.prims(doc, binary, node['mesh'])
allp = np.concatenate([pr['POSITION'].astype(np.float64) for pr in prims]); allb = np.c_[allp[:, 0], -allp[:, 2], allp[:, 1]]
offset = d['verts'].min(0) - allb.min(0)
gc = np.concatenate([np.c_[pr['POSITION'][:, 0], -pr['POSITION'][:, 2], pr['POSITION'][:, 1]].astype(np.float64)[pr['T']].mean(1) for pr in prims]) + offset
dist, idx = cKDTree(cen).query(gc)
print('MATCH max dist', dist.max(), 'unique', len(np.unique(idx)) == len(idx))
keep, grp = np.load(keep_f)[idx], np.load(grp_f)[idx]
lining, lined = drop[idx], lined_in[idx]
assert not (keep & lining).any()
grp = np.where(lining, 0, grp)
np.savez(f'work/glb_sets_{label}.npz', keep=keep, group=grp, lining=lining, lined=lined)
print('SETS', label, 'keep', int(keep.sum()), 'lining', int(lining.sum()), 'lined', int(lined.sum()),
      'groups', {int(g): int(((grp == g) & ~keep & ~lining).sum()) for g in np.unique(grp)})
