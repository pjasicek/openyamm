#!/usr/bin/env python3
"""Fist solve (follow-up 2026-11-11): finger and thumb angles of a closed fist for the grafted Titan hands, found
numerically on the spliced GLB (work/splice_v1.glb: graft rest frames, splice_ttn.py's rotation rule and spread signs
from work/splice_v1.json), so the result drops into finger_poses.json as a named pose.

Per side the hand vertices are split into parts by dominant joint: palm (Hand), Thumb, Index, Middle, Ring, Pinky.
Cost of a pose (angles added to the grafted rest curl, as splice_ttn.py applies them):
- interpenetration: the distal (bone 2-3) vertices of every part against every other part's distal faces or the palm
  (signed distance to the nearest triangle interior by its face normal, as arm_hand_gate.py --exact): the squared
  worst depth per pair beyond 0.1 cm (0.5 cm for a fingertip pressing into the palm, hidden inside the fist);
- fingertips (bone-3 tip vertex) on the palm where a fist puts them: within 1.5 cm of the palm-side vertex under the
  line wrist -> the finger's knuckle at TIP_AT of the way (not merely touching the palm next to the knuckle: a claw);
- thumb: its tip on the OUTSIDE of the index/middle middle phalanges (gap 0.1-0.5 cm), not inside the fist and not
  past the fist's extent (a thumb poking out);
- a weak prior (MCP 70, PIP 85, DIP 25 added to the rest curl: the MPFB distal phalanx is long, a deeper DIP drives
  the tip back through the palm); bounds keep every joint in its human range.
Both sides are solved together with one shared pose (the clips key 'both'), or per side with --per-side.
Usage: fist_solve.py <splice glb> <out json> [--start fist] [--iters 1500] [--per-side]"""
import argparse, json, sys
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import glb_pose as gp
from detached_parts_audit import closest_on_triangles
F = ('Thumb', 'Index', 'Middle', 'Ring', 'Pinky')
TIP_AT = {'Index': 0.5, 'Middle': 0.5, 'Ring': 0.55, 'Pinky': 0.65}   # the short pinky folds nearer its knuckle


def qmul(a, b):
    x1, y1, z1, w1 = a; x2, y2, z2, w2 = b
    return np.array([w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
                     w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2])


def qaxis(axis, deg):
    h = np.radians(deg) / 2; return np.array([*(np.array(axis) * np.sin(h)), np.cos(h)])


