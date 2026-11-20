#!/usr/bin/env python3
"""Pose-aware half-edge collapse of the Nosferatu's LOD0 body primitive, part by part (no new vertices).
Copied from ../mm9_banshee_reduce_claude/scripts/mpqem.py (the brief's route for cloth that is flat at rest and curves in
motion); changes: parts from work/glb_parts.npz instead of primitives, a ratio per part, the head primitive and the
small parts kept whole, and zero-area UV parts (the robe and sleeve linings, one texel) skip the UV checks.

Every collapse is scored over every clip at 10 Hz (plane quadrics per pose, mean + 0.1 x max) plus a 5-D rest quadric of
position and UV. Every output corner is an existing GLB vertex: positions, UVs, normals, joints and weights stay exactly
the source's. Locked: open-boundary vertices (hem, waist, part borders), UV/normal seams, non-manifold edges.

Usage: mpqem.py <glb> <ratio,...> [part:scale,...]  -> work/mp_r<NN>.npz (per primitive index arrays into the GLB's own
vertices) and work/mesh_r<NN>.npz (the same faces on work/mesh_in.npz for reduce_ladder.py)."""
import heapq
import json
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
sys.path.insert(0, str(HERE / 'scripts'))
from glb_pose import Glb, Model  # noqa: E402
import glbio  # noqa: E402

HZ = 10.0
W5 = 1.0
MAXW = float(__import__('os').environ.get('MP_MAXW', '0.1'))


def cross2(a, b):
    return a[..., 0] * b[..., 1] - a[..., 1] * b[..., 0]


def tri_normals(X, T):
    n = np.cross(X[..., T[:, 1], :] - X[..., T[:, 0], :], X[..., T[:, 2], :] - X[..., T[:, 0], :])
    return n


def quality(p):
    a = np.linalg.norm(np.cross(p[1] - p[0], p[2] - p[0])) / 2
    s = ((p[1] - p[0]) ** 2).sum() + ((p[2] - p[1]) ** 2).sum() + ((p[0] - p[2]) ** 2).sum()
    return 4 * np.sqrt(3) * a / max(s, 1e-20)


