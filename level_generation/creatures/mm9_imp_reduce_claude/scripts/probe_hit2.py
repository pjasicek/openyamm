import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, '../claude_shared/floor'); sys.path.insert(0, 'scripts')
from glb_pose import Glb, Model
import bglbio as gb
d, b = gb.read('/home/pjasicek/github/OpenYAMM/assets_source/worlds/mm9/models/mm9_imp_trident.glb')
n = next(n for n in d['nodes'] if 'mesh' in n); p = gb.prims(d, b, n['mesh'])[0]; TP = p['POSITION'].astype(float); TT = p['T']
def wn(pts, X, T):
    a, b_, c = X[T[:, 0]][None] - pts[:, None], X[T[:, 1]][None] - pts[:, None], X[T[:, 2]][None] - pts[:, None]
    la, lb, lc = [np.linalg.norm(v, axis=-1) for v in (a, b_, c)]
    num = np.einsum('pfi,pfi->pf', a, np.cross(b_, c)); den = la * lb * lc + np.einsum('pfi,pfi->pf', a, b_) * lc + np.einsum('pfi,pfi->pf', b_, c) * la + np.einsum('pfi,pfi->pf', c, a) * lb
    return np.arctan2(num, den).sum(1) / (2 * np.pi)
for f in sys.argv[1:]:
    m = Model(Glb(f)); names = [x.get('name') for x in m.glb.json['nodes']]; jn = [names[j] for j in m.joints]
    w = m.world(m.sample('Hit2', 32 / 48)); sp = m.skinned_positions(w)
    node = m.primitives[0]['node']; K = [k for k, pp in enumerate(m.primitives) if pp['node'] == node]
    X = sp[K[0]][0]; T = sp[K[0]][1]; pr = m.primitives[K[0]]
    dom = np.array(jn)[pr['joints'][np.arange(len(X)), pr['weights'].argmax(1)]]
    hand = np.array(['L Hand' in x or 'L Finger' in x for x in dom])
    Y = (np.c_[TP, np.ones(len(TP))] @ w[names.index('Yweaponbase')].T)[:, :3]
    ax = np.linalg.svd(TP - TP.mean(0))[2][0]; tt = TP @ ax; e0, e1 = Y[tt.argmin()], Y[tt.argmax()]
    Y = np.vstack([Y, e0 + np.outer(np.linspace(0, 1, 240), e1 - e0)])
    from scipy.spatial import cKDTree
    dd, _ = cKDTree(X[hand]).query(Y)
    print(f, 'min dist trident->L hand verts', round(dd.min() * 100, 2), 'cm; trident pts within 3 cm', int((dd < 0.03).sum()))
    hf = T[hand[T].all(1)]
    close = Y[dd < 0.07]
    if len(close):
        print("  shaft/trident points within 7 cm of the left hand:", len(close), "winding number vs the whole body mesh: max", np.round(np.abs(wn(close, X, T)).max(), 3))
