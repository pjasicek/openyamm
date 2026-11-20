"""Cloak and robe chains simulated over a new locomotion clip (package h03 of the 2026-10-31 gait rollout).

Package h03 generalisation of ../h01/scripts/cloak.py (a numpy port of ../../mm6_thf_claude/scripts/cloak_sim.py) to
the three MM6 bakes that descend from the Thief's (each project's cloak_sim.py / robe_sim.py, same algorithm with its
own constants), chosen by a per-model preset:

- `cle`: ../../mm6_cle_claude/scripts/cloak_sim.py (13 chains from the chest `Spine`, the Thief's constants with
  MARGIN 0.035 and wider leg capsules: thighs 0.15, shins 0.10, hips 0.13).
- `dru1`: ../../mm6_dru1_claude/scripts/cloak_sim.py (15 chains from `B_Spine2`; DAMP 0.94, STIFF 0.09 (calmer than the
  Thief's after the user's "cloak flapping erratically"), NARROW 0.4 (the hanging bell narrowed toward the hem),
  neck and heel capsules, leg capsule radii kept at least 8.5 cm, trajectories smoothed over 1.5 frames at 30 fps).
- `sor1`: ../../mm6_sor1_codex/scripts/robe_sim.py (the druidess bake on 16 closed robe chains from `B_Pelvis`:
  MARGIN 0.03, FLOOR 0.10, wider foot and heel capsules, other capsules kept at least 10 cm, neighbours wrap round).

Per chain point (joints and bone midpoints, 9 per chain): verlet with velocity damping DAMP, a pull STIFF toward the
rest bell hung plumb from the chain roots (root bone heading only), exact segment lengths, neighbour chains kept
between 0.6 and NB_MAX x their rest spacing, one-sided collisions (outward along the chain's own direction) against
capsules on legs, hips, torso, arms and feet, a floor; three loops simulated and the last kept. Each chain bone is
then aimed at its next simulated point. The upright branch only (the lying blend of the bakes is for deaths).

Additions for runs (opt-in, job keys under `cloak`): `floor` (chain points never below it), `leg_pad` (extra radius on
the leg and foot capsules after the rest-pose shrink, h01), `lift_deg` (the bell's rest target turned back about the
root's left axis: a cloak that streams behind at speed, like h05's `cape_lift`), `smooth_s` (trajectory smoothing in
seconds, overriding the preset's), `stiff`, `damp`.

Chain rest points come from the projects' Blender rigs (`dump_cloak_chains.py`; Blender (x, y, z) -> GLB (x, z, -y),
matching the GLB bind pose exactly: `chains_check.py`) or, for the Sorcerer whose rig blend is not kept, from the
GLB's bind pose (`chains_check.py --from-glb Robe_`). Joint names are the composer's aliases (gaitlib.MESHY).
"""
import json

import numpy as np
from scipy.ndimage import gaussian_filter1d

import gaitlib
from gaitlib import glb_pose

FLOOR = 0.025
STEPS = np.arange(0.0, 0.45, 0.004)
THIEF_CAPS = [('LeftUpLeg', 'LeftLeg', 0.09), ('RightUpLeg', 'RightLeg', 0.09), ('LeftLeg', 'LeftFoot', 0.075),
              ('RightLeg', 'RightFoot', 0.075), ('LeftUpLeg', 'RightUpLeg', 0.10), ('Spine02', 'Spine', 0.12),
              ('LeftArm', 'LeftForeArm', 0.05), ('RightArm', 'RightForeArm', 0.05), ('LeftForeArm', 'LeftHand', 0.045),
              ('RightForeArm', 'RightHand', 0.045), ('LeftFoot', 'LeftToeBase', 0.06),
              ('RightFoot', 'RightToeBase', 0.06)]
