"""Where a clip's collapsed faces are at a time: rest-space centroids binned. Args: glb clip t"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
m = Model(Glb(sys.argv[1])); doc = m.glb.json
names = [doc['nodes'][j]['name'] for j in doc['skins'][0]['joints']]
Rs = m.skinned_positions(m.world({}))
rest = np.concatenate([r[0] for r in Rs]); offs = np.cumsum([0] + [len(r[0]) for r in Rs])
T = np.concatenate([np.asarray(r[1]).reshape(-1, 3) + o for r, o in zip(Rs, offs)])
J = np.concatenate([p['joints'] for p in m.primitives]); W = np.concatenate([p['weights'] for p in m.primitives])
clip = sys.argv[2]
def tri(P):
    n = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]]); return n, np.linalg.norm(n, axis=1) / 2
n0, a0 = tri(rest); ok = a0 > 1e-9
ts = [float(x) for x in sys.argv[3:]] or list(m.clip_times(clip)[::3])
fw = np.zeros((len(T), len(names)))
for k in range(J.shape[1]):
    for c in range(3): np.add.at(fw, (np.arange(len(T)), J[T[:, c], k]), W[T[:, c], k])
for t in ts:
    world = m.world(m.sample(clip, t)); P = np.concatenate([r[0] for r in m.skinned_positions(world)])
    pal = world[m.joints] @ m.inverse_binds
    nr = np.einsum('fij,fj->fi', np.einsum('fb,bij->fij', fw / 3, pal[:, :3, :3]), n0)
    n, a = tri(P)
    d = (n * nr).sum(1) / np.maximum(np.linalg.norm(n, axis=1) * np.linalg.norm(nr, axis=1), 1e-12)
    badA = ok & (a < 0.2 * a0); badF = ok & (d < 0)
    bad = badA | badF
    c = rest[T[bad]].mean(1)
    print(f't={t:.2f} bad {bad.sum()} area {badA.sum()} flip {badF.sum()}')
    if bad.sum():
        # by simple clusters
        import collections
        key = collections.Counter((round(float(x) * 12) / 12, round(float(y - 1.109) * 12) / 12, round(float(z) * 12) / 12) for x, y, z in c)
        print('  ', [(tuple(round(q, 2) for q in k), v) for k, v in key.most_common(12)])
    top = np.argsort(-fw[bad].sum(0))[:6]; print('   bones', [(names[i], round(float(fw[bad].sum(0)[i]), 1)) for i in top])
