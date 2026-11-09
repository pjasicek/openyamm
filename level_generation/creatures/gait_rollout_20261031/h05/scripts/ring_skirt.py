"""(h05) The MM6 PeasantF3's (mfp) five-ring wrap-skirt cage for a new locomotion clip: a numpy port of the kinematic
part of her project's final_skirt.py (../../../mm6_mfp_codex/scripts/final_skirt.py), which fitted the cage of the
accepted Walking and Running to the posed legs. Five rings of 12 pelvis-child points (Skirt_<ring>_<k>); per sample:

- ring frame: the pelvis' deformation; below the hip the ring follows the legs' mid-line instead (the mean of both
  hips, knees and ankles: the rest mid-line segment through the ring's height turned onto the posed one, about the
  posed point at that height), blended in over 10 cm below z 0.955;
- `hang` (h05, optional): a ring's centre rises at most this far above its pelvis-carried place;
- ring shape: an ellipse (rest radii 0.19 lateral, 0.145 fore-aft, centred 3 cm forward) widened to hold every leg skin
  vertex within 9.5 cm of the ring's rest height plus 1.4 cm (`posed_band`, h05: for the listed rings, thigh and
  knee skin at the ring's posed height);
- each point: the ring frame's rotation and the ellipse point (the joint's deformation = that rigid transform).

Then a push-out in place of the project's (8 passes against the closed skirt surface): per pass, every skirt vertex
inside a leg (its nearest leg vertex within 4 cm and the skirt vertex behind that vertex's normal: skirt_probe.py's
test) asks to move out along that normal by its depth + 1.5 mm; each cage point moves by the weighted mean of the asks
of the vertices it carries (x 0.75); `floor` (h05): skirt vertices below that height ask to rise to it, up to `push_passes` (8) passes. Axes: glTF (Y up, +Z forward); the project's Blender (x, y, z) is
glTF (x, z, -y).
"""
import re

import numpy as np
from scipy.spatial import cKDTree

import gaitlib
from gaitlib import glb_pose


def rotation_between(u, v):
    u = u / np.linalg.norm(u)
    v = v / np.linalg.norm(v)
    axis = np.cross(u, v)
    s = np.linalg.norm(axis)
    c = float(np.clip(u @ v, -1, 1))
    if s < 1e-12:
        return np.eye(3)
    k = axis / s
    K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + np.sin(np.arctan2(s, c)) * K + (1 - c) * K @ K