DRU_CAPS = [('B_L_Thigh', 'B_L_Calf', 0.11), ('B_R_Thigh', 'B_R_Calf', 0.11), ('B_L_Calf', 'B_L_Foot', 0.10),
            ('B_R_Calf', 'B_R_Foot', 0.10), ('B_L_Thigh', 'B_R_Thigh', 0.11), ('B_Spine', 'B_Spine2', 0.12),
            ('B_Spine2', 'B_Neck', 0.10),
            ('B_L_UpperArm', 'B_L_Forearm', 0.05), ('B_R_UpperArm', 'B_R_Forearm', 0.05),
            ('B_L_Forearm', 'B_L_Hand', 0.045), ('B_R_Forearm', 'B_R_Hand', 0.045),
            ('B_L_Foot', 'B_L_Toe0', 0.06), ('B_R_Foot', 'B_R_Toe0', 0.06),
            ('B_L_Calf', 'B_L_Foot:heel', 0.08), ('B_R_Calf', 'B_R_Foot:heel', 0.08)]
PRESETS = {
    'thf': dict(chest='Spine', sub_hz=144, damp=0.985, stiff=0.05, margin=0.022, floor=0.025, narrow=0.0,
                smooth_s=0.0, closed=False, caps=THIEF_CAPS, floor_r='thief'),
    'cle': dict(chest='Spine', sub_hz=144, damp=0.985, stiff=0.05, margin=0.035, floor=0.025, narrow=0.0,
                smooth_s=0.0, closed=False, floor_r='thief',
                caps=[('LeftUpLeg', 'LeftLeg', 0.15), ('RightUpLeg', 'RightLeg', 0.15), ('LeftLeg', 'LeftFoot', 0.10),
                      ('RightLeg', 'RightFoot', 0.10), ('LeftUpLeg', 'RightUpLeg', 0.13)] + THIEF_CAPS[5:]),
    'dru1': dict(chest='B_Spine2', sub_hz=150, damp=0.94, stiff=0.09, margin=0.022, floor=0.02, narrow=0.4,
                 smooth_s=0.05, closed=False, caps=DRU_CAPS, floor_r='dru'),
    'sor1': dict(chest='B_Pelvis', sub_hz=150, damp=0.94, stiff=0.09, margin=0.030, floor=0.10, narrow=0.0,
                 smooth_s=0.05, closed=True, floor_r='sor',
                 caps=DRU_CAPS[:11] + [('B_L_Foot', 'B_L_Toe0', 0.11), ('B_R_Foot', 'B_R_Toe0', 0.11),
                                       ('B_L_Calf', 'B_L_Foot:heel', 0.12), ('B_R_Calf', 'B_R_Foot:heel', 0.12)]),
}
# (h18) the MM8 Cleric's robe bake (../../mm8_m460_claude/scripts/robe_sim.py): the MM6 Sorcerer's robe_sim.py with
# MARGIN 0.022 and FLOOR 0.025; the MM8 female Dark Elf peasant's dress bake (../../mm8_m428_claude/scripts/dress_sim.py)
# is the same with `Dress_` chains (its other changes are for Death only)
PRESETS['m460'] = dict(PRESETS['sor1'], margin=0.022, floor=0.025)
PRESETS['m428'] = dict(PRESETS['m460'])


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


def floor_radius(rule, name):
    arm = name.endswith(('Arm', 'ForeArm')) or 'UpperArm' in name or 'Forearm' in name
    if arm:
        return 0.04
    if rule == 'thief':
        return 0.01
    if 'Calf' in name or 'Thigh' in name:
        return 0.085
    return 0.10 if rule == 'sor' else 0.01


