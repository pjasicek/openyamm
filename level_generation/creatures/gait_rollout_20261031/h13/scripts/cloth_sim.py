"""Cloth chains (robe skirt, cape sheet) of a new locomotion clip: a numpy port of the robed projects' Blender
robe_sim.py (../../mm7_m422_claude/scripts/robe_sim.py; the Monk's copy is the same without the m422 flags), run on
the composer's world matrices so a jog or sprint gets its own skirt and cape motion instead of the walk's.

Same model as robe_sim.py: per chain point (joints and bone midpoints) verlet with damping DAMP and a pull STIFF per
substep (5 substeps per 1/30 s) toward the rest bell hung from the chain root with the root bone's heading (yaw)
only; straight rigid bones; neighbour chains kept between 0.6 and NB_MAX of their rest spacing; one-sided capsule
collisions (a point inside moves out along its chain's outward heading); floor. Loops simulate three cycles and keep
the last; the kept trajectories are smoothed over time (SMOOTH_SIG frames at 30 fps, circular). The m422 flags:
BEND_SMOOTH (bending stiffness across the ring and along the chains), MID_COLLIDE (neighbour midpoints kept out of the
capsules, also as a hard pass after the smoothing), BEND_MAX (joint bend limit), NB_FINAL (a last neighbour pass).
Each chain bone then aims at the simulated joint below it (minimal-twist tracking, as key_frame in robe_sim.py).
Lying and tilt handling (Death) is not ported: locomotion stays upright.

Axes: the chain JSON (dump_chains.py) is Blender's (Z up, -Y forward); here glTF (Y up, +Z forward), x' = (x, z, -y).
"""
import json
import math

import numpy as np

SUB, DAMP, STIFF, FLOOR = 5, 0.94, 0.09, 0.025
NB_MAX = 1.06
STEPS = np.arange(0.0, 0.45, 0.004)
CAPS = [('B_L_Thigh', 'B_L_Calf', 0.065, 'leg'), ('B_R_Thigh', 'B_R_Calf', 0.065, 'leg'),
        ('B_L_Calf', 'B_L_Foot', 0.05, 'leg'), ('B_R_Calf', 'B_R_Foot', 0.05, 'leg'),
        ('B_L_Thigh', 'B_R_Thigh', 0.07, 'leg'), ('B_Spine', 'B_Spine2', 0.12, ''), ('B_Spine2', 'B_Neck', 0.10, ''),
        ('B_L_UpperArm', 'B_L_Forearm', 0.05, ''), ('B_R_UpperArm', 'B_R_Forearm', 0.05, ''),
        ('B_L_Forearm', 'B_L_Hand', 0.045, ''), ('B_R_Forearm', 'B_R_Hand', 0.045, ''),
        ('B_L_Foot', 'B_L_Toe0', 0.05, 'leg'), ('B_R_Foot', 'B_R_Toe0', 0.05, 'leg'),
        ('B_L_Hand', 'B_L_Hand:tip', 0.045, ''), ('B_R_Hand', 'B_R_Hand:tip', 0.045, '')]


def to_gltf(p):
    p = np.asarray(p, dtype=float)
    return np.stack([p[..., 0], p[..., 2], -p[..., 1]], axis=-1)


def seg_dist(p, a, b):
    ab = b - a
    t = np.clip(((p - a) @ ab) / (ab @ ab), 0, 1)
    q = a + np.outer(t, ab) if p.ndim == 2 else a + t * ab
    return p - q


