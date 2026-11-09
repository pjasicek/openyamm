#!/usr/bin/env python3
"""Pose-aware half-edge collapse of the Ghost's runtime LOD0 primitives (no new vertices). Prim class copied from
mm9_highwayman_reduce_claude/scripts/mpqem.py (itself from mm9_banshee_reduce_claude: one plane quadric per sampled pose,
10 Hz over every clip, plus a 5-D rest quadric of position and UV; link condition, no flip at rest or in any pose, no UV
flip, triangle quality; texture guard). Every output corner is an existing GLB vertex of the source, so positions, UVs,
normals, joints and weights stay exactly the source's.

Ghost (2026-11-04): source = the Ghost's own pre-mirror, pre-lining runtime LOD0
(../mm9_ghost_claude/export/mm9_ghost_runtime_lod0.glb, reproduced by build_cand.sh r100 to the installed meshes byte for
byte). The robe lining is not in it: finish_blend.py rebuilds it from the reduced robe. Sets per GLB face from
work/sets_<SETS>.npz (make_sets.py): kept faces lock their vertices; each primitive is cut per group on its own (group 0 =
the ladder ratio, others MP_GROUPS g:ratio, a ratio given as "xN" is N times the ladder ratio). GhostHead is kept whole.
Texture guard on the shared base colour (RGB and alpha: the robe's tatters and fades are alpha) and the region mask
(RGB and A: tier ramps follow it); head images are not needed (head kept).
Usage: mpqem.py <runtime_lod0.glb> <ratio,...>   (env SETS, MP_GROUPS, MP_TEX_MAX, MP_TEX_MEAN, MP_TEX)"""
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

CUFF = 0.045
KEPT_PRIMS = ('GhostHead',)
HZ = 10.0
W5 = 1.0
MAXW = float(__import__('os').environ.get('MP_MAXW', '0.1'))
TEX_MAX = float(__import__('os').environ.get('MP_TEX_MAX', '70'))      # 0-255 mean RGB difference, any sample, worst tier
TEX_MEAN = float(__import__('os').environ.get('MP_TEX_MEAN', '30'))    # mean over a collapse's samples
TEX_BARY = np.array([[1, 1, 1], [4, 1, 1], [1, 4, 1], [1, 1, 4], [1, 1, 0], [0, 1, 1], [1, 0, 1]], float)
TEX_BARY /= TEX_BARY.sum(1, keepdims=True)


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
    def __init__(self, name, P, UV, T, J, Wt, posed, keep_face, lockv=None, tex=None):
        self.name = name; self.tex = tex
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
        if lockv is not None:                                    # GLB vertices to lock (lined-region border)
            locked[self.topo[lockv]] = True
        self.keep_idx = np.flatnonzero(~degenerate)
        self.locked = locked
        self.alive = np.ones(len(self.TF), bool)
        self.vfaces = [set() for _ in range(nt)]
        for f, t in enumerate(self.TF):
            for v in t:
                self.vfaces[v].add(f)
        self.free0 = int((~self.keep_face).sum())
        self._quadrics()
        if self.tex is not None:
            self._tex_reference()

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
        self.s = np.sqrt(a3 / max(auv, 1e-20))
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

    def _colour(self, uv):
        """per tier RGB (blurred base colour) at glTF UVs (origin top left), shape (tiers, n, 3)"""
        out = []
        for im in self.tex:
            H, W = im.shape[:2]
            x = np.clip((uv[:, 0] % 1) * W, 0, W - 1).astype(int); y = np.clip((uv[:, 1] % 1) * H, 0, H - 1).astype(int)
            out.append(im[y, x])
        return np.stack(out)

    def _tex_reference(self):
        """Texture guard (Highwayman: a collapsed face whose UV triangle left its chart painted a dark wedge on the bracer
        and stepped the belt's gold edge): dense rest samples of the source surface (about 2.5 mm apart) with their colour
        in every tier; a collapse is refused when its new faces sample colours that the source does not have there."""
        X, T, U = self.X, self.TF, self.UV
        pts, nrm, col = [], [], []
        for f in range(len(T)):
            a, b, c = X[T[f]]; g = self.T[f]
            n = np.cross(b - a, c - a); A = np.linalg.norm(n) / 2
            if A < 1e-12:
                continue
            k = int(np.clip(np.sqrt(A) / 0.0025, 1, 12))
            i, j = np.meshgrid(np.arange(k + 1), np.arange(k + 1)); m = i + j <= k
            w = np.stack([i[m], j[m], k - i[m] - j[m]], 1) / k
            pts.append(w @ X[T[f]]); col.append(self._colour(w @ U[g])); nrm.append(np.repeat(n[None] / (2 * A), len(w), 0))
        self.ref_p = np.concatenate(pts); self.ref_n = np.concatenate(nrm); self.ref_c = np.concatenate(col, 1)
        self.ref_tree = cKDTree(self.ref_p)

    def tex_ok(self, Tm, Gm):
        X, U = self.X, self.UV
        B = TEX_BARY
        pos = np.einsum('sk,fkc->fsc', B, X[Tm]).reshape(-1, 3); uv = np.einsum('sk,fkc->fsc', B, U[Gm]).reshape(-1, 2)
        n = np.cross(X[Tm[:, 1]] - X[Tm[:, 0]], X[Tm[:, 2]] - X[Tm[:, 0]]); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-20)
        n = np.repeat(n, len(B), 0)
        d, idx = self.ref_tree.query(pos, 6)
        ok = (self.ref_n[idx] * n[:, None]).sum(-1) > 0.5
        best = idx[np.arange(len(idx)), np.where(ok, d, np.inf).argmin(1)]
        diff = np.abs(self._colour(uv) - self.ref_c[:, best]).mean(-1).max(0)      # worst tier per sample
        return diff.max() <= TEX_MAX and diff.mean() <= TEX_MEAN

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
            if a0 * a1 <= 0 or abs(a1) < 1e-12:
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
        if self.tex is not None and not self.tex_ok(Tm, Gm):
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
        return self.T[self.alive], self.keep_idx[self.alive]