class RingSkirt:
    def __init__(self, P, cfg):
        self.P = P
        names = [n.get('name', '') for n in P.nodes]
        joints = list(P.model.joints)
        self.bind = {}
        ring = {}
        for i, n in enumerate(names):
            m = re.fullmatch(r'Skirt_(\d+)_(\d+)', n)
            if m:
                ring.setdefault(int(m.group(1)), {})[int(m.group(2))] = i
                self.bind[i] = np.linalg.inv(P.model.inverse_binds[joints.index(i)])
        self.rings = [ring[j] for j in sorted(ring)]
        self.ibm_pelvis = P.model.inverse_binds[joints.index(P.idx['B_Pelvis'])]
        self.levels = [float(np.mean([self.bind[i][1, 3] for i in r.values()])) for r in self.rings]
        self.count = len(self.rings[0])
        self.rx, self.ry = float(cfg.get('rx', 0.19)), float(cfg.get('ry', 0.145))
        self.forward = float(cfg.get('forward', 0.03))
        self.margin = float(cfg.get('margin', 0.014))
        self.band = float(cfg.get('band', 0.095))
        self.hang = cfg.get('hang')
        self.posed_band = set(cfg.get('posed_band', ()))      # ring indices
        rest_world = {i: np.linalg.inv(P.model.inverse_binds[joints.index(i)]) for i in joints}
        I = P.idx
        self.rest_mid = [np.mean([rest_world[I[f'B_{s}_{b}']][:3, 3] for s in 'LR'], axis=0)
                         for b in ('Thigh', 'Calf', 'Foot')]
        prim = P.model.primitives[0]
        dom = [names[joints[j]] for j in prim['joints'][np.arange(len(prim['joints'])), prim['weights'].argmax(axis=1)]]
        rest = prim['positions']
        self.legs = np.where([any(t in d for t in ('Thigh', 'Calf', 'Foot', 'Toe')) and 'Swing' not in d for d in dom]
                             & (rest[:, 1] < 0.90))[0]
        self.leg_rest_y = rest[self.legs, 1]
        legdom = [dom[v] for v in self.legs]
        self.knee_up = np.array([('Thigh' in d) or ('Calf' in d and y > 0.40) for d, y in zip(legdom, self.leg_rest_y)])
        # push-out: skirt vertices (dominated by a cage point) with their cage weights, the leg skin probe set
        self.prim = prim
        self.skirt_v = np.where([d.startswith('Skirt_') for d in dom])[0]
        order = sorted(self.nodes())
        self.order = order
        col = {node: c for c, node in enumerate(order)}
        cw = np.zeros((len(self.skirt_v), len(order)))
        for r, v in enumerate(self.skirt_v):
            for j, w in zip(prim['joints'][v], prim['weights'][v]):
                node = joints[j]
                if w > 0 and node in col:
                    cw[r, col[node]] += w
        self.cw = cw
        self.leg_probe = np.where([d.startswith('B_') and any(t in d for t in ('Thigh', 'Calf', 'Foot', 'Toe'))
                                   for d in dom])[0]
        self.passes = int(cfg.get('push_passes', 8))
        self.knee_out = float(cfg.get("knee_out", 0.0))
        self.floor = cfg.get('floor')
        self.knee_margin = float(cfg.get("knee_margin", 0.002))
        self.report = {'push_max_m': 0.0, 'residual_mm': 0.0}

    def nodes(self):
        return {i for r in self.rings for i in r.values()}

    def pose(self, worlds):
        P = self.P
        I = P.idx
        out = worlds.copy()
        for n, W in enumerate(worlds):
            D = W[I['B_Pelvis']] @ self.ibm_pelvis
            Rp = D[:3, :3] / np.linalg.norm(D[:3, :3], axis=0)
            mid = [np.mean([W[I[f'B_{s}_{b}'], :3, 3] for s in 'LR'], axis=0) for b in ('Thigh', 'Calf', 'Foot')]
            skin = P.model.skinned_positions(W)[0][0][self.legs]
            for j, (ring, z) in enumerate(zip(self.rings, self.levels)):
                rest_c = np.array([0.0, z, self.forward])
                R, C = Rp, D[:3, :3] @ rest_c + D[:3, 3]
                if j > 0:
                    if z >= self.rest_mid[1][1]:
                        a0, a1, b0, b1 = self.rest_mid[0], self.rest_mid[1], mid[0], mid[1]
                    else:
                        a0, a1, b0, b1 = self.rest_mid[1], self.rest_mid[2], mid[1], mid[2]
                    t = (a0[1] - z) / (a0[1] - a1[1])
                    rc = a0 + t * (a1 - a0)
                    pc = b0 + t * (b1 - b0)
                    R2 = rotation_between(Rp @ (a1 - a0), b1 - b0) @ Rp
                    C2 = pc + R2 @ (rest_c - rc)
                    blend = float(np.clip((0.955 - z) / 0.10, 0, 1))
                    Cp = C
                    C = (1 - blend) * C + blend * C2
                    if self.hang is not None and C[1] > Cp[1] + self.hang:
                        # (h05) `hang`: a ring hangs no higher than this above its pelvis-carried place (a sprint's
                        # high knee and heel kick lifted the legs' mid-line and bagged the lower skirt)
                        C = C.copy()
                        C[1] = Cp[1] + self.hang
                    q = glb_pose.slerp(glb_pose.matrix_quaternion(Rp), glb_pose.matrix_quaternion(R2), blend)
                    R = glb_pose.quaternion_matrix(q)
                rx, ry = self.rx, self.ry
                if j in self.posed_band:
                    # (h05) the leg skin at the ring's posed height (its frame's y), not at its rest height: a lifted
                    # knee is held by the ring it reaches
                    local = (skin - C) @ R
                    band = (np.abs(local[:, 1]) < self.band) & self.knee_up
                    local = local[band]
                else:
                    band = np.abs(self.leg_rest_y - z) < self.band
                    local = (skin[band] - C) @ R
                if band.any():
                    rx = max(rx, float(np.abs(local[:, 0]).max()) + self.margin)
                    ry = max(ry, float(np.abs(local[:, 2]).max()) + self.margin)
                for k, node in ring.items():
                    a = k * 2 * np.pi / self.count
                    target = C + R @ np.array([rx * np.cos(a), 0.0, -ry * np.sin(a)])
                    Dk = np.eye(4)
                    Dk[:3, :3] = R
                    Dk[:3, 3] = target - R @ self.bind[node][:3, 3]
                    out[n][node] = Dk @ self.bind[node]
            out[n] = self.push(out[n])
        return out

    def push(self, W):
        from compose_gait import vertex_normals
        shifts = np.zeros((len(self.order), 3))
        base = {node: W[node].copy() for node in self.order}
        depth_max = 0.0
        for _ in range(self.passes):
            pts = self.P.model.skinned_positions(W)[0][0]
            nrm = vertex_normals(pts, self.prim['triangles'])
            legs = self.leg_probe
            d, j = cKDTree(pts[legs]).query(pts[self.skirt_v])
            n = nrm[legs][j]
            depth = np.einsum('ij,ij->i', pts[self.skirt_v] - pts[legs][j], n)
            inside = (d < 0.04) & (depth < -0.002)
            ask = np.where(inside[:, None], n * (-depth[:, None] + 0.0015), 0.0)
            depth_max = float(-depth[inside].min()) if inside.any() else 0.0
            if self.knee_out:
                # (h05) knees out through the cloth: skin within knee_out m of a knee joint in front of its nearest
                # skirt vertex (along that vertex's normal turned away from the body's vertical axis) pushes that
                # vertex out past it (+ knee_margin, 2 mm)
                I = self.P.idx
                sp = pts[self.skirt_v]
                sn = nrm[self.skirt_v]
                axis = W[I['B_Pelvis'], :3, 3]
                radial = sp - axis
                radial[:, 1] = 0.0
                sn = np.where((np.einsum('ij,ij->i', sn, radial) < 0)[:, None], -sn, sn)
                tree = cKDTree(sp)
                for side in 'LR':
                    knee = W[I[f'B_{side}_Calf'], :3, 3]
                    near = self.leg_probe[np.linalg.norm(pts[self.leg_probe] - knee, axis=1) < self.knee_out]
                    dk, jk = tree.query(pts[near])
                    out = np.einsum('ij,ij->i', pts[near] - sp[jk], sn[jk])
                    hit = (dk < 0.05) & (out > 0.0)
                    for v, o in zip(jk[hit], out[hit]):
                        want = sn[v] * (o + self.knee_margin)
                        if np.linalg.norm(want) > np.linalg.norm(ask[v]):
                            ask[v] = want
                            inside[v] = True
                        depth_max = max(depth_max, float(o))
            if self.floor is not None:
                # (h05) the hem kept above the floor: a skirt vertex below `floor` m asks to rise to it
                low = pts[self.skirt_v, 1] < self.floor
                rise = np.zeros_like(ask)
                rise[:, 1] = np.maximum(self.floor + 0.002 - pts[self.skirt_v, 1], 0.0)
                ask = np.where((low & (rise[:, 1] > ask[:, 1]))[:, None], rise, ask)
                inside = inside | low
            if not inside.any():
                break
            w = self.cw * inside[:, None]
            den = w.sum(axis=0)
            cor = w.T @ ask
            move = np.where(den[:, None] > 0, cor / np.maximum(den[:, None], 1e-9), 0.0) * 0.75
            shifts += move
            for c, node in enumerate(self.order):
                W[node] = base[node].copy()
                W[node][:3, 3] += shifts[c]
        self.report['push_max_m'] = max(self.report['push_max_m'], float(np.linalg.norm(shifts, axis=1).max()))
        self.report['residual_mm'] = max(self.report['residual_mm'], 1000 * depth_max)
        return W
