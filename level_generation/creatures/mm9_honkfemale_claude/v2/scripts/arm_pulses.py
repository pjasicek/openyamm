#!/usr/bin/env python3
"""Smooth arm corrections for the fall (Honk night pass 2, 2026-10-31), on an unmirrored GLB after the floor pass.

A pulse is one constant rotation of the upper arm and one of the forearm, each in its parent's frame, weighted by a smoothstep up from t0 to t1 and down
from t2 to t3 over a clip, so nothing is solved per key and the arm keeps MM9's motion plus one slow lean. hand_rest.py cannot do this: it casts along a
horizontal direction, and on a corpse the belly faces up (it read 26 cm for a 3 cm contact).

  solve: arm_pulses.py solve <in glb> <pulses json>   finds each pulse's rotations and writes them into the json
  apply: arm_pulses.py apply <in glb> <out glb> <pulses json>

Pulses json: [{"name", "clip": "Death", "times": [t0, t1, t2, t3], "dead": true (hold through the Dead clip, t2/t3 ignored), "sides": ["R"],
"test": [{"side": "R", "against": ["torso", "Lsleeve"]}], "margin": 0.01, "weight": 0.02}]
The cost is the squared depth of that side's hand and forearm vertices behind the surfaces, at keys inside [t1, t2], plus `weight` x squared angle: the least
turn that clears. Surfaces are the outer faces (outer_surface.py) of the torso and robe, or of the other sleeve."""
import json, sys
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[3] / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE.parents[3] / 'claude_shared')); sys.path.insert(0, str(HERE.parent))
from glb_pose import Glb, Model, quaternion_matrix, matrix_quaternion
from outer_surface import outer_faces
from detached_parts_audit import closest_on_triangles

mode = sys.argv[1]


def rv_quat(r):
    a = np.linalg.norm(r)
    if a < 1e-9:
        return np.array([0, 0, 0, 1.0])
    return np.r_[np.sin(a / 2) * r / a, np.cos(a / 2)]


def qmul(p, q):
    x1, y1, z1, w1 = p; x2, y2, z2, w2 = q
    return np.array([w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2, w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2])


def weight(p, t, clip):
    if clip == 'Dead':
        return 1.0 if p.get('dead') else 0.0
    if clip != p['clip']:
        return 0.0
    t0, t1, t2, t3 = p['times']
    up = np.clip((t - t0) / (t1 - t0), 0, 1)
    mix = p.get('soft', 0.0)          # 0 smoothstep .. 1 linear: a lower peak rate over the same window
    up = mix * up + (1 - mix) * up * up * (3 - 2 * up)
    if p.get('dead'):
        return float(up)
    dn = np.clip((t3 - t) / (t3 - t2), 0, 1)
    return float(up * dn * dn * (3 - 2 * dn))


