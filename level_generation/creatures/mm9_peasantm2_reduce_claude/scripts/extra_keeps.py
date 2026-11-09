#!/usr/bin/env python3
"""PeasantM2 extra keep sets, carried from PeasantM2d's reduction (same body; read-only from ../mm9_peasantm2d_reduce_claude/work):
- keep_shoulder.npy: every face touching a vertex dominated by a Clavicle or UpperArm joint (the jitter gate's shoulder-skin sample);
- part 4 (the Meshy forearm stubs inside the sleeves: a cut stub root-lifted in M2d's b60);
- hip contact: M2d's keep_h minus its shoulder set and part 4 (trousers/skirt faces at the corpse's hip that cover the Dead/Death
  see-through sliver at the belt), mapped by rest centroid (<= 1 mm) onto PeasantM2's faces.
Writes work/keep_shoulder.npy, work/keep_stub.npy, work/keep_hip.npy, work/keep_h.npy (union)."""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_peasantm2.glb', 'PeasantM2')
PR = ['PeasantM2', 'Pm2Torso_A', 'Pm2Head']
g = np.load(HERE / 'work' / 'glb_parts.npz'); part = g['part']; jn = [str(x) for x in g['jnames']]
offs = g['voff']
P = np.concatenate([D[k]['P'] for k in PR]); T = np.concatenate([D[k]['T'] + offs[i] for i, k in enumerate(PR)])
J = np.concatenate([D[k]['J'] for k in PR]); W = np.concatenate([D[k]['W'] for k in PR])
dom = J[np.arange(len(J)), W.argmax(1)]
sh = np.array([('Clavicle' in n or 'UpperArm' in n) for n in jn])
shv = sh[dom]
keep_sh = shv[T].any(1)
stub = part == 4
M = HERE.parent / 'mm9_peasantm2d_reduce_claude' / 'work'
mg = np.load(M / 'glb_parts.npz'); mh = np.load(M / 'keep_h.npy'); ms = np.load(M / 'keep_shoulder.npy')
hip_m = mh & ~ms & (mg['part'] != 4)
print('M2d keep_h', int(mh.sum()), 'shoulder', int(ms.sum()), 'hip-only', int(hip_m.sum()), 'parts', np.unique(mg['part'][hip_m], return_counts=True))
d, nn = cKDTree(g['cen']).query(mg['cen'][hip_m])
ok = d < 1e-3
keep_hip = np.zeros(len(T), bool); keep_hip[nn[ok]] = True
print('hip mapped', int(ok.sum()), 'of', int(hip_m.sum()), 'max d', d.max().round(6), 'parts', np.unique(part[keep_hip], return_counts=True))
# sanity: M2d shoulder set vs ours by centroid
d2, nn2 = cKDTree(g['cen']).query(mg['cen'][ms]); print('M2d shoulder mapped', int((d2 < 1e-3).sum()), 'of', int(ms.sum()), '; ours', int(keep_sh.sum()))
for name, arr in (('keep_shoulder', keep_sh), ('keep_stub', stub), ('keep_hip', keep_hip), ('keep_h', keep_sh | stub | keep_hip)):
    np.save(HERE / 'work' / f'{name}.npy', arr); print(name, int(arr.sum()))
