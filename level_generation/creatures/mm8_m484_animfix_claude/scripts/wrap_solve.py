#!/usr/bin/env python3
"""The MM8 Minotaur Peasant's wrap cage re-projected for a new clip (package h20).

`mm8_m488` hangs its short wrap on a 48-control surface cage (`Wrap_<row>_<col>`, rows 5/9/14 x 16 columns, children of
the pelvis, translation only). Its project (`../../mm8_m488_claude/scripts/wrap_cage.py`) fitted the cage per frame to
a thigh-following target, then projected it out of the skin: a wrap vertex is inside when the nearest skin face faces
away from it and a parity ray (Blender (1, .317, .193)) crosses the skin an odd number of times; it then needs the
distance to the skin along its outward radial (from the pelvis axis, through y = .027 m in Blender) plus a margin
(Running 0.05 m, other clips 0.018 m); a vertex outside but closer than 2/3 of the margin to a face that looks outward
needs the rest of the margin. Each control moves out along its own radial by the largest need of its vertices divided by
their weighted outward agreement; 20 passes; then a (1, 2, 1) / 4 loop smoothing and one more projection.

A copy of the new clip's base (`Running`, phase-aligned by the composer) carries offsets fitted to the base clip's
legs, so this starts from them and adds only the outward moves the new legs need. Coordinates are glTF's (+Y up,
+Z forward): the Blender radial (x, y - .027, 0) is (x, 0, z + .027) here and the parity ray (1, .193, -.317).
"""
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

from gaitlib import glb_pose
from kilt_solve import Surface, pose_points

PARITY = np.array([1.0, 0.193, -0.317]) / np.linalg.norm([1.0, 0.193, -0.317])


def setup(P, cfg):
    prefix = cfg.get('prefix', 'Wrap_')
    names = [n['name'] for n in P.nodes]
    prim = P.model.primitives[0]
    joints = np.asarray(P.model.joints)
    W, J, T = prim['weights'], prim['joints'], prim['triangles']
    controls = [j for j in range(len(joints)) if names[joints[j]].startswith(prefix)]
    A = np.zeros((len(W), len(controls)))
    for c, j in enumerate(controls):
        A[:, c] = (W * (J == j)).sum(axis=1)
    wrap = np.where(A.sum(axis=1) > 0.05)[0]           # the project's `active` vertices
    # the skin: the connected piece (vertices welded by position) with the most triangles
    n = len(W)
    _, weld = np.unique(np.round(prim['positions'], 5), axis=0, return_inverse=True)
    weld = weld.ravel()
    e = np.concatenate([T[:, [0, 1]], T[:, [1, 2]]])
    graph = coo_matrix((np.ones(len(e)), (weld[e[:, 0]], weld[e[:, 1]])), shape=(n, n))
    _, label = connected_components(graph, directed=False)
    label = label[weld]
    skin_label = np.bincount(label[T[:, 0]]).argmax()
    skin = T[label[T[:, 0]] == skin_label]
    rest = prim['positions']
    radial = rest.copy()
    radial[:, 1] = 0.0
    radial[:, 2] += 0.027
    radial /= np.maximum(np.linalg.norm(radial, axis=1, keepdims=True), 1e-12)
    pel = P.idx['B_Pelvis']
    bind = {int(joints[j]): np.linalg.inv(P.model.inverse_binds[j]) for j in range(len(joints))}
    heads = np.array([bind[int(joints[j])][:3, 3] for j in controls])
    dirs = heads.copy()
    dirs[:, 1] = 0.0
    dirs[:, 2] += 0.027
    dirs /= np.maximum(np.linalg.norm(dirs, axis=1, keepdims=True), 1e-12)
    S = {'controls': [int(joints[j]) for j in controls], 'A': A[wrap], 'wrap': wrap, 'skin': skin,
         'radial': radial[wrap], 'dirs': dirs, 'pelvis_bind_rot': bind[pel][:3, :3],
         'sample_idx': np.stack([wrap] * 3, axis=1), 'sample_w': np.tile([1.0, 0.0, 0.0], (len(wrap), 1))}
    if cfg.get('face_samples'):
        # (h20) the reduced wrap has 448 cage vertices: a knee passes between them, so the centroids and edge
        # midpoints of its triangles are tested too (their weights and radials interpolated)
        on = np.zeros(n, bool)
        on[wrap] = True
        wt = T[on[T].all(axis=1)]
        edges = np.unique(np.sort(np.concatenate([wt[:, [0, 1]], wt[:, [1, 2]], wt[:, [2, 0]]]), axis=1), axis=0)
        idx = np.concatenate([S['sample_idx'], wt, np.concatenate([edges, edges[:, :1]], axis=1)])
        w = np.concatenate([S['sample_w'], np.full((len(wt), 3), 1.0 / 3), np.tile([0.5, 0.5, 0.0], (len(edges), 1))])
        S['sample_idx'], S['sample_w'] = idx, w
        S['A'] = np.einsum('sk,skc->sc', w, A[idx])
        r = np.einsum('sk,skc->sc', w, radial[idx])
        S['radial'] = r / np.maximum(np.linalg.norm(r, axis=1, keepdims=True), 1e-12)
    return S