class Hand:
    def __init__(self, glb_path, side, signs, clip='Fidget', time=0.34):
        self.g = gp.Glb(glb_path); self.m = gp.Model(self.g); self.side = side; self.signs = signs
        self.names = [n.get('name') for n in self.g.json['nodes']]
        self.base = self.m.sample(clip, time)
        pr = self.m.primitives[0]; jn = [self.names[j] for j in self.m.joints]
        dom = np.array([jn[pr['joints'][v][np.argmax(pr['weights'][v])]] for v in range(len(pr['positions']))])
        part = np.full(len(dom), -1)
        part[dom == f'{side}Hand'] = 0
        for k, f in enumerate(F, 1):
            for j in (1, 2, 3):
                part[dom == f'{side}Hand{f}{j}'] = k
        self.dom = dom
        hv = np.where(part >= 0)[0]
        # skin only the hand's vertices
        self.hv = hv; self.part = part[hv]
        self.P = np.concatenate([pr['positions'][hv], np.ones((len(hv), 1))], 1)
        self.J = pr['joints'][hv]; self.W = pr['weights'][hv]
        tri = pr['triangles']; inh = np.isin(tri, hv).all(1); remap = -np.ones(len(dom), int); remap[hv] = np.arange(len(hv))
        self.tri = remap[tri[inh]]
        tp = self.part[self.tri]
        self.face_part = np.where((tp[:, 0] == tp[:, 1]) | (tp[:, 0] == tp[:, 2]), tp[:, 0], tp[:, 1])
        # distal: bones 2-3 (the webbing and knuckle blends of bone 1 are shared surfaces, not contacts)
        dd = np.array([d[-1] in '23' and 'Hand' in d and d[-2] != 'd' for d in dom[hv]])
        self.distal = dd; self.face_distal = dd[self.tri].all(1)
        self.tipv = {}
        self.rest_q = {n: np.array(self.g.json['nodes'][self.names.index(n)]['rotation'], float)
                       for n in self.names if n and n.startswith(f'{side}Hand') and n[-1].isdigit()}
        X = self.pose(np.zeros(16))
        # palm-side palm vertices (rest vertex normals along the palm normal of graft_v1.json, glTF axes) and, per
        # finger, the one under the line wrist -> its knuckle at TIP_AT of the way: where its tip rests in a fist
        fr = json.load(open(HERE / 'work/graft_v1.json'))['frames'][side[0]]['n']; n_g = np.array([fr[0], fr[2], -fr[1]])
        vn = np.zeros_like(X); T = X[self.tri]; fn = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
        for c in range(3):
            np.add.at(vn, self.tri[:, c], fn)
        vn /= np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-12)
        palm_side = np.where((self.part == 0) & (vn @ n_g > 0.4))[0]
        wrist = self.world[self.names.index(f'{side}Hand')][:3, 3]; self.tgt = {}
        for f in F[1:]:
            mcp = self.world[self.names.index(f'{side}Hand{f}1')][:3, 3]; q = wrist + TIP_AT[f] * (mcp - wrist)
            self.tgt[f] = palm_side[np.argmin(np.linalg.norm(X[palm_side] - q, axis=1))]
        for k, f in enumerate(F, 1):
            sel = np.where(np.isin(self.dom[hv], [f'{side}Hand{f}3']))[0]
            a = self.world[self.names.index(f'{side}Hand{f}3')][:3, 3]
            self.tipv[f] = sel[np.argmax(np.linalg.norm(X[sel] - a, axis=1))]

    def pose(self, p):
        """p: [I,M,R,P] x [mcp,pip,dip] (12) + thumb [cmc flex, toward index, mcp, ip] (4); added to rest, spread 0."""
        local = {k: [x.copy() for x in v] for k, v in self.base.items()}
        s = self.side
        for k, f in enumerate(F):
            if f == 'Thumb':
                a = p[12:16]
                rots = {1: qmul(qaxis([0, 0, 1], self.signs[f'{s}Thumb'] * a[1]), qaxis([1, 0, 0], a[0])),
                        2: qaxis([1, 0, 0], a[2]), 3: qaxis([1, 0, 0], a[3])}
            else:
                a = p[(k - 1) * 3:(k - 1) * 3 + 3]
                rots = {1: qaxis([1, 0, 0], a[0]), 2: qaxis([1, 0, 0], a[1]), 3: qaxis([1, 0, 0], a[2])}
            for j in (1, 2, 3):
                n = f'{s}Hand{f}{j}'; ni = self.names.index(n)
                trs = local.setdefault(ni, [x.copy() for x in self.m.rest[ni]])
                trs[1] = qmul(self.rest_q[n], rots[j])
        w = self.m.world(local); self.world = w
        pal = w[self.m.joints] @ self.m.inverse_binds
        B = np.einsum('vk,vkij->vij', self.W, pal[self.J])
        return np.einsum('vij,vj->vi', B, self.P)[:, :3]

    def depth(self, pts, X, faces):
        """signed depth (m, >0 inside) of pts behind the nearest face of `faces` (by face normal), 0 if outside."""
        T = X[self.tri[faces]]; a, b, c = T[:, 0], T[:, 1], T[:, 2]
        n = np.cross(b - a, c - a); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
        k = min(12, len(T)); _, near = cKDTree((a + b + c) / 3).query(pts, k=k); near = near.reshape(len(pts), -1)
        R = np.repeat(pts, k, 0)
        q, bary = closest_on_triangles(R, a[near.ravel()], b[near.ravel()], c[near.ravel()])
        d = np.linalg.norm(R - q, axis=1).reshape(near.shape); best = d.argmin(1); rows = np.arange(len(pts))
        qq = q.reshape(*near.shape, 3)[rows, best]
        interior = bary.reshape(*near.shape, 3)[rows, best].min(1) > 0.01   # an edge/corner hit has no clear side
        side = np.einsum('ij,ij->i', pts - qq, n[near[rows, best]])
        return np.where((side < 0) & interior & (d[rows, best] < 0.03), -side, 0.0), d[rows, best], side

    def metrics(self, p):
        X = self.pose(p); out = {'pairs': {}}
        parts = {k: np.where(self.part == k)[0] for k in range(6)}
        faces = {k: np.where(self.face_part == k)[0] for k in range(6)}
        pen = 0.0
        for a in range(1, 6):
            for b in range(0, 6):
                if a == b:
                    continue
                # distal vertices (bones 2-3) of one part against another part's distal faces (or the palm's faces)
                pa = parts[a][self.distal[parts[a]]]
                fb = faces[b] if b == 0 else faces[b][self.face_distal[faces[b]]]
                if not len(pa) or not len(fb):
                    continue
                dep, _, _ = self.depth(X[pa], X, fb)
                out['pairs'][f'{"HTIMRP"[a]}{"HTIMRP"[b]}'] = round(float(dep.max()) * 100, 2)
                tol = 0.5 if b == 0 and a > 1 else 0.1        # cm: a fingertip may press into the palm a little
                pen += max(0.0, float(dep.max()) * 100 - tol) ** 2
        # fingertips onto the palm (unsigned gap to the palm surface)
        tips = {}
        for f in F[1:]:
            tips[f] = float(np.linalg.norm(X[self.tipv[f]] - X[self.tgt[f]]))
        out['tip_gap_cm'] = {f: round(v * 100, 2) for f, v in tips.items()}
        # thumb tip on the outside of index/middle middle phalanges
        tt = X[self.tipv['Thumb']][None]
        mid = np.where(np.isin(self.face_part, [2, 3]))[0]
        dep, d, side = self.depth(tt, X, mid)
        out['thumb_gap_cm'] = round(float(side[0] if dep[0] == 0 else -dep[0]) * 100, 2)
        fist = np.concatenate([parts[k] for k in (0, 2, 3, 4, 5)])
        c = X[fist].mean(0); u = tt[0] - c; L = np.linalg.norm(u); u /= L
        out['thumb_out_cm'] = round(float(L - ((X[fist] - c) @ u).max()) * 100, 2)
        out['_pen'] = pen; out['_tips'] = tips; out['_thumb'] = (float(side[0] if dep[0] == 0 else -dep[0]), d[0])
        return out