def yaw_matrix(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def rot_between(u, v):
    """Smallest rotation taking unit u to unit v."""
    u = u / np.linalg.norm(u)
    v = v / np.linalg.norm(v)
    axis = np.cross(u, v)
    s = np.linalg.norm(axis)
    c = float(np.clip(u @ v, -1, 1))
    if s < 1e-12:
        return np.eye(3)
    k = axis / s
    K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    a = math.atan2(s, c)
    return np.eye(3) + math.sin(a) * K + (1 - math.cos(a)) * K @ K


class Cloth:
    def __init__(self, P, cfg):
        """P: compose_gait.Body. cfg: chains (json path), key, root, prefix-free settings: leg_r, leg_floor, margin,
        push_cap, finger_tip, narrow, smooth_sig, bend_smooth, bend_max, mid_collide, nb_final."""
        self.P = P
        self.cfg = cfg
        data = json.load(open(cfg['chains']))
        self.CH = data[cfg.get('key', 'cloak_chains')]
        self.root = cfg.get('root', 'B_Pelvis')
        self.margin = float(cfg.get('margin', 0.012))
        rest = []
        for c in self.CH:
            J = to_gltf(c['pts'])
            F = []
            for k in range(len(c['bones'])):
                F += [J[k], (J[k] + J[k + 1]) / 2]
            F.append(J[len(c['bones'])])
            rest.append(np.array(F))
        narrow = float(cfg.get('narrow', 0.0))
        for c in range(len(rest)):
            off = rest[c] - rest[c][0]
            f = 1 - narrow * np.linspace(0, 1, len(off))[:, None]
            off[:, [0, 2]] *= f
            rest[c] = rest[c][0] + off
        self.REST = rest
        self.NP = len(rest[0])
        self.OUT = [to_gltf([math.sin(math.radians(c['deg'])), math.cos(math.radians(c['deg'])), 0.0])
                    for c in self.CH]
        self.SEG = [np.linalg.norm(np.diff(r, axis=0), axis=1) for r in rest]
        self.order = sorted(range(len(self.CH)), key=lambda i: self.CH[i]['deg'])
        if 'group' in self.CH[0]:
            self.nb = [(i, i + 1) for i in range(len(self.CH) - 1) if self.CH[i]['group'] == self.CH[i + 1]['group']]
        else:
            self.nb = [(self.order[i], self.order[(i + 1) % len(self.order)]) for i in range(len(self.order))]
        self.nbrest = {(a, b): np.linalg.norm(rest[a][1:] - rest[b][1:], axis=1) for a, b in self.nb}
        I = P.idx
        rest_local = {i: P.model.rest[i] for i in range(len(P.nodes))}
        self.W_rest = P.model.world(rest_local)
        self.rest_root = self.W_rest[I[self.root]]
        leg_r = float(cfg.get('leg_r', 1.0))
        self.caps = [(a, b, r * (leg_r if kind == 'leg' else 1.0)) for a, b, r, kind in CAPS]
        allrest = np.vstack([r[1:] for r in rest])
        rest_caps = [(self.joint(self.W_rest, a), self.joint(self.W_rest, b)) for a, b, _ in self.caps]
        leg_floor = float(cfg.get('leg_floor', 0.035))
        self.radii = []
        for (a, b), (na, _, r) in zip(rest_caps, self.caps):
            d = np.linalg.norm(seg_dist(allrest, a, b), axis=1).min()
            floor_r = 0.04 if ('Arm' in na or 'Forearm' in na) else (
                leg_floor if any(t in na for t in ('Calf', 'Thigh', 'Foot')) else 0.10)
            self.radii.append(min(r, max(floor_r, d - self.margin - 0.004)))
        # the chain bones' rest locals (relative to the root / the previous chain bone)
        self.bones = [c['bones'] for c in self.CH]

    def joint(self, W, name):
        I = self.P.idx
        if name.endswith(':tip'):
            h = name.split(':')[0]
            hp = W[I[h], :3, 3]
            mk = W[I[h.replace('Hand', 'Finger2')], :3, 3]
            d = (mk - hp) / max(np.linalg.norm(mk - hp), 1e-9)
            return hp + d * 0.7 * float(self.cfg.get('finger_tip', 0.17))
        return W[I[name], :3, 3].copy()

    def state(self, W):
        sp = W[self.P.idx[self.root]]
        return sp, [(self.joint(W, a), self.joint(W, b)) for a, b, _ in self.caps]

    def roots(self, sp):
        M = sp @ np.linalg.inv(self.rest_root)
        return [M[:3, :3] @ r[0] + M[:3, 3] for r in self.REST]

    def yaw(self, sp):
        R = sp[:3, :3] @ np.linalg.inv(self.rest_root[:3, :3])
        f = R @ np.array([0, 0, 1.0])
        return yaw_matrix(math.atan2(f[0], f[2]))

    def rigid_floor(self, x, seg):
        for k in range(0, self.NP - 1, 2):
            d = x[k + 2] - x[k]
            L = np.linalg.norm(d)
            Lb = seg[k] + seg[k + 1]
            x[k + 2] = x[k] + d / max(L, 1e-9) * Lb
            if x[k + 2][1] < FLOOR:
                dz = FLOOR - x[k][1]
                if abs(dz) < Lb:
                    hor = d.copy()
                    hor[1] = 0
                    hn = np.linalg.norm(hor)
                    hor = hor / hn if hn > 1e-9 else np.array([0.0, 0.0, -1.0])
                    x[k + 2] = x[k] + hor * math.sqrt(Lb * Lb - dz * dz) + np.array([0, dz, 0])
                else:
                    x[k + 2][1] = FLOOR
            x[k + 1] = (x[k] + x[k + 2]) / 2

    def push_out(self, x, caps, u0):
        for (a, b), r in zip(caps, self.radii):
            d = seg_dist(x[1:], a, b)
            L = np.linalg.norm(d, axis=1)
            for j in np.where(L < r + self.margin)[0]:
                q = x[1 + j]
                st = 0.0
                for st in STEPS:
                    if np.linalg.norm(seg_dist(q + u0 * st, a, b)) >= r + self.margin:
                        break
                x[1 + j] = q + u0 * st

    def mid_push(self, X, pairs, caps):
        for a_, b_ in pairs:
            m_ = (X[a_][1:] + X[b_][1:]) / 2
            for (ca, cb), r in zip(caps, self.radii):
                d = seg_dist(m_, ca, cb)
                L = np.linalg.norm(d, axis=1)
                for j in np.where(L < r + self.margin)[0]:
                    push = d[j] / max(L[j], 1e-9) * (r + self.margin - L[j])
                    X[a_][1 + j] += push
                    X[b_][1 + j] += push
                    m_[j] += push

    def body_at(self, worlds, phase):
        """Root matrix and capsule ends at a loop phase (0-1), linear between the samples (periodic)."""
        N = len(worlds)
        f = (phase % 1.0) * N
        i = int(math.floor(f)) % N
        j = (i + 1) % N
        w = f - math.floor(f)
        s0, c0 = self.state(worlds[i])
        s1, c1 = self.state(worlds[j])
        from glb_pose import matrix_quaternion, quaternion_matrix, slerp
        q = slerp(matrix_quaternion(s0[:3, :3]), matrix_quaternion(s1[:3, :3]), w)
        sp = np.eye(4)
        sp[:3, :3] = quaternion_matrix(q)
        sp[:3, 3] = s0[:3, 3] * (1 - w) + s1[:3, 3] * w
        caps = [(a0 * (1 - w) + a1 * w, b0 * (1 - w) + b1 * w) for (a0, b0), (a1, b1) in zip(c0, c1)]
        return sp, caps

    def simulate(self, worlds, T):
        """Chain points per output sample (N, chains, points, 3) for a loop of length T."""
        N = len(worlds)
        steps = int(round(T * 30 * SUB))
        CH = range(len(self.CH))
        sp, caps = self.body_at(worlds, 0.0)
        R0, Ry = self.roots(sp), self.yaw(sp)
        X = [np.array([R0[c] + Ry @ (self.REST[c][k] - self.REST[c][0]) for k in range(self.NP)]) for c in CH]
        V = [np.zeros_like(x) for x in X]
        mid = bool(self.cfg.get('mid_collide', False))
        kept = []
        for step in range(3 * steps):
            sp, caps = self.body_at(worlds, step / steps)
            Rr, Ry = self.roots(sp), self.yaw(sp)
            old = [x.copy() for x in X]
            for c in CH:
                x = X[c]
                tgt = np.array([Rr[c] + Ry @ (self.REST[c][k] - self.REST[c][0]) for k in range(self.NP)])
                x[1:] += V[c][1:] * DAMP + (tgt[1:] - x[1:]) * STIFF
                x[0] = Rr[c]
            for it in range(3):
                for c in CH:
                    x = X[c]
                    for k in range(0, self.NP - 1, 2):
                        d = x[k + 2] - x[k]
                        L = np.linalg.norm(d)
                        x[k + 2] = x[k] + d / max(L, 1e-9) * (self.SEG[c][k] + self.SEG[c][k + 1])
                        x[k + 1] = (x[k] + x[k + 2]) / 2
                for a, b in self.nb:
                    d = X[b][1:] - X[a][1:]
                    L = np.linalg.norm(d, axis=1)
                    r = self.nbrest[(a, b)]
                    corr = np.where(L > NB_MAX * r, L - NB_MAX * r, np.where(L < 0.6 * r, L - 0.6 * r, 0.0))
                    u = d / np.maximum(L, 1e-9)[:, None]
                    X[a][1:] += u * (corr * 0.5)[:, None]
                    X[b][1:] -= u * (corr * 0.5)[:, None]
                for c in CH:
                    self.push_out(X[c], caps, Ry @ self.OUT[c])
                    X[c][1:, 1] = np.maximum(X[c][1:, 1], FLOOR)
                if mid:
                    self.mid_push(X, self.nb, caps)
            for c in CH:
                self.rigid_floor(X[c], self.SEG[c])
            for c in CH:
                V[c] = X[c] - old[c]
            if step >= 2 * steps:
                kept.append(np.array(X))
        kept = np.array(kept)                                    # steps x chains x points x 3, phases k / steps
        # to the output samples (linear in phase, periodic), then the temporal smoothing (SMOOTH_SIG frames at 30 fps)
        ph = np.arange(N) / N * steps
        i0 = np.floor(ph).astype(int) % steps
        i1 = (i0 + 1) % steps
        w = (ph - np.floor(ph))[:, None, None, None]
        Xs = kept[i0] * (1 - w) + kept[i1] * w
        sig = float(self.cfg.get('smooth_sig', 1.5)) * N / (T * 30)
        if sig > 0:
            r_ = int(math.ceil(3 * sig))
            kern = np.exp(-0.5 * (np.arange(-r_, r_ + 1) / sig) ** 2)
            kern /= kern.sum()
            idx = (np.arange(N)[:, None] + np.arange(-r_, r_ + 1)[None, :]) % N
            Xsm = (Xs[idx] * kern[None, :, None, None, None]).sum(1)
            Xsm[:, :, 0] = Xs[:, :, 0]
        else:
            Xsm = Xs.copy()
        for i in range(N):
            for c in CH:
                self.rigid_floor(Xsm[i, c], self.SEG[c])
        bend_smooth = int(self.cfg.get('bend_smooth', 0))
        bend_max = float(self.cfg.get('bend_max', 0))
        order = self.order
        pos = {c: i for i, c in enumerate(order)}
        prv = [order[(pos[c] - 1) % len(order)] for c in CH]
        nxt = [order[(pos[c] + 1) % len(order)] for c in CH]
        ring = [(order[i], order[(i + 1) % len(order)]) for i in range(len(order))]
        for i in range(N):
            sp, caps = self.state(worlds[i])
            if bend_smooth and 'group' not in self.CH[0]:
                Rr, Ry = self.roots(sp), self.yaw(sp)
                tgt = np.array([[Rr[c] + Ry @ (self.REST[c][k] - self.REST[c][0]) for k in range(self.NP)] for c in CH])
                for it in range(bend_smooth):
                    D = Xsm[i] - tgt
                    D[:, 1:] = 0.5 * D[:, 1:] + 0.25 * (D[prv][:, 1:] + D[nxt][:, 1:])
                    A = D.copy()
                    A[:, 1:-1] = 0.5 * D[:, 1:-1] + 0.25 * (D[:, :-2] + D[:, 2:])
                    A[:, -1] = 0.5 * D[:, -1] + 0.5 * D[:, -2]
                    Xsm[i, :, 1:] = tgt[:, 1:] + A[:, 1:]
                    for c in CH:
                        self.rigid_floor(Xsm[i, c], self.SEG[c])
            if mid:
                Ry = self.yaw(sp)
                for it in range(2):
                    for c in CH:
                        self.push_out(Xsm[i, c], caps, Ry @ self.OUT[c])
                    self.mid_push(Xsm[i], ring, caps)
                    for c in CH:
                        self.rigid_floor(Xsm[i, c], self.SEG[c])
                if bend_max:
                    for c in CH:
                        x = Xsm[i, c]
                        for k in range(2, self.NP - 1, 2):
                            u = x[k] - x[k - 2]
                            w_ = x[k + 2] - x[k]
                            nu, nw = np.linalg.norm(u), np.linalg.norm(w_)
                            ang = math.degrees(math.acos(max(-1.0, min(1.0, float(u @ w_) / max(nu * nw, 1e-12)))))
                            if ang > bend_max:
                                R_full = rot_between(w_ / nw, u / nu)
                                frac = 1 - bend_max / ang
                                R_ = rot_power(R_full, frac)
                                piv = x[k].copy()
                                for m_ in range(k + 1, self.NP):
                                    x[m_] = piv + R_ @ (x[m_] - piv)
                        x[1:, 1] = np.maximum(x[1:, 1], FLOOR)
        if self.cfg.get('nb_final', False):
            nbr = {(a, b): np.linalg.norm(self.REST[a][1:] - self.REST[b][1:], axis=1) for a, b in self.nb}
            for i in range(N):
                for it in range(4):
                    for a_, b_ in self.nb:
                        d = Xsm[i, b_][1:] - Xsm[i, a_][1:]
                        L = np.linalg.norm(d, axis=1)
                        r = nbr[(a_, b_)]
                        corr = np.where(L > NB_MAX * r, L - NB_MAX * r, 0.0)
                        u = d / np.maximum(L, 1e-9)[:, None]
                        Xsm[i, a_][1:] += u * (corr * 0.5)[:, None]
                        Xsm[i, b_][1:] -= u * (corr * 0.5)[:, None]
                    for c in CH:
                        self.rigid_floor(Xsm[i, c], self.SEG[c])
        if self.cfg.get('final_collide', False):
            # new clips (runs): the bend limit and the last neighbour pass ran after the hard collision pass and let
            # the striding knee back through the coat front; one more hard pass per sample, then rigid bones
            for i in range(N):
                sp, caps = self.state(worlds[i])
                Ry = self.yaw(sp)
                for it in range(int(self.cfg.get('final_collide_passes', 2))):
                    for c in CH:
                        self.push_out(Xsm[i, c], caps, Ry @ self.OUT[c])
                    self.mid_push(Xsm[i], ring, caps)
                    for c in CH:
                        self.rigid_floor(Xsm[i, c], self.SEG[c])
        return Xsm

    def key(self, worlds, Xsm):
        """Chain bones aimed at the simulated joints (minimal-twist tracking from the previous sample, starting at the
        bone's parent-driven rest orientation); writes their world matrices into worlds."""
        I = self.P.idx
        for c, bones in enumerate(self.bones):
            prev = {}
            for i in range(len(worlds)):
                W = worlds[i]
                for k, b in enumerate(bones):
                    n = I[b]
                    parent = self.P.parent[n]
                    t, q, s = self.P.model.rest[n]
                    from glb_pose import trs_matrix
                    Mu = W[parent] @ trs_matrix(t, q, s)
                    basis = prev.get(b, Mu[:3, :3] / np.linalg.norm(Mu[:3, :3], axis=0))
                    y = basis[:, 1]
                    d = Xsm[i, c, 2 * k + 2] - Mu[:3, 3]
                    basis = rot_between(y, d) @ basis
                    prev[b] = basis
                    M = np.eye(4)
                    M[:3, :3] = basis * np.linalg.norm(Mu[:3, :3], axis=0)[None, :]
                    M[:3, 3] = Mu[:3, 3]
                    W[n] = M
        return worlds


def rot_power(R, w):
    from glb_pose import matrix_quaternion, quaternion_matrix
    q = matrix_quaternion(R)
    if q[3] < 0:
        q = -q
    angle = 2 * math.atan2(np.linalg.norm(q[:3]), q[3])
    if angle < 1e-9:
        return np.eye(3)
    axis = q[:3] / np.linalg.norm(q[:3])
    a = angle * w
    return quaternion_matrix(np.append(axis * math.sin(a / 2), math.cos(a / 2)))


def apply(P, worlds, T, cfgs, report):
    """Simulate every cloth config on a composed loop; returns worlds and the chain bone names (authored)."""
    names = []
    for cfg in cfgs:
        cloth = Cloth(P, cfg)
        Xsm = cloth.simulate(worlds, T)
        worlds = cloth.key(worlds, Xsm)
        names += [b for bones in cloth.bones for b in bones]
        report.setdefault('cloth', []).append({'chains': cfg['chains'], 'key': cfg.get('key', 'cloak_chains'),
                                               'radii': [round(r, 3) for r in cloth.radii]})
    return worlds, names
