#!/usr/bin/env python3
"""Two keep sets after the d r60 gates (per GLB face, work/<name>.npy):
shoulder.npy: robe faces with a vertex weighted mostly (> WSH) to a Clavicle or UpperArm (the jitter gate's shoulder-skin set:
  its Cast L 95th percentile went 0.53 -> 2.14 mm/f2 with fewer vertices there);
boottop.npy: boot faces within RB m of another body-set piece's surface at bind, and the shaft top (above BOOT_TOP m) (detached_parts_audit's bind gap of the right
  boot went 0 -> 3.1 cm when its top was cut).
tube.npy: every face of the robe tube piece.
Usage: extra_keeps.py <sets tag>"""
import json, os, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
WSH = float(os.environ.get('WSH', '0.5')); RB = float(os.environ.get('RB', '0.015'))
doc, b, nd, D = glbio.load(HERE / 'before' / 'mm9_honkm.glb', 'HonkM')
s = np.load(HERE / 'work' / f'glb_sets_{sys.argv[1]}.npz'); C = json.load(open(HERE / 'work' / 'classes.json'))['names']
names = [doc['nodes'][j]['name'] for j in doc['skins'][nd['skin']]['joints']]
P, T, J, W = (D['HonkM_A'][k] for k in 'PTJW'); n = len(T); cls = s['cls'][:n]
sh = np.array([('Clavicle' in x or 'UpperArm' in x) for x in names])
vw = (W * sh[J]).sum(1)
shoulder = (cls == C.index('robe')) & (vw[T] > WSH).any(1)
boot = cls == C.index('boots')
k = 10; i, j = np.meshgrid(np.arange(k + 1), np.arange(k + 1)); m = i + j <= k
bw = np.stack([i[m], j[m], k - i[m] - j[m]], 1) / k
surf = np.einsum('sk,fkc->fsc', bw, P[T[~boot]]).reshape(-1, 3)      # the other pieces' surfaces, densely sampled
d = cKDTree(surf).query(P[T[boot]].reshape(-1, 3))[0].reshape(-1, 3).min(1)
print('boot to body surface min mm', round(float(d.min()) * 1000, 2))
boottop = np.zeros(n, bool); boottop[np.flatnonzero(boot)[d < RB]] = True
# the boots are 3 cm from every other piece at bind (they hang inside the robe tube), so the audit's contact is the shaft top:
# keep the boot faces above BOOT_TOP m (the shaft was cut with a plane at 0.28 m, robe_lining.py)
boottop |= boot & (P[T][:, :, 1].max(1) > float(os.environ.get('BOOT_TOP', '0.22')))
# tube.npy: the robe tube piece (the audit's 'body', the boots' holder): its cut moved the right boot's bind gap 0 -> 3.1 cm
from make_sets_util import pieces  # noqa: E402
_, _, fl = pieces(P, T)
robe = np.isin(cls, [C.index('robe'), C.index('lined'), C.index('lining')])
low = fl[np.argmin(np.where(robe, P[T][:, :, 1].min(1), 9))]
tube = robe & (fl == low)
for nm, x in (('shoulder', shoulder), ('boottop', boottop), ('tube', tube)):
    out = np.zeros(len(s['cls']), bool); out[:n] = x; np.save(HERE / 'work' / f'{nm}.npy', out)
    print(nm, int(x.sum()), 'free before', int((x & ~s['keep'][:n]).sum()))