class Prim:
    def __init__(self, name, P, UV, T, J, Wt, posed, keep_face):
        self.name = name
        self.P, self.UV, self.posed = P, UV, posed            # posed: (S, n, 3) GLB vertices
        key = np.concatenate([np.round(P, 6), J.astype(np.float64), np.round(Wt, 4)], 1)
        _, topo, = np.unique(key, axis=0, return_inverse=True)[:2]
        self.topo = topo.reshape(-1)
        nt = self.topo.max() + 1
        TF = self.topo[T]
        degenerate = (TF[:, 0] == TF[:, 1]) | (TF[:, 1] == TF[:, 2]) | (TF[:, 0] == TF[:, 2])
        self.dropped = int(degenerate.sum())
        self.T = T[~degenerate].copy(); self.TF = TF[~degenerate].copy(); self.keep_face = keep_face[~degenerate]
        self.nt = nt
        # representative GLB vertex per topological vertex (positions/poses identical within a class)
        rep = np.zeros(nt, np.int64); rep[self.topo] = np.arange(len(P)); self.rep = rep
        self.X = P[rep]; self.XS = posed[:, rep]                                  # (nt,3), (S,nt,3)
        locked = np.zeros(nt, bool)
        edges = {}
        for f, t in enumerate(self.TF):
            for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
                edges.setdefault((min(a, b), max(a, b)), []).append(f)
        for (a, b), fs in edges.items():
            if len(fs) != 2:
                locked[a] = locked[b] = True
        glbs = [set() for _ in range(nt)]
        for t, g in zip(self.TF.reshape(-1), self.T.reshape(-1)):
            glbs[t].add(int(g))
        for v in range(nt):
            if len(glbs[v]) > 1:
                locked[v] = True
        locked[np.unique(self.TF[self.keep_face])] = True
        self.locked = locked
        self.alive = np.ones(len(self.TF), bool)
        self.vfaces = [set() for _ in range(nt)]
        for f, t in enumerate(self.TF):
            for v in t:
                self.vfaces[v].add(f)
        self.free0 = int((~self.keep_face).sum())
        self._quadrics()

    def _quadrics(self):
        TF = self.TF
        S = self.XS.shape[0]
        n = tri_normals(self.XS, TF)                                              # (S,f,3)
        A = np.linalg.norm(n, axis=-1, keepdims=True) / 2
        nu = n / np.maximum(2 * A, 1e-20)
        d = -(nu * self.XS[:, TF[:, 0]]).sum(-1, keepdims=True)
        p = np.concatenate([nu, d], -1)                                           # (S,f,4)
        K = A[..., None] * p[..., :, None] * p[..., None, :]                       # (S,f,4,4)
        Q = np.zeros((S, self.nt, 4, 4))
        for k in range(3):
            np.add.at(Q, (slice(None), TF[:, k]), K)
        self.Q = Q
        # 5-D rest quadric (position + UV scaled to metres), Garland-Heckbert 1998
        X = self.X; G = self.T
        a3 = np.linalg.norm(np.cross(X[TF[:, 1]] - X[TF[:, 0]], X[TF[:, 2]] - X[TF[:, 0]]), axis=1).sum()
        U = self.UV
        auv = np.abs(cross2(U[G[:, 1]] - U[G[:, 0]], U[G[:, 2]] - U[G[:, 0]])).sum()
        self.s = np.sqrt(a3 / auv) if auv > 1e-9 else 0.0     # linings: one texel, no texture to slide
        Q5 = np.zeros((self.nt, 6, 6))
        for f in range(len(TF)):
            pts = [np.concatenate([X[TF[f, k]], self.s * U[G[f, k]]]) for k in range(3)]
            Q5[TF[f]] += self._q5(pts)
        self.Q5 = Q5

    @staticmethod
    def _q5(pts):
        p0, p1, p2 = pts
        e1 = p1 - p0; l1 = np.linalg.norm(e1)
        area = np.linalg.norm(np.cross(pts[1][:3] - p0[:3], pts[2][:3] - p0[:3])) / 2
        if l1 < 1e-12:
            return np.zeros((6, 6))
        e1 /= l1
        e2 = p2 - p0 - np.dot(e1, p2 - p0) * e1; l2 = np.linalg.norm(e2)
        if l2 < 1e-12:
            return np.zeros((6, 6))
        e2 /= l2
        A = np.eye(5) - np.outer(e1, e1) - np.outer(e2, e2)
        b = np.dot(p0, e1) * e1 + np.dot(p0, e2) * e2 - p0
        c = np.dot(p0, p0) - np.dot(p0, e1) ** 2 - np.dot(p0, e2) ** 2
        M = np.zeros((6, 6)); M[:5, :5] = A; M[:5, 5] = b; M[5, :5] = b; M[5, 5] = c
        return area * M

    def neighbours(self, u):
        return {int(v) for f in self.vfaces[u] for v in self.TF[f] if v != u}

    def glb_at(self, f, v):
        k = int(np.flatnonzero(self.TF[f] == v)[0]); return int(self.T[f, k])

    def candidate(self, u, v):
        """cost of collapsing u onto v, or None when the collapse is not allowed"""
        fu = self.vfaces[u]; fv = self.vfaces[v]
        edge = fu & fv
        if len(edge) != 2:
            return None
        opp = {int(w) for f in edge for w in self.TF[f] if w != u and w != v}
        if self.neighbours(u) & self.neighbours(v) != opp:
            return None
        gvs = {self.glb_at(f, v) for f in edge}
        if len(gvs) != 1:
            return None
        gv = gvs.pop()
        moved = [f for f in fu if f not in edge]
        if not moved:
            return None
        Tm = self.TF[moved].copy(); Tm[Tm == u] = v
        Gm = self.T[moved].copy(); Gm[self.TF[moved] == u] = gv
        # rest normal, quality and UV orientation
        X = self.X
        for f, t, g in zip(moved, Tm, Gm):
            old = self.TF[f]
            n0 = np.cross(X[old[1]] - X[old[0]], X[old[2]] - X[old[0]])
            n1 = np.cross(X[t[1]] - X[t[0]], X[t[2]] - X[t[0]])
            l0, l1 = np.linalg.norm(n0), np.linalg.norm(n1)
            if l1 < 1e-12 or np.dot(n0, n1) < 0.5 * l0 * l1:
                return None
            if quality(X[t]) < min(0.2, quality(X[old])):
                return None
            U = self.UV; go = self.T[f]
            a0 = cross2(U[go[1]] - U[go[0]], U[go[2]] - U[go[0]]); a1 = cross2(U[g[1]] - U[g[0]], U[g[2]] - U[g[0]])
            if self.s > 0 and (a0 * a1 <= 0 or abs(a1) < 1e-12):
                return None
        # every pose: no flip
        XS = self.XS
        old = self.TF[moved]
        n0 = np.cross(XS[:, old[:, 1]] - XS[:, old[:, 0]], XS[:, old[:, 2]] - XS[:, old[:, 0]])
        n1 = np.cross(XS[:, Tm[:, 1]] - XS[:, Tm[:, 0]], XS[:, Tm[:, 2]] - XS[:, Tm[:, 0]])
        l0 = np.linalg.norm(n0, axis=-1); l1 = np.linalg.norm(n1, axis=-1)
        ok = (n0 * n1).sum(-1) >= 0.2 * l0 * l1
        if not np.all(ok | (l0 < 1e-10)):
            return None
        h = np.concatenate([XS[:, v], np.ones((XS.shape[0], 1))], 1)
        e = np.einsum('si,sij,sj->s', h, self.Q[:, u], h)
        cost = float(e.mean() + MAXW * e.max())       # a collapse bad in one pose (an elbow at 115 deg) is not averaged away
        h5 = np.concatenate([X[v], self.s * self.UV[gv], [1.0]])
        cost += W5 * float(h5 @ self.Q5[u] @ h5)
        return max(cost, 0.0), gv

    def run(self, ratio, log):
        target = int(round(self.free0 * ratio))
        heap = []; ver = np.zeros(self.nt, np.int64)

        def push(u):
            if self.locked[u] or not self.vfaces[u]:
                return
            best = None
            for v in self.neighbours(u):
                c = self.candidate(u, v)
                if c is not None and (best is None or c[0] < best[0]):
                    best = (c[0], v, c[1])
            if best:
                heapq.heappush(heap, (best[0], int(u), best[1], best[2], int(ver[u])))
        for u in range(self.nt):
            push(u)
        free_alive = self.free0; worst = 0.0
        while free_alive > target and heap:
            cost, u, v, gv, vv = heapq.heappop(heap)
            if vv != ver[u] or not self.vfaces[u]:
                continue
            c = self.candidate(u, v)
            if c is None or abs(c[0] - cost) > 1e-12 + 1e-6 * cost:
                ver[u] += 1; push(u); continue
            ring = self.neighbours(u)
            fu = set(self.vfaces[u]); edge = fu & self.vfaces[v]
            for f in edge:
                self.alive[f] = False
                for w in self.TF[f]:
                    self.vfaces[w].discard(f)
                free_alive -= 1
            for f in fu - edge:
                k = int(np.flatnonzero(self.TF[f] == u)[0])
                self.TF[f, k] = v; self.T[f, k] = gv
                self.vfaces[v].add(f)
            self.vfaces[u] = set()
            self.Q[:, v] += self.Q[:, u]; self.Q5[v] += self.Q5[u]
            worst = max(worst, cost)
            for w in ring | {v}:
                ver[w] += 1; push(w)
        log.append(f'{self.name}: free {self.free0} -> {free_alive} (target {target}), kept {int(self.keep_face.sum())}, '
                   f'dropped degenerate {self.dropped}, worst collapse rms {np.sqrt(worst) * 1000:.2f} mm')
        return self.T[self.alive]


