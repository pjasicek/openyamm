"""Neck/head and feet deformation per clip at 48 fps: edge ratio p1/min and triangles whose normal turned > 120 deg
against the body-relative bind normal (folds). Region by bind distance to joints. Usage: region_gate.py <glb>"""
import sys
import numpy as np
sys.path.insert(0, '/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/floor')
from glb_pose import Glb, Model


def merged(model):
    """all LOD0 primitives of a Model as one: (prim dict with positions/joints/weights/triangles, posed(world))"""
    ps = model.primitives
    off = np.cumsum([0] + [len(p['positions']) for p in ps])
    prim = {'positions': np.concatenate([p['positions'] for p in ps]),
            'joints': np.concatenate([p['joints'] for p in ps]),
            'weights': np.concatenate([p['weights'] for p in ps]),
            'triangles': np.concatenate([p['triangles'] + o for p, o in zip(ps, off)])}

    def posed(W):
        return np.concatenate([q for q, _ in model.skinned_positions(W)])
    return prim, posed

m = Model(Glb(sys.argv[1])); N = m.glb.json['nodes']
idx = {N[j]['name']: j for j in m.joints}
pr, posed = merged(m); tri = pr['triangles']
W0 = m.world({}); P0 = posed(W0)
regions = {'neck_head': (['XneckA', 'Xheadpiv', 'Xhead'], 0.06), 'feet': (['Xtoe', 'Xtoe01'], 0.045)}
E = np.unique(np.sort(np.concatenate([tri[:, [0, 1]], tri[:, [1, 2]], tri[:, [2, 0]]]), axis=1), axis=0)
def nrm(P):
    n = np.cross(P[tri[:, 1]] - P[tri[:, 0]], P[tri[:, 2]] - P[tri[:, 0]])
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
n0 = nrm(P0)
masks = {}
for r, (bones, rad) in regions.items():
    d = np.min([np.linalg.norm(P0 - W0[idx[b]][:3, 3], axis=1) for b in bones], axis=0)
    vm = d < rad
    masks[r] = (vm[E].all(1), vm[tri].all(1))
for clip in m.clips:
    T = m.clip_times(clip)[-1]
    out = {r: [[], [], 0] for r in regions}
    for k in range(int(T * 48) + 1):
        W = m.world(m.sample(clip, k / 48)); P = posed(W)
        L0 = np.linalg.norm(P0[E[:, 0]] - P0[E[:, 1]], axis=1); L = np.linalg.norm(P[E[:, 0]] - P[E[:, 1]], axis=1)
        ratio = L / np.maximum(L0, 1e-9)
        # local rotation of each triangle: compare with the dominant-joint rotation applied to the bind normal
        pal = W[m.joints] @ m.inverse_binds
        dj = pr['joints'][np.arange(len(P0)), pr['weights'].argmax(1)]
        Rv = pal[dj][:, :3, :3]
        Rt = Rv[tri[:, 0]]
        exp = np.einsum('tij,tj->ti', Rt, n0); exp /= np.linalg.norm(exp, axis=1, keepdims=True)
        flip = (nrm(P) * exp).sum(1) < -0.5
        for r, (em, tm) in masks.items():
            out[r][0].append(np.percentile(ratio[em], 1)); out[r][1].append(ratio[em].min())
            out[r][2] = max(out[r][2], int(flip[tm].sum()))
    print(f'{clip:12s} ' + '  '.join(f'{r}: p1 {min(v[0]):.2f} min {min(v[1]):.2f} folded {v[2]}' for r, v in out.items()))
