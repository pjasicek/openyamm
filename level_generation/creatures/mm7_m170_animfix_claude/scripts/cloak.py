"""The MM6 Thief's cloak chains simulated over a new locomotion clip (package h01 of the 2026-10-31 gait rollout).

A numpy port of ../../mm6_thf_claude/scripts/cloak_sim.py (the Blender bake of the accepted clips) for loops: 17 chains
of 4 bones hung from the chest bone `Spine`, 9 points per chain (joints and bone midpoints), verlet at 144 Hz with
velocity damping DAMP, a pull STIFF toward the rest bell hung plumb from the chain roots (chest heading only; blending
into the chest frame as the chest tilts past 25-70 deg), exact segment lengths, neighbour chains kept between 0.6 and
NB_MAX x their rest spacing, one-sided collisions (outward along the chain's own direction) against capsules on legs,
hips, torso, arms and feet, a floor, three cycles simulated and the last kept. Each chain bone is then aimed at its
next simulated point. Constants, capsules and radii are the bake's.

The chain rest points come from the Blender rig (scene['thf_cloak'] of mm6_thf_claude/work/rig_v3.blend, dumped once
to work/thf_cloak_chains.json; Blender (x, y, z) -> GLB (x, z, -y), which matches the GLB's bind pose exactly).
Joint names are the composer's aliases (gaitlib.MESHY: Spine -> B_Spine2, LeftUpLeg -> B_L_Thigh, ...).
"""
import json

import numpy as np

import gaitlib
from gaitlib import glb_pose

SUB_HZ, DAMP, STIFF, MARGIN, FLOOR = 144, 0.985, 0.05, 0.022, 0.025
NB_MAX = 1.06
CHEST = 'B_Spine2'                       # Meshy 'Spine', the chains' parent
CAPS = [('LeftUpLeg', 'LeftLeg', 0.09), ('RightUpLeg', 'RightLeg', 0.09), ('LeftLeg', 'LeftFoot', 0.075),
        ('RightLeg', 'RightFoot', 0.075), ('LeftUpLeg', 'RightUpLeg', 0.10), ('Spine02', 'Spine', 0.12),
        ('LeftArm', 'LeftForeArm', 0.05), ('RightArm', 'RightForeArm', 0.05), ('LeftForeArm', 'LeftHand', 0.045),
        ('RightForeArm', 'RightHand', 0.045), ('LeftFoot', 'LeftToeBase', 0.06), ('RightFoot', 'RightToeBase', 0.06)]
STEPS = np.arange(0.0, 0.45, 0.004)


def blender_to_glb(p):
    p = np.asarray(p, dtype=float)
    return np.stack([p[..., 0], p[..., 2], -p[..., 1]], axis=-1)


def seg_dist(p, a, b):
    ab = b - a
    t = np.clip(((p - a) @ ab) / (ab @ ab), 0, 1)
    return p - (a + np.outer(t, ab) if p.ndim == 2 else a + t * ab)


def rot_between(a, b):
    a = a / np.linalg.norm(a)
    b = b / np.linalg.norm(b)
    v = np.cross(a, b)
    c = float(np.dot(a, b))
    if np.linalg.norm(v) < 1e-9:
        return np.eye(3)
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + K + K @ K / (1 + c)


def ortho(m):
    u, _, vt = np.linalg.svd(m)
    return u @ vt