KEEP_PARTS = ('neckin', 'trim', 'buckle', 'pendant', 'cuffs', 'slining', 'feet')
CUT_PARTS = ('robe', 'rlining', 'torso', 'belt', 'hands', 'sleeves')


def main():
    glb_path = Path(sys.argv[1]); ratios = [float(r) for r in sys.argv[2].split(',')]
    scales = {k: float(v) for k, v in (kv.split(':') for kv in (sys.argv[3] if len(sys.argv) > 3 else '').split(',') if kv)}
    tag_sfx = __import__('os').environ.get('MP_TAG', '')
    g = Glb(str(glb_path)); model = Model(g)
    doc, binary = glbio.read(glb_path)
    prims = glbio.prims(doc, binary, 0)
    gp = np.load(HERE / 'work' / 'glb_parts.npz'); pnames = [str(x) for x in gp['names']]
    body_part = gp['part'][gp['mat'] == 0]
    keepf = np.load(HERE / 'work' / __import__('os').environ['MP_KEEP']) if __import__('os').environ.get('MP_KEEP') else np.zeros(len(body_part), bool)
    print('KEEP faces', int(keepf.sum()), flush=True)
    poses = []
    for clip in model.clips:
        t1 = model.clip_times(clip)[-1]
        for t in np.append(np.arange(0, t1, 1 / HZ), t1):
            poses.append([p for p, _ in model.skinned_positions(model.world(model.sample(clip, t)))])
    S = len(poses); print('POSES', S, flush=True)
    d_in = np.load(HERE / 'work' / 'mesh_in.npz')
    bl_tree = cKDTree(d_in['verts'])
    bl_mats = list(np.load(HERE / 'work' / 'faces_info.npz')['mats'])
    allp = np.concatenate([pr['POSITION'].astype(np.float64) for pr in prims])
    allb = np.c_[allp[:, 0], -allp[:, 2], allp[:, 1]]
    offset = d_in['verts'].min(0) - allb.min(0)
    print('BLENDER OFFSET', offset.round(6))
    for r in ratios:
        log = []; out = {}; bl_faces = []; bl_wuv = []; bl_group = []
        for pi, pr in enumerate(prims):
            name = pr['material']; T = pr['T']
            if pi == 1:
                newT = T; log.append(f'{name}: kept whole (head set)')
            else:
                J = pr['JOINTS_0']; Wt = pr['WEIGHTS_0'].astype(np.float64)
                posed = np.stack([pz[pi] for pz in poses])
                parts_out = []
                for k, pn in enumerate(pnames):
                    Tk = T[body_part == k]
                    if not len(Tk):
                        continue
                    ratio = min(1.0, scales.get(pn, 1.0) * r) if pn in CUT_PARTS else 1.0
                    if ratio >= 1.0:
                        parts_out.append(Tk); log.append(f'{pn}: kept whole ({len(Tk)})'); continue
                    prim = Prim(pn, pr['POSITION'].astype(np.float64), pr['TEXCOORD_0'].astype(np.float64), Tk.copy(),
                                J, Wt, posed, keepf[body_part == k])
                    parts_out.append(prim.run(ratio, log))
                newT = np.concatenate(parts_out)
            out[name] = newT
            P = pr['POSITION'].astype(np.float64)
            pb = np.c_[P[:, 0], -P[:, 2], P[:, 1]] + offset
            dist, bid = bl_tree.query(pb)
            assert dist.max() < 1e-5, (name, dist.max())
            bf = bid[newT]
            ok = (bf[:, 0] != bf[:, 1]) & (bf[:, 1] != bf[:, 2]) & (bf[:, 0] != bf[:, 2])
            mi = bl_mats.index(name)
            uv = pr['TEXCOORD_0'].astype(np.float64)
            w = np.stack([uv[newT][..., 0] + 2.0 * mi, 1.0 - uv[newT][..., 1]], -1)
            bl_faces.append(bf[ok]); bl_wuv.append(w[ok].reshape(-1, 2)); bl_group.append(np.full(int(ok.sum()), mi))
        tag = f'{int(round(r * 100))}{tag_sfx}'
        np.savez(HERE / 'work' / f'mp_r{tag}.npz', **out)
        F = np.concatenate(bl_faces); used = np.unique(F); m = -np.ones(len(d_in['verts']), np.int64); m[used] = np.arange(len(used))
        np.savez(HERE / 'work' / f'mesh_r{tag}.npz', verts=d_in['verts'][used], faces=m[F], wuv=np.concatenate(bl_wuv),
                 group=np.concatenate(bl_group), src_index=used)
        total = sum(len(v) for v in out.values())
        print('STEP', r, tag, 'glb tris', total, 'blender tris', len(F), flush=True)
        for line in log:
            print('  ', line, flush=True)
        (HERE / 'work' / f'mp_r{tag}.json').write_text(json.dumps({'ratio': r, 'scales': scales, 'log': log,
                                                                   'tris': {k: len(v) for k, v in out.items()}}, indent=1))


if __name__ == '__main__':
    main()