def samples(S, pts):
    return np.einsum('sk,skc->sc', S['sample_w'], pts[S['sample_idx']])


def ray_hits(origins, direction, a, b, c):
    """Distances (rays, triangles) along rays origins + t direction to their crossings with triangles; inf if none.
    direction: one (3,) vector or one per ray (rays, 3)."""
    e1, e2 = b - a, c - a
    d = np.broadcast_to(direction, origins.shape)
    out = np.full((len(origins), len(a)), np.inf)
    for s in range(0, len(origins), 256):
        o, dd = origins[s:s + 256, None, :], d[s:s + 256, None, :]
        p = np.cross(dd, e2[None])
        det = np.einsum('rtk,tk->rt', p, e1)
        ok = np.abs(det) > 1e-12
        inv = np.where(ok, 1.0 / np.where(ok, det, 1.0), 0.0)
        tv = o - a[None]
        u = np.einsum('rtk,rtk->rt', tv, p) * inv
        q = np.cross(tv, e1[None])
        v = np.einsum('rtk,rtk->rt', np.broadcast_to(dd, q.shape), q) * inv
        t = np.einsum('rtk,tk->rt', q, e2) * inv
        hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-6)
        out[s:s + 256] = np.where(hit, t, np.inf)
    return out


def project(C, base, A, dirs, outward, tris, surface, margin, iterations=20, min_den=0.3, C_ref=None, cap=None):
    a, b, c = tris
    count = 0
    for _ in range(iterations):
        X = base + A @ C
        dist, q, nrm = surface.nearest(X)
        facing = np.einsum('ij,ij->i', X - q, nrm)
        need = np.zeros(len(X))
        inward = (facing < 0) & (dist < 0.25)
        cand = np.where(inward)[0]
        if len(cand):
            parity = np.isfinite(ray_hits(X[cand], PARITY, a, b, c)).sum(axis=1) % 2 == 1
            inside = cand[parity]
            if len(inside):
                exit_t = ray_hits(X[inside], outward[inside], a, b, c).min(axis=1)
                need[inside] = np.where(np.isfinite(exit_t), exit_t + margin, 0.0)
        near = (~inward) & (dist < margin * 0.67) & (np.einsum('ij,ij->i', nrm, outward) > 0.3)
        need[near] = (margin - dist[near]) / np.maximum(0.3, np.einsum('ij,ij->i', nrm[near], outward[near]))
        bad = np.where(need > 0)[0]
        count = max(count, len(bad))
        if not len(bad):
            break
        agree = np.maximum(0.1, outward[bad] @ dirs.T)                       # (bad, controls)
        den = (A[bad] * agree).sum(axis=1)
        # (h20) a vertex with little cage weight (the reduced mesh's upper rows) may not throw its controls: the
        # project's need / den reached 2.4 m on Wrap_5_14 here, so den is at least `min_den`
        share = np.where(A[bad] > 0, (need[bad] / np.maximum(den, min_den))[:, None], 0.0)
        C = C + dirs * share.max(axis=0)[:, None]
        if cap is not None:
            # (h20) each control moves at most `cap` from its start
            added = np.linalg.norm(C - C_ref, axis=1)
            C = C_ref + (C - C_ref) * np.minimum(1.0, cap / np.maximum(added, 1e-9))[:, None]
    return C, count