class Cloak:
    def __init__(self, P, chains_path, floor=FLOOR, leg_pad=0.0):
        self.floor = float(floor)     # chain points never below it (the bake's 2.5 cm; the hem skin hangs below them)
        data = json.loads(open(chains_path).read())
        self.P = P
        I = P.idx
        alias = gaitlib.MESHY
        self.cap_nodes = [(I[alias.get(a, a)], I[alias.get(b, b)], r) for a, b, r in CAPS]
        self.chains = data['chains']
        self.order = sorted(range(len(self.chains)), key=lambda i: self.chains[i]['deg'])
        self.joints = [blender_to_glb(c['pts']) for c in self.chains]          # 5 joints per chain, bind pose
        rest = []
        for J in self.joints:
            pts = []
            for k in range(4):
                pts += [J[k], (J[k] + J[k + 1]) / 2]
            pts.append(J[4])
            rest.append(np.array(pts))
        self.rest = rest
        self.out = [np.array([np.sin(np.radians(c['deg'])), 0.0, -np.cos(np.radians(c['deg']))]) for c in self.chains]
        joints = list(P.model.joints)
        self.bind = {i: np.linalg.inv(P.model.inverse_binds[joints.index(i)]) for i in set(joints)}
        self.rest_chest = self.bind[I[CHEST]]
        allrest = np.vstack([r[1:] for r in rest])
        self.radii = []
        for (a, b, r), (na, _, _) in zip(self.cap_nodes, CAPS):
            d = np.linalg.norm(seg_dist(allrest, self.bind[a][:3, 3], self.bind[b][:3, 3]), axis=1).min()
            floor_r = 0.04 if na.endswith(('Arm', 'ForeArm')) else 0.01
            self.radii.append(min(r, max(floor_r, d - MARGIN - 0.004)))
        # `leg_pad`: extra radius on the leg and foot capsules after the rest-pose shrink (a sprint's kicked heel came
        # through the back hem between chain points)
        for i, (na, nb, _) in enumerate(CAPS):
            if na != 'LeftUpLeg' or nb != 'RightUpLeg':
                if na.endswith(('UpLeg', 'Leg', 'Foot')):
                    self.radii[i] += float(leg_pad)
        self.seglen = [np.linalg.norm(np.diff(r, axis=0), axis=1) for r in rest]
        self.nb = [(self.order[i], self.order[i + 1]) for i in range(len(self.order) - 1)]
        self.nbrest = {(a, b): np.linalg.norm(rest[a][1:] - rest[b][1:], axis=1) for a, b in self.nb}
        self.bones = [[I[b] for b in c['bones']] for c in self.chains]
        # each bone's rest direction (joint k -> k+1) in its own local frame: the aim of the bake's bone Y axis
        self.dir_local = []
        for J, bones in zip(self.joints, self.bones):
            self.dir_local.append([ortho(self.bind[n][:3, :3]).T @ (J[k + 1] - J[k]) for k, n in enumerate(bones)])

    def body(self, worlds, f):
        """Chest matrix and capsule ends at fractional sample f (loop, linear between samples)."""
        N = len(worlds)
        i0 = int(np.floor(f)) % N
        i1 = (i0 + 1) % N
        w = f - np.floor(f)
        c = self.P.idx[CHEST]
        q0 = glb_pose.matrix_quaternion(ortho(worlds[i0, c, :3, :3]))
        q1 = glb_pose.matrix_quaternion(ortho(worlds[i1, c, :3, :3]))
        sp = np.eye(4)
        sp[:3, :3] = glb_pose.quaternion_matrix(glb_pose.slerp(q0, q1, w))
        sp[:3, 3] = (1 - w) * worlds[i0, c, :3, 3] + w * worlds[i1, c, :3, 3]
        caps = [((1 - w) * worlds[i0, a, :3, 3] + w * worlds[i1, a, :3, 3],
                 (1 - w) * worlds[i0, b, :3, 3] + w * worlds[i1, b, :3, 3]) for a, b, _ in self.cap_nodes]
        return sp, caps

    def yaw(self, sp):
        f = sp[:3, :3] @ ortho(self.rest_chest[:3, :3]).T @ np.array([0, 0, 1.0])
        a = np.arctan2(f[0], f[2])
        return np.array([[np.cos(a), 0, np.sin(a)], [0, 1, 0], [-np.sin(a), 0, np.cos(a)]])

    def tilt(self, sp):
        up = sp[:3, :3] @ ortho(self.rest_chest[:3, :3]).T @ np.array([0, 1.0, 0])
        t = np.degrees(np.arccos(np.clip(up[1] / np.linalg.norm(up), -1, 1)))
        x = min(1.0, max(0.0, (t - 25.0) / 45.0))
        return x * x * (3 - 2 * x)

    def simulate(self, worlds, T):
        """Chain points (chains, 9, 3) at each of the N samples of a loop of length T."""
        N = len(worlds)
        n = max(1, int(round(T * SUB_HZ)))
        rest, out = self.rest, self.out
        inv_rest = np.linalg.inv(self.rest_chest)
        sp, caps = self.body(worlds, 0.0)
        Ry = self.yaw(sp)
        R0 = [(sp @ inv_rest @ np.append(r[0], 1.0))[:3] for r in rest]
        X = [np.array([R0[c] + Ry @ (rest[c][k] - rest[c][0]) for k in range(len(rest[c]))])
             for c in range(len(rest))]
        V = [np.zeros_like(x) for x in X]
        kept = []
        for step in range(3 * n + 1):
            f = (step % n) / n * N
            sp, caps = self.body(worlds, f)
            Mc = sp @ inv_rest
            Ry, tw = self.yaw(sp), self.tilt(sp)
            old = [x.copy() for x in X]
            for c in range(len(rest)):
                x = X[c]
                root = (Mc @ np.append(rest[c][0], 1.0))[:3]
                tgt = root + (rest[c] - rest[c][0]) @ Ry.T
                if tw > 0:
                    tgt = tgt * (1 - tw) + (rest[c] @ Mc[:3, :3].T + Mc[:3, 3]) * tw
                    tgt[1:, 1] = tgt[1:, 1] * (1 - tw) + (self.floor + 0.01) * tw
                x[1:] += V[c][1:] * DAMP + (tgt[1:] - x[1:]) * STIFF
                x[0] = root
            for _ in range(3):
                for c in range(len(rest)):
                    x = X[c]
                    for k in range(len(x) - 1):
                        d = x[k + 1] - x[k]
                        x[k + 1] = x[k] + d / max(np.linalg.norm(d), 1e-9) * self.seglen[c][k]
                for a, b in self.nb:
                    d = X[b][1:] - X[a][1:]
                    L = np.linalg.norm(d, axis=1)
                    r = self.nbrest[(a, b)]
                    corr = np.where(L > NB_MAX * r, L - NB_MAX * r, np.where(L < 0.6 * r, L - 0.6 * r, 0.0))
                    u = d / np.maximum(L, 1e-9)[:, None]
                    X[a][1:] += u * (corr * 0.5)[:, None]
                    X[b][1:] -= u * (corr * 0.5)[:, None]
                for c in range(len(rest)):
                    x = X[c]
                    u = Ry @ out[c]
                    for (a, b), r in zip(caps, self.radii):
                        L = np.linalg.norm(seg_dist(x[1:], a, b), axis=1)
                        for j in np.where(L < r + MARGIN)[0]:
                            q = x[1 + j]
                            moved = q + np.outer(STEPS, u)
                            clear = np.linalg.norm(seg_dist(moved, a, b), axis=1) >= r + MARGIN
                            st = STEPS[np.argmax(clear)] if clear.any() else STEPS[-1]
                            x[1 + j] = q + u * st
                    x[1:, 1] = np.maximum(x[1:, 1], self.floor)
            for c in range(len(rest)):
                V[c] = X[c] - old[c]
            if step >= 2 * n:
                kept.append(np.array([x.copy() for x in X]))
        kept = np.array(kept)                      # n + 1 states over the last loop, 0..n
        pts = np.zeros((N,) + kept.shape[1:])
        for i in range(N):
            s = i / N * n
            j = int(np.floor(s))
            w = s - j
            pts[i] = (1 - w) * kept[j] + w * kept[min(j + 1, n)]
        return pts

    def pose(self, worlds, pts):
        """Aim every chain bone at its next simulated joint; returns the worlds with the cloak bones set."""
        P = self.P
        worlds = worlds.copy()
        for i, W in enumerate(worlds):
            for c, bones in enumerate(self.bones):
                for k, node in enumerate(bones):
                    Mp = W[P.parent[node]]
                    t, r, s = P.model.rest[node]
                    Mu = Mp @ glb_pose.trs_matrix(t, r, s)
                    scale = np.linalg.norm(Mu[:3, :3], axis=0)
                    Ru = Mu[:3, :3] / scale[None, :]
                    target = pts[i, c, 2 * k + 2] - Mu[:3, 3]
                    R = rot_between(Ru @ self.dir_local[c][k], target) @ Ru
                    W[node] = np.eye(4)
                    W[node][:3, :3] = R * scale[None, :]
                    W[node][:3, 3] = Mu[:3, 3]
        return worlds

    def nodes(self):
        return {n for bones in self.bones for n in bones}