class Scene:
    def __init__(self, path):
        self.g = Glb(path); self.m = Model(self.g); m = self.m; d = m.glb.json
        self.nd = [n.get('name', '') for n in d['nodes']]
        self.names = [d['nodes'][j]['name'] for j in d['skins'][0]['joints']]
        ps = [p for p in m.primitives if p['skinned']]
        off = np.cumsum([0] + [len(p['positions']) for p in ps])
        self.T = np.vstack([p['triangles'] + off[i] for i, p in enumerate(ps)])
        self.J = np.vstack([p['joints'] for p in ps]); self.W = np.vstack([p['weights'] for p in ps]); self.P = np.vstack([p['positions'] for p in ps])
        names = self.names
        arm = {s: [i for i, n in enumerate(names) if f' {s} ' in n and any(k in n for k in ('UpperArm', 'Forearm', 'Hand', 'Finger', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky', 'Clavicle'))] for s in 'LR'}
        hair = [i for i, n in enumerate(names) if 'Ponytail' in n or n.startswith('Y')]
        fw = np.zeros((len(self.T), len(names)))
        for k in range(self.J.shape[1]):
            for c in range(3):
                np.add.at(fw, (np.arange(len(self.T)), self.J[self.T[:, c], k]), self.W[self.T[:, c], k])
        isa = {s: fw[:, arm[s]].sum(1) > 1.5 for s in 'LR'}
        ish = fw[:, hair].sum(1) > 1.0
        head = fw[:, names.index('Bip01 Head')] > 1.5
        rest = self.skin(m.world({}))
        self.surf = {'torso': np.where(~isa['L'] & ~isa['R'] & ~ish & ~head)[0], 'Lsleeve': np.where(isa['L'])[0], 'Rsleeve': np.where(isa['R'])[0]}
        self.surf = {k: v[outer_faces(rest, self.T, v)] for k, v in self.surf.items()}
        dom = self.J[np.arange(len(self.J)), self.W.argmax(1)]
        self.pts = {}
        for s in 'LR':
            ids = [names.index(n) for n in names if f' {s} ' in n and any(k in n for k in ('Forearm', 'Hand', 'Finger', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky'))]
            self.pts[s] = np.where(np.isin(dom, ids))[0]

    def skin(self, world):
        m = self.m
        pal = world[m.joints] @ m.inverse_binds
        h = np.c_[self.P, np.ones(len(self.P))]
        b = np.einsum('vk,vkij->vij', self.W, pal[self.J])
        return np.einsum('vij,vj->vi', b, h)[:, :3]

    def posed(self, clip, t, pulses, extra=None):
        local = self.m.sample(clip, float(t))
        local = {k: [x.copy() for x in v] for k, v in local.items()}
        for p, rot in pulses:
            w = weight(p, t, clip)
            if w == 0:
                continue
            for s in p['sides']:
                for b, key in (('UpperArm', 'u'), ('Forearm', 'f')):
                    n = self.nd.index(f'Bip01 {s} {b}')
                    tr = local.setdefault(n, [x.copy() for x in self.m.rest[n]])
                    tr[1] = qmul(rv_quat(np.array(rot[s + key]) * w), tr[1])
        return self.skin(self.m.world(local))

    def depth(self, x, side, against):
        out = 0.0
        q = self.pts[side]
        for a in against:
            ft = x[self.T[self.surf[a]]]
            c = ft.mean(1)
            n = np.cross(ft[:, 1] - ft[:, 0], ft[:, 2] - ft[:, 0])
            n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
            _, near = cKDTree(c).query(x[q], k=12)
            pts = np.repeat(x[q], 12, 0)
            qq, _ = closest_on_triangles(pts, ft[near.ravel(), 0], ft[near.ravel(), 1], ft[near.ravel(), 2])
            dd = np.linalg.norm(pts - qq, axis=1).reshape(near.shape)
            b = dd.argmin(1); r = np.arange(len(q))
            s = ((x[q] - qq.reshape(*near.shape, 3)[r, b]) * n[near[r, b]]).sum(1)
            ins = (s < 0) & (dd[r, b] < 0.13)
            if ins.any():
                out = max(out, float(-s[ins].min()))
        return out


if mode == 'solve':
    S = Scene(sys.argv[2])
    spec = sys.argv[3]
    P = json.load(open(spec))
    done = []
    for p in P:
        if p.get('fixed'):
            done.append((p, p['rot']))
            continue
        keys = np.linspace(p['times'][1], p['times'][2], 5) if not p.get('dead') else np.r_[np.linspace(p['times'][1], S.m.clip_times(p['clip'])[-1], 4)]
        margin = p.get('margin', 0.01); lam = p.get('weight', 0.02)
        order = [s + k for s in p['sides'] for k in ('u', 'f')]

        def unpack(v):
            return {k: v[i * 3:i * 3 + 3].tolist() for i, k in enumerate(order)}

        def report(rot):
            return [round(max(S.depth(S.posed(p['clip'], t, done + [(p, rot)]), c['side'], c['against']) for c in p['test']) * 100, 2) for t in keys]

        def cost(v):
            rot = unpack(v)
            c = 0.0
            for t in keys:
                x = S.posed(p['clip'], t, done + [(p, rot)])
                for k in p['test']:
                    d = S.depth(x, k['side'], k['against'])
                    c += (max(d + (margin if d > 0 else 0), 0) * 100) ** 2
            return c + lam * 1000 * float((v ** 2).sum())

        print(p['name'], 'before', report({k: [0, 0, 0] for k in order}), flush=True)
        x0 = np.array([c for k in order for c in p.get('init', {}).get(k, [0, 0, 0])], float)
        r = minimize(cost, x0, method='Powell', options={'maxfev': p.get('evals', 260), 'xtol': 0.003, 'ftol': 0.005, 'direc': np.eye(len(order) * 3) * 0.08})
        rot = unpack(r.x)
        print(p['name'], 'after', report(rot), 'deg', {k: round(float(np.degrees(np.linalg.norm(v))), 1) for k, v in rot.items()}, 'cost', round(float(r.fun), 2), flush=True)
        p['rot'] = rot
        done.append((p, rot))
    json.dump(P, open(spec, 'w'), indent=1)
else:
    src, dst, spec = sys.argv[2:5]
    g = Glb(src); m = Model(g); d = g.json
    nd = [n.get('name', '') for n in d['nodes']]
    P = json.load(open(spec))
    for clip in sorted({p['clip'] for p in P} | ({'Dead'} if any(p.get('dead') for p in P) else set())):
        an = d['animations'][m.clips[clip]]
        for s in 'LR':
            for b, key in (('UpperArm', 'u'), ('Forearm', 'f')):
                n = nd.index(f'Bip01 {s} {b}')
                ps = [p for p in P if s in p['sides'] and (p['clip'] == clip or (clip == 'Dead' and p.get('dead')))]
                if not ps:
                    continue
                c = next(c for c in an['channels'] if c['target']['node'] == n and c['target']['path'] == 'rotation')
                sm = an['samplers'][c['sampler']]
                T = g.accessor(sm['input'])[:, 0].astype(np.float64)
                Q = g.accessor(sm['output']).astype(np.float64)
                if clip == 'Dead' or len(T) < 3:
                    pass
                out = []
                for t, q in zip(T, Q):
                    q = q / np.linalg.norm(q)
                    for p in ps:
                        q = qmul(rv_quat(np.array(p['rot'][s + key]) * weight(p, float(t), clip)), q)
                    out.append(q / np.linalg.norm(q))
                sm['output'] = g.append_accessor(np.array(out), 'VEC4')
    g.write(dst)
    print('PULSES', dst)