def pose_array(p):
    """finger_poses.json pose -> the 16 solver angles (fingers I, M, R, P x MCP, PIP, DIP; thumb 4); spread ignored."""
    out = []
    for f in F[1:]:
        e = p.get('per_finger', {}).get(f, [0, 0, 0]); out += [p['fingers'][i] + e[i] for i in range(3)]
    return np.array(out + list(p['thumb']), float)


def cost(p, hands, w_prior=1.0):
    c = 0.0
    prior = np.array([70, 85, 25] * 4, float)
    c += w_prior * 1e-4 * float(((p[:12] - prior) ** 2).sum())
    for h in hands:
        m = h.metrics(p)
        c += m['_pen'] * 4
        c += sum(max(0.0, g * 100 - 1.5) ** 2 for g in m['_tips'].values())
        tg = m['_thumb'][0] * 100
        c += 4 * (max(0.0, 0.1 - tg) ** 2 + max(0.0, tg - 0.5) ** 2)
        c += 2 * max(0.0, m['thumb_out_cm'] + 0.3) ** 2
    return c


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('glb'); ap.add_argument('out')
    ap.add_argument('--start', default='fist'); ap.add_argument('--iters', type=int, default=1500)
    ap.add_argument('--per-side', action='store_true')
    o = ap.parse_args()
    signs = json.load(open(Path(o.glb).with_suffix('.json')))['spread_signs']
    poses = json.load(open(HERE / 'scripts/finger_poses.json'))['poses']; s0 = poses[o.start]
    p0 = []
    for f in F[1:]:
        e = s0.get('per_finger', {}).get(f, [0, 0, 0]); p0 += [s0['fingers'][i] + e[i] for i in range(3)]
    p0 = np.array(p0 + list(s0['thumb']), float)
    groups = [['Left'], ['Right']] if o.per_side else [['Left', 'Right']]
    res = {}
    for g in groups:
        hands = [Hand(o.glb, s, signs) for s in g]
        for h in hands:
            print('START', h.side, {k: v for k, v in h.metrics(p0).items() if not k.startswith('_')})
        bounds = [(40, 100), (50, 110), (0, 70)] * 4 + [(-40, 30), (20, 95), (0, 60), (0, 60)]
        p0 = np.clip(p0, [b[0] for b in bounds], [b[1] for b in bounds])
        r = minimize(cost, p0, args=(hands,), method='Powell', bounds=bounds,
                     options={'maxfev': o.iters, 'xtol': 0.5, 'ftol': 1e-4})
        p = np.round(r.x, 1)
        for h in hands:
            mm = h.metrics(p); res[h.side] = {'angles': p.tolist(), **{k: v for k, v in mm.items() if not k.startswith('_')}}
            print('SOLVED', h.side, 'cost', round(float(r.fun), 3), res[h.side])
    json.dump(res, open(o.out, 'w'), indent=1)
