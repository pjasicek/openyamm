"""Where a clip's collapsed faces sit: rest centroids. Args: glb clip time [region substring]"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
m = Model(Glb(sys.argv[1])); clip, t = sys.argv[2], float(sys.argv[3])
doc = m.glb.json
names = [doc['nodes'][j]['name'] for j in doc['skins'][0]['joints']]
world = m.world(m.sample(clip, t))
pal = world[m.joints] @ m.inverse_binds
for pr, (rest, T), (P, _) in zip(m.primitives, m.skinned_positions(m.world({})), m.skinned_positions(world)):
    T = np.asarray(T).reshape(-1, 3)
    n0 = np.cross(rest[T[:, 1]] - rest[T[:, 0]], rest[T[:, 2]] - rest[T[:, 0]])
    a0 = np.linalg.norm(n0, axis=1) / 2
    n = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]]); a = np.linalg.norm(n, axis=1) / 2
    J, W = pr['joints'], pr['weights']
    fw = np.zeros((len(T), len(names)))
    for k in range(J.shape[1]):
        for c in range(3):
            np.add.at(fw, (np.arange(len(T)), J[T[:, c], k]), W[T[:, c], k])
    blend = np.einsum('fb,bij->fij', fw / 3, pal[:, :3, :3])
    nr = np.einsum('fij,fj->fi', blend, n0)
    d = (n * nr).sum(1) / np.maximum(np.linalg.norm(n, axis=1) * np.linalg.norm(nr, axis=1), 1e-16)
    bad = (a0 > 1e-9) & ((a < 0.2 * a0) | (d < 0))
    print('prim', len(T), 'bad', bad.sum(), 'areas small', (a < 0.2 * a0).sum(), 'flip', (d < 0).sum())
    c = rest[T[bad]].mean(1)
    dom = fw[bad].argmax(1)
    for ce, b, r in list(zip(c, dom, a[bad] / a0[bad]))[:int(sys.argv[4]) if len(sys.argv) > 4 else 14]:
        print('  ', np.round(ce, 3), names[b], round(float(r), 3))
