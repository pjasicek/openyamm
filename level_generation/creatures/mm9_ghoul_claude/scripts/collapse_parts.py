"""Which part the collapsed faces of a clip belong to, at its worst frame: front flap, back flap, hands, other skin. Args: glb clip..."""
import json, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
m = Model(Glb(sys.argv[1])); doc = m.glb.json
Rs = m.skinned_positions(m.world({}))
rest = np.concatenate([r[0] for r in Rs]); offs = np.cumsum([0] + [len(r[0]) for r in Rs])
T = np.concatenate([np.asarray(r[1]).reshape(-1, 3) + o for r, o in zip(Rs, offs)])
J = np.concatenate([p['joints'] for p in m.primitives]); W = np.concatenate([p['weights'] for p in m.primitives])
names = [doc['nodes'][j]['name'] for j in doc['skins'][0]['joints']]
D = np.load('work/flap_verts.npz'); LIFT = 1.1093; conv = lambda q: np.c_[q[:, 0], q[:, 2] + LIFT, -q[:, 1]]
fw = np.zeros((len(T), len(names)))
for k in range(J.shape[1]):
    for c in range(3): np.add.at(fw, (np.arange(len(T)), J[T[:, c], k]), W[T[:, c], k])
share = lambda *ns: fw[:, [names.index(n) for n in ns if n in names]].sum(1) / 3
fr = share('Bone01') > 0.15
bk = share('Bone03') > 0.15
hair = (share('Bip01 Spine3') > 0.15) & (share('Bip01 Head') > 0.15)
hand = np.abs(rest[T].mean(1)[:, 0]) > 0.72
def tri(P):
    n = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]]); return n, np.linalg.norm(n, axis=1) / 2
n0, a0 = tri(rest); ok = a0 > 1e-9
rep = json.load(open('review/gates/collapse.json'))
for clip in sys.argv[2:]:
    t = rep[clip]['worst_time']
    world = m.world(m.sample(clip, t)); P = np.concatenate([r[0] for r in m.skinned_positions(world)])
    pal = world[m.joints] @ m.inverse_binds
    nr = np.einsum('fij,fj->fi', np.einsum('fb,bij->fij', fw / 3, pal[:, :3, :3]), n0)
    n, a = tri(P); d = (n * nr).sum(1) / np.maximum(np.linalg.norm(n, axis=1) * np.linalg.norm(nr, axis=1), 1e-12)
    bad = ok & ((a < 0.2 * a0) | (d < 0))
    print(f'{clip:12} t={t:.2f} total {int(bad.sum())}: front flap {int((bad & fr).sum())}, back flap {int((bad & bk).sum())}, hands {int((bad & hand & ~fr & ~bk).sum())}, hair {int((bad & hair).sum())}, other skin {int((bad & ~fr & ~bk & ~hand & ~hair).sum())}')