class Cloak:
    def __init__(self, P, spec, floor=None, leg_pad=0.0):
        if isinstance(spec, str):                       # h01's form: the Thief's chains file
            spec = {'chains': spec, 'preset': 'thf'}
        cfg = dict(PRESETS[spec.get('preset', 'thf')])
        cfg.update({k: v for k, v in spec.items() if k in cfg})
        self.cfg = cfg
        self.floor = float(spec.get('floor', floor if floor is not None else cfg['floor']))
        leg_pad = float(spec.get('leg_pad', leg_pad))
        data = json.loads(open(spec['chains']).read())
        self.P = P
        I = P.idx
        alias = gaitlib.MESHY
        self.chest = alias.get(cfg['chest'], cfg['chest'])
        self.caps = [(alias.get(a, a), b if ':' in b else alias.get(b, b), r) for a, b, r in cfg['caps']]
        self.cap_nodes = [(I[a], (I[b.split(':')[0]], I[b.split(':')[0].replace('Foot', 'Toe0')])
                           if ':' in b else I[b], r) for a, b, r in self.caps]
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
        self.rest_chest = self.bind[I[self.chest]]
        # the bell target: optionally narrowed toward the hem (dru1) and turned back about the root's left axis
        target = []
        lift = np.radians(float(spec.get('lift_deg', 0.0)))
        for c, r in enumerate(rest):
            off = r - r[0]
            f = 1 - float(cfg['narrow']) * np.linspace(0, 1, len(off))[:, None]
            off = off * np.array([1.0, 0.0, 1.0]) * f + off * np.array([0.0, 1.0, 0.0])
            if lift:
                # rotate about +X (left): the hem moves back (-Z) and up
                Rl = np.array([[1, 0, 0], [0, np.cos(lift), np.sin(lift)], [0, -np.sin(lift), np.cos(lift)]])
                off = off @ Rl.T
            target.append(r[0] + off)
        self.target = target
        allrest = np.vstack([r[1:] for r in rest])
        self.radii = []
        W_bind = np.array([self.bind.get(i, np.eye(4)) for i in range(len(P.nodes))])
        rest_caps = [self._cap_ends(W_bind, cn) for cn in self.cap_nodes]
        for (a, b), (na, _, r) in zip(rest_caps, self.caps):
            d = np.linalg.norm(seg_dist(allrest, a, b), axis=1).min()
            self.radii.append(min(r, max(floor_radius(cfg['floor_r'], na), d - cfg['margin'] - 0.004)))
        for i, (na, nb, _) in enumerate(self.caps):
            if na.endswith(('Thigh', 'Calf', 'Foot')) and not nb.endswith('Thigh'):
                self.radii[i] += leg_pad
        self.seglen = [np.linalg.norm(np.diff(r, axis=0), axis=1) for r in rest]
        n = len(self.order)
        pairs = range(n) if cfg['closed'] else range(n - 1)
        self.nb = [(self.order[i], self.order[(i + 1) % n]) for i in pairs]
        self.nbrest = {(a, b): np.linalg.norm(rest[a][1:] - rest[b][1:], axis=1) for a, b in self.nb}
        self.bones = [[I[b] for b in c['bones']] for c in self.chains]
        self.dir_local = []
        for J, bones in zip(self.joints, self.bones):
            self.dir_local.append([ortho(self.bind[n][:3, :3]).T @ (J[k + 1] - J[k]) for k, n in enumerate(bones)])

    @staticmethod
    def _cap_ends(W, cap):
        a, b, _ = cap
        pa = W[a][:3, 3]
        if isinstance(b, tuple):
            # heel: behind and below the ankle, opposite the toe direction (the druidess bake's `:heel`)
            fh, th = W[b[0]][:3, 3], W[b[1]][:3, 3]
            return pa, fh - 0.35 * (th - fh) + np.array([0.0, -0.05, 0.0])
        return pa, W[b][:3, 3]

    def body(self, worlds, f):
        """Root matrix and capsule ends at fractional sample f (loop, linear between samples)."""
        N = len(worlds)
        i0 = int(np.floor(f)) % N
        i1 = (i0 + 1) % N
        w = f - np.floor(f)
        c = self.P.idx[self.chest]
        q0 = glb_pose.matrix_quaternion(ortho(worlds[i0, c, :3, :3]))
        q1 = glb_pose.matrix_quaternion(ortho(worlds[i1, c, :3, :3]))
        sp = np.eye(4)
        sp[:3, :3] = glb_pose.quaternion_matrix(glb_pose.slerp(q0, q1, w))
        sp[:3, 3] = (1 - w) * worlds[i0, c, :3, 3] + w * worlds[i1, c, :3, 3]
        caps = []
        for cn in self.cap_nodes:
            a0, b0 = self._cap_ends(worlds[i0], cn)
            a1, b1 = self._cap_ends(worlds[i1], cn)
            caps.append(((1 - w) * a0 + w * a1, (1 - w) * b0 + w * b1))
        return sp, caps

    def yaw(self, sp):
        f = sp[:3, :3] @ ortho(self.rest_chest[:3, :3]).T @ np.array([0, 0, 1.0])
        a = np.arctan2(f[0], f[2])
        return np.array([[np.cos(a), 0, np.sin(a)], [0, 1, 0], [-np.sin(a), 0, np.cos(a)]])

    def simulate(self, worlds, T):
        """Chain points (chains, 9, 3) at each of the N samples of a loop of length T."""
        cfg = self.cfg
        damp, stiff, margin = float(cfg['damp']), float(cfg['stiff']), float(cfg['margin'])
        N = len(worlds)
        n = max(1, int(round(T * cfg['sub_hz'])))
        rest, out, target = self.rest, self.out, self.target
        inv_rest = np.linalg.inv(self.rest_chest)
        sp, caps = self.body(worlds, 0.0)
        Ry = self.yaw(sp)
        R0 = [(sp @ inv_rest @ np.append(r[0], 1.0))[:3] for r in rest]
        X = [np.array([R0[c] + Ry @ (target[c][k] - target[c][0]) for k in range(len(rest[c]))])
             for c in range(len(rest))]
        V = [np.zeros_like(x) for x in X]
        kept = []
        for step in range(3 * n + 1):
            f = (step % n) / n * N
            sp, caps = self.body(worlds, f)
            Mc = sp @ inv_rest
            Ry = self.yaw(sp)
            old = [x.copy() for x in X]
            for c in range(len(rest)):
                x = X[c]
                root = (Mc @ np.append(rest[c][0], 1.0))[:3]
                tgt = root + (target[c] - target[c][0]) @ Ry.T
                x[1:] += V[c][1:] * damp + (tgt[1:] - x[1:]) * stiff
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
                    corr = np.where(L > 1.06 * r, L - 1.06 * r, np.where(L < 0.6 * r, L - 0.6 * r, 0.0))
                    u = d / np.maximum(L, 1e-9)[:, None]
                    X[a][1:] += u * (corr * 0.5)[:, None]
                    X[b][1:] -= u * (corr * 0.5)[:, None]
                for c in range(len(rest)):
                    x = X[c]
                    u = Ry @ out[c]
                    for (a, b), r in zip(caps, self.radii):
                        L = np.linalg.norm(seg_dist(x[1:], a, b), axis=1)
                        for j in np.where(L < r + margin)[0]:
                            q = x[1 + j]
                            moved = q + np.outer(STEPS, u)
                            clear = np.linalg.norm(seg_dist(moved, a, b), axis=1) >= r + margin
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
        sigma = float(cfg['smooth_s']) * N / T
        if sigma > 0:
            # the dru1/sor1 bakes smooth the kept trajectories over time (circular for loops), roots exact, then
            # restore the segment lengths and the floor
            sm = gaussian_filter1d(pts, sigma, axis=0, mode='wrap')
            sm[:, :, 0] = pts[:, :, 0]
            for i in range(N):
                for c in range(len(rest)):
                    x = sm[i, c]
                    for k in range(len(x) - 1):
                        d = x[k + 1] - x[k]
                        x[k + 1] = x[k] + d / max(np.linalg.norm(d), 1e-9) * self.seglen[c][k]
                    x[1:, 1] = np.maximum(x[1:, 1], self.floor)
            pts = sm
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