def project_free(C, C0, base, A, outward, tris, surface, margin, iterations=40, reg=0.025, step=0.75, cap=0.35):
    """(h20) The same contact test, but the controls move freely in 3D (least squares, as kilt_solve.py) toward the
    nearest skin point + its normal x margin: a thigh raised level under the wrap needs the cloth lifted over it, and
    the project's push along the outward radial ran the length of the thigh (2.4 m on Wrap_5_14 in the Jog)."""
    a, b, c = tris
    count = 0
    for _ in range(iterations):
        X = base + A @ C
        dist, q, nrm = surface.nearest(X)
        facing = np.einsum('ij,ij->i', X - q, nrm)
        bad = np.zeros(len(X), bool)
        cand = np.where((facing < 0) & (dist < 0.25))[0]
        if len(cand):
            parity = np.isfinite(ray_hits(X[cand], PARITY, a, b, c)).sum(axis=1) % 2 == 1
            bad[cand[parity]] = True
        bad |= (facing >= 0) & (dist < margin * 0.67) & (np.einsum('ij,ij->i', nrm, outward) > 0.3)
        hit = np.where(bad)[0]
        count = max(count, len(hit))
        if not len(hit):
            break
        d = q[hit] + nrm[hit] * margin - X[hit]
        delta = np.linalg.solve(A[hit].T @ A[hit] + np.eye(A.shape[1]) * reg, A[hit].T @ d)
        C = C + delta * step
        added = np.linalg.norm(C - C0, axis=1)
        C = C0 + (C - C0) * np.minimum(1.0, cap / np.maximum(added, 1e-9))[:, None]
    return C, count