def main():
    import os
    glb_path = Path(sys.argv[1]); ratios = [float(r) for r in sys.argv[2].split(',')]
    gspec = {int(k): v for k, v in (kv.split(':') for kv in os.environ.get('MP_GROUPS', '').split(',') if kv)}
    sets = np.load(HERE / 'work' / f"sets_{os.environ.get('SETS', 'a')}.npz")
    g = Glb(str(glb_path)); model = Model(g)
    doc, binary = glbio.read(glb_path)
    prims = glbio.prims(doc, binary, 0)
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
    offset = d_in['verts'].min(0) - allb.min(0)              # the importer re-bases the skinned mesh under its rig
    print('BLENDER OFFSET', offset.round(6))
    from PIL import Image
    from scipy import ndimage
    TEX = None
    if os.environ.get('MP_TEX', '1') == '1':
        blur = lambda a: ndimage.gaussian_filter(a.astype(np.float32), (1.5, 1.5, 0))
        base = np.asarray(Image.open(HERE / 'work' / 'img_ghost_basecolor_rgba.png').convert('RGBA'))
        mask = np.asarray(Image.open(HERE / 'work' / 'img_ghost_region_mask.png').convert('RGBA'))
        TEX = [blur(base[..., :3]), blur(np.repeat(base[..., 3:], 3, -1)), blur(mask[..., :3]), blur(np.repeat(mask[..., 3:], 3, -1))]
    for r in ratios:
        log = []; out = {}; bl_faces = []; bl_wuv = []; bl_group = []
        for pi, pr in enumerate(prims):
            name = pr['material']; T = pr['T']
            J = pr['JOINTS_0']; Wt = pr['WEIGHTS_0'].astype(np.float64); P = pr['POSITION'].astype(np.float64)
            if name in KEPT_PRIMS:
                newT = T; log.append(f'{name}: kept whole')
            else:
                keep, group = sets['keep_' + name], sets['group_' + name]
                assert len(keep) == len(T)
                posed = np.stack([pz[pi] for pz in poses])
                newT = [T[keep]]
                for gl in np.unique(group[~keep]):
                    sub = np.flatnonzero(~keep & (group == gl))
                    spec = gspec.get(int(gl), 'x1')
                    ratio = r * float(spec[1:]) if spec.startswith('x') else float(spec)
                    ratio = min(ratio, 1.0)
                    if ratio >= 1.0:
                        newT.append(T[sub]); log.append(f'{name}/{gl}: kept whole ({len(sub)})'); continue
                    prim = Prim(f'{name}/{gl}', P, pr['TEXCOORD_0'].astype(np.float64), T[sub].copy(), J, Wt, posed,
                                np.zeros(len(sub), bool), None, TEX)
                    t_, i_ = prim.run(ratio, log); newT.append(t_)
                newT = np.concatenate(newT)
            out[name] = newT
            pb = np.c_[P[:, 0], -P[:, 2], P[:, 1]] + offset
            dist, bid = bl_tree.query(pb)
            assert dist.max() < 1e-5, (name, dist.max())
            bf = bid[newT]
            ok = (bf[:, 0] != bf[:, 1]) & (bf[:, 1] != bf[:, 2]) & (bf[:, 0] != bf[:, 2])
            mi = bl_mats.index(name)
            uv = pr['TEXCOORD_0'].astype(np.float64)
            w = np.stack([uv[newT][..., 0] + 2.0 * mi, 1.0 - uv[newT][..., 1]], -1)
            bl_faces.append(bf[ok]); bl_wuv.append(w[ok].reshape(-1, 2)); bl_group.append(np.full(int(ok.sum()), mi))
        tag = int(round(r * 100))
        lab = os.environ.get('MP_LABEL', '')
        np.savez(HERE / 'work' / f'mp_{lab}r{tag}.npz', **out)
        F = np.concatenate(bl_faces); used = np.unique(F); m = -np.ones(len(d_in['verts']), np.int64); m[used] = np.arange(len(used))
        np.savez(HERE / 'work' / f'mesh_r{tag}.npz', verts=d_in['verts'][used], faces=m[F], wuv=np.concatenate(bl_wuv),
                 group=np.concatenate(bl_group), src_index=used)
        total = sum(len(v) for v in out.values())
        robe = None
        print('STEP', r, 'glb tris', total, 'blender tris', len(F), flush=True)
        for line in log:
            print('  ', line, flush=True)
        (HERE / 'work' / f'mp_{lab}r{tag}.json').write_text(json.dumps({'ratio': r, 'groups': gspec, 'log': log,
                                                                   'tris': {k: len(v) for k, v in out.items()}}, indent=1))


if __name__ == '__main__':
    main()