def smoothstep(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


def thigh_rule(P, S):
    """(h20) The project's thigh-following wrap target (`../../mm8_m488_claude/scripts/wrap_motion.py`) as a function
    of a pose: four waist pivots (front and back at Blender (0, .027, 1.18), left and right at the thigh heads) turn
    the cloth with the thighs (front/back about X by the mean forward thigh swing +- half their spread, +-4 deg; the
    sides by the thigh's own turn), weighted by height t (smoothstep of (1.18 - z) / .18) and side share (|x| / .18)."""
    joints = list(P.model.joints)
    bind = lambda name: np.linalg.inv(P.model.inverse_binds[joints.index(P.idx[name])])
    r = P.model.primitives[0]['positions'][S['wrap']]
    t = smoothstep((1.18 - r[:, 1]) / 0.18)
    side = smoothstep(np.abs(r[:, 0]) / 0.18)
    front = r[:, 2] > -0.027                        # Blender y < .027 (Blender y = -glTF z)
    left = r[:, 0] > 0
    heads = {s: bind(f'B_{s}_Thigh')[:3, 3] for s in 'LR'}
    rest_dir = {s: bind(f'B_{s}_Calf')[:3, 3] - heads[s] for s in 'LR'}
    centre = np.array([0.0, 1.18, -0.027])
    pel_ibm = P.model.inverse_binds[joints.index(P.idx['B_Pelvis'])]

    def target(W):
        M = W[P.idx['B_Pelvis']] @ pel_ibm                     # mesh space -> world, rigid with the pelvis
        Minv = np.linalg.inv(M)[:3, :3]
        angle, D = {}, {}
        for s in 'LR':
            d = Minv @ (W[P.idx[f'B_{s}_Calf']][:3, 3] - W[P.idx[f'B_{s}_Thigh']][:3, 3])
            angle[s] = np.arctan2(d[2], -d[1]) - np.arctan2(rest_dir[s][2], -rest_dir[s][1])
            a, b = unit3(rest_dir[s]), unit3(d)
            v, c = np.cross(a, b), float(np.dot(a, b))
            K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
            D[s] = np.eye(3) + K + K @ K / (1 + c)
        mid = (angle['L'] + angle['R']) / 2
        spread = np.sqrt((angle['L'] - angle['R']) ** 2 + 0.035 ** 2) / 2
        rot = {}
        for name, sign in (('F', 1.0), ('B', -1.0)):
            a = mid + sign * spread + sign * np.radians(4)
            # Blender Matrix.Rotation(-a, 'X') moves a hanging panel toward Blender -Y, glTF +Z (forward)
            rot[name] = np.array([[1, 0, 0], [0, np.cos(a), -np.sin(a)], [0, np.sin(a), np.cos(a)]]).T
        out = (1 - t)[:, None] * r
        for name, mask in (('F', front), ('B', ~front)):
            w = ((1 - side) * t * mask)[:, None]
            out += w * ((r - centre) @ rot[name].T + centre)
        for s, mask in (('L', left), ('R', ~left)):
            w = (side * t * mask)[:, None]
            out += w * ((r - heads[s]) @ D[s].T + heads[s])
        return out @ M[:3, :3].T + M[:3, 3], t
    return target


def unit3(v):
    return v / max(np.linalg.norm(v), 1e-12)


def solve_wrap(P, worlds, base_local, cfg, report):
    S = setup(P, cfg)
    ctrl = S['controls']
    margin = float(cfg.get('margin', 0.05))
    N = len(worlds)
    states, C0 = [], []
    rule = thigh_rule(P, S) if cfg.get('target') == 'thighs' else None
    for i in range(N):
        W = worlds[i].copy()
        for node in ctrl:
            t, _, _ = P.model.rest[node]
            local = base_local[i].get(node, P.model.rest[node])
            W[node] = W[P.parent[node]] @ glb_pose.trs_matrix(t, local[1], local[2])
        pts = pose_points(P, W)
        R = W[P.idx['B_Pelvis']][:3, :3] @ S['pelvis_bind_rot'].T
        tris = tuple(pts[S['skin'][:, k]] for k in range(3))
        states.append((samples(S, pts), tris, Surface(pts, S['skin']), S['radial'] @ R.T, S['dirs'] @ R.T,
                       [W[P.parent[node]][:3, :3] for node in ctrl]))
        if rule is not None:
            # the project's start: the cage fitted to the thigh-following target (least squares, its pinv)
            desired, t = rule(W)
            nv = len(S['wrap'])
            C0.append(np.linalg.lstsq(S['A'][:nv], desired - pts[S['wrap']], rcond=None)[0])
        else:
            C0.append(np.array([states[-1][5][c] @ (np.asarray(base_local[i].get(node, P.model.rest[node])[0])
                                                    - P.model.rest[node][0]) for c, node in enumerate(ctrl)]))
    C0 = np.array(C0)
    free = bool(cfg.get('free', False))
    cap = float(cfg.get('cap', 0.35))

    def run(C, C_ref, base, dirs, outward, tris, surface, iterations=None):
        if free:
            return project_free(C, C_ref, base, S['A'], outward, tris, surface, margin, iterations or 40, cap=cap)
        return project(C, base, S['A'], dirs, outward, tris, surface, margin, iterations or 20, C_ref=C_ref, cap=cap)

    first, solved = [], []
    for i in range(N):
        base, tris, surface, outward, dirs, _ = states[i]
        C, count = run(C0[i], C0[i], base, dirs, outward, tris, surface)
        first.append(count)
        solved.append(C)
    solved = np.array(solved)
    smooth = (np.roll(solved, 1, axis=0) + 2 * solved + np.roll(solved, -1, axis=0)) / 4
    left = []
    for i in range(N):
        base, tris, surface, outward, dirs, _ = states[i]
        smooth[i], _ = run(smooth[i], C0[i], base, dirs, outward, tris, surface)
        left.append(run(smooth[i], C0[i], base, dirs, outward, tris, surface, 1)[1])
    out = []
    for i in range(N):
        local = dict(base_local[i])
        for c, node in enumerate(ctrl):
            t, _, _ = P.model.rest[node]
            old = local.get(node, P.model.rest[node])
            local[node] = [t + states[i][5][c].T @ smooth[i][c], old[1], old[2]]
        out.append(local)
    report['wrap_solve'] = {'free': free, 'controls': len(ctrl), 'wrap_vertices': int(len(S['wrap'])),
                            'margin_m': margin, 'needing_vertices_before_max': int(max(first)),
                            'needing_vertices_after_max': int(max(left)),
                            'max_added_m': float(np.linalg.norm(smooth - C0, axis=2).max())}
    return out
