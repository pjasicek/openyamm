#!/usr/bin/env python3
"""Dwarf copy (2026-11-04 fix pass, mm9_dwarf_reduce_claude): node MP_NODE=Dwarf, DwarfWeapon kept whole (MP_KEPT_PRIMS), chart
guard MP_CHART=1, texture guard on the three tier base colours baked from the ramps (tex_extract.py, work/tex_list.json),
no linings cut (all lined faces are kept faces; sets from glb_sets.py). The Giant's docstring follows.

Giant copy (2026-11-04 fix pass, mm9_giant_reduce_claude): node Giant, the mallet primitive kept whole (replaced afterwards by
the rebuilt mallet), chart guard on (MP_CHART=1), texture guard on the body base colour + region mask and both tier head
images (work/tex_list.json), sets from scripts/giant_sets.py. The Mummy's docstring follows.

Mummy copy (2026-11-04, mm9_mummy_reduce_claude) of the Lesser Demon's copy (seam slides, MP_SEAM_GROUPS): node MP_NODE
(default Mummy), the Zombie's per-tier texture guard (work/tex_list.json: three tier base colours per primitive, tex_extract.py),
no linings, a chart guard (MP_CHART=1: new UV triangles stay on the source charts), a texture stretch guard (MP_ANISO, max anisotropy of a new face's 3D -> UV map), texture weight of the 5-D rest quadric from MP_W5 (default 1; the brief's 3-8 against smeared painted details).
Lesser Demon: no kept primitive, one texture tier, no linings (sets from make_sets.py). Original docstring follows.

Pose-aware half-edge collapse of the Highwayman's LOD0 primitives (no new vertices). Copied from
mm9_banshee_reduce_claude/scripts/mpqem.py (the brief's route for cloth that is flat at rest but curves in motion); the
Highwayman changes are at the end of this docstring and in main().

Why not the MeshLab ladder: the dress and the cloak are lattice cloth that bends and turns over in every clip. A rest-pose
quadric merges triangles that are flat at rest and curved in pose (the first ladder: 61 mm at 92 % on the wings in
AttackRanged, 39 mm at 70 % on the dress in Death). Here every collapse is scored over the clips: one plane quadric per
sampled pose (10 Hz, every clip) plus a 5-D rest quadric of position and UV (texture drift), so a collapse is cheap only
where the cloth stays flat in every pose and the texture does not slide.

Half-edge collapse moves a vertex onto a neighbour: every output corner is an existing GLB vertex of the source, so
positions, UVs, normals, joints and weights stay exactly the source's (no weight transfer at all).
Locked: open-boundary vertices (hem, waist, primitive borders), UV/normal seams (a topological vertex with more than one
GLB vertex), non-manifold edges, every vertex of a kept face. Kept faces: all of Head, Neck, HairL, HairR; on the arms the
hands with fingers and claws (dominant Zhand*/Zfing*) and the sleeve within CUFF of the wrist rim.
Checks per collapse: link condition, no normal flip at rest (dot >= 0.5) or in any pose (dot >= 0.2), no UV flip,
triangle quality not below min(0.2, old).

Usage: mpqem.py <runtime_lod0.glb> <ratio,...> [scales g:s,...]  -> work/mp_r<NN>.npz (per primitive index arrays into
the GLB's own vertices) and work/mesh_r<NN>.npz (the same faces on work/mesh_in.npz for reduce_ladder.py).

Highwayman (2026-11-04): source = the installed GLB (before/mm9_highwayman.glb, LOD0 node Highwayman), sets per GLB face from
work/glb_sets_<SETS>.npz (glb_sets.py): kept faces lock their vertices; each primitive is cut per group label on its own
(0 = the ladder ratio, others = MP_GROUPS ratios, e.g. 1:0.7,2:0.7,3:0.75,4:0.7: hands, hair, skirt, boots; group borders
are open edges of the subset, so they stay); HwWeapon_A is kept whole. Linings (finish_hw's inner copies) are not cut: the
vertices on the border of the lined outer region are locked, so every surviving lined outer face keeps three vertices that
have a lining twin, and the lining is re-emitted as the reversed faces of those twins (their GLB vertices: offset
position, dark texel, same weights, all exact). Usage: mpqem.py <glb> <ratio,...>   (env SETS, MP_GROUPS)"""
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
import bglbio as glbio  # noqa: E402

CUFF = 0.045
KEPT_PRIMS = tuple(x for x in __import__('os').environ.get('MP_KEPT_PRIMS', 'DwarfWeapon').split(',') if x)
HZ = 10.0
W5 = float(__import__('os').environ.get('MP_W5', '1.0'))
MAXW = float(__import__('os').environ.get('MP_MAXW', '0.1'))
TEX_MAX = float(__import__('os').environ.get('MP_TEX_MAX', '70'))      # 0-255 mean RGB difference, any sample, worst tier
TEX_MEAN = float(__import__('os').environ.get('MP_TEX_MEAN', '30'))    # mean over a collapse's samples
SEAM_GROUPS = {int(x) for x in __import__('os').environ.get('MP_SEAM_GROUPS', '').split(',') if x}
TEX_BARY = np.array([[1, 1, 1], [4, 1, 1], [1, 4, 1], [1, 1, 4], [1, 1, 0], [0, 1, 1], [1, 0, 1]], float)
TEX_BARY /= TEX_BARY.sum(1, keepdims=True)


def cross2(a, b):
    return a[..., 0] * b[..., 1] - a[..., 1] * b[..., 0]


def tri_normals(X, T):
    n = np.cross(X[..., T[:, 1], :] - X[..., T[:, 0], :], X[..., T[:, 2], :] - X[..., T[:, 0], :])
    return n


ANISO = float(__import__('os').environ.get('MP_ANISO', '0'))


def aniso(p, u):
    """sigma max / sigma min of the 3D -> UV map of one triangle (p: 3x3 rest corners, u: 3x2 UVs)"""
    e1, e2 = p[1] - p[0], p[2] - p[0]; n = np.cross(e1, e2); A = np.linalg.norm(n)
    if A < 1e-20:
        return 1e9
    x = e1 / max(np.linalg.norm(e1), 1e-20); y = np.cross(n / A, x)
    Pm = np.array([[e1 @ x, e2 @ x], [0.0, e2 @ y]]); Um = np.stack([u[1] - u[0], u[2] - u[0]], 1)
    s = np.linalg.svd(Um @ np.linalg.inv(Pm), compute_uv=False)
    return s[0] / max(s[1], 1e-12)


CHART = {}
_k = 8; _i, _j = np.meshgrid(np.arange(_k + 1), np.arange(_k + 1)); _m = _i + _j <= _k
CHART_W = np.stack([_i[_m], _j[_m], _k - _i[_m] - _j[_m]], 1) / _k


def chart_masks(prims, res=2048, dil=2):
    """per primitive: rasterised coverage of its source UV triangles (MP_CHART=1)"""
    from PIL import Image, ImageDraw
    from scipy import ndimage
    out = {}
    for pr in prims:
        im = Image.new('L', (res, res)); d = ImageDraw.Draw(im); U = pr['TEXCOORD_0'].astype(np.float64)
        for t in pr['T']:
            d.polygon([tuple(U[k] * res) for k in t], fill=255)
        out[pr['material']] = ndimage.binary_dilation(np.asarray(im) > 0, iterations=dil)
    return out


def quality(p):
    a = np.linalg.norm(np.cross(p[1] - p[0], p[2] - p[0])) / 2
    s = ((p[1] - p[0]) ** 2).sum() + ((p[2] - p[1]) ** 2).sum() + ((p[0] - p[2]) ** 2).sum()
    return 4 * np.sqrt(3) * a / max(s, 1e-20)


class Prim:
    def __init__(self, name, P, UV, T, J, Wt, posed, keep_face, lockv=None, tex=None, seams=False):
        self.name = name; self.tex = tex; self.seams = seams; self.chart = CHART.get(name.split('/')[0]) if CHART else None
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
        self.seam = np.array([len(x) > 1 for x in glbs])
        for v in range(nt):
            if len(glbs[v]) > (2 if seams else 1):
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

    def chart_ok(self, uv):
        R = self.chart.shape[0]
        s = CHART_W @ uv
        x = np.clip((s[:, 0] * R).astype(int), 0, R - 1); y = np.clip((s[:, 1] * R).astype(int), 0, R - 1)
        return bool(self.chart[y, x].all())

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
        # GLB copy of u -> GLB copy of v per chart, from the two faces on the edge (Lesser Demon: a UV-seam vertex with two
        # copies may slide along its seam onto the next seam vertex when both charts agree; MP_SEAM_GROUPS)
        mp = {}
        for f in edge:
            a, b_ = self.glb_at(f, u), self.glb_at(f, v)
            if mp.get(a, b_) != b_:
                return None
            mp[a] = b_
        if len(set(mp.values())) != len(mp):
            return None
        moved = [f for f in fu if f not in edge]
        if not moved:
            return None
        if any(self.glb_at(f, u) not in mp for f in moved):
            return None
        if len(mp) > 1 and not (self.seam[u] and self.seam[v]):
            return None
        gv = next(iter(mp.values()))
        Tm = self.TF[moved].copy(); Tm[Tm == u] = v
        Gm = self.T[moved].copy()
        for i, f in enumerate(moved):
            k = int(np.flatnonzero(self.TF[f] == u)[0]); Gm[i, k] = mp[int(self.T[f, k])]
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
            # Mummy: texture stretch guard (MP_ANISO): a new face may not stretch the texture more anisotropically than
            # max(MP_ANISO, the face it replaces); the first build smeared a painted band into a chevron on the forearm
            if ANISO > 0 and aniso(X[t], U[g]) > max(ANISO, aniso(X[old], U[go])):
                return None
            # Mummy: chart guard (MP_CHART): every sample of the new face's UV triangle must lie on the source's painted charts
            # (installed UV triangles rasterised, dilated 2 texels); the first build had 204 faces reaching into gutters or
            # other islands (a smeared chevron on the Embalmed forearm) that the 7-sample texture guard missed
            if self.chart is not None and not self.chart_ok(U[g]):
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
        if len(mp) == 1:
            h5 = np.concatenate([X[v], self.s * self.UV[gv], [1.0]])
            cost += W5 * float(h5 @ self.Q5[u] @ h5)
        else:   # seam slide: each face round u against its own chart's 5-D plane (the summed quadric mixes both charts)
            for f in fu:
                g = self.T[f]; pts = [np.concatenate([X[self.TF[f, k]], self.s * self.UV[g[k]]]) for k in range(3)]
                h5 = np.concatenate([X[v], self.s * self.UV[mp[self.glb_at(f, u)]], [1.0]])
                cost += W5 * float(h5 @ self._q5(pts) @ h5)
        return max(cost, 0.0), mp

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
                self.TF[f, k] = v; self.T[f, k] = gv[int(self.T[f, k])]
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
    gratios = {int(k): float(v) for k, v in (kv.split(':') for kv in os.environ.get('MP_GROUPS', '').split(',') if kv)}
    sets = np.load(HERE / 'work' / f"glb_sets_{os.environ.get('SETS', 'a')}.npz")
    g = Glb(str(glb_path)); model = Model(g)
    doc, binary = glbio.read(glb_path)
    node = next(n for n in doc['nodes'] if n.get('name') == os.environ.get('MP_NODE', 'Dwarf') and 'mesh' in n)
    prims = glbio.prims(doc, binary, node['mesh'])
    poses = []
    for clip in model.clips:
        t1 = model.clip_times(clip)[-1]
        for t in np.append(np.arange(0, t1, 1 / HZ), t1):
            poses.append([p for p, _ in model.skinned_positions(model.world(model.sample(clip, t)))])
    S = len(poses); print('POSES', S, flush=True)
    d_in = np.load(HERE / 'work' / 'mesh_in.npz')
    bl_tree = cKDTree(d_in['verts'])
    allp = np.concatenate([pr['POSITION'].astype(np.float64) for pr in prims])
    allb = np.c_[allp[:, 0], -allp[:, 2], allp[:, 1]]
    offset = d_in['verts'].min(0) - allb.min(0)              # the importer re-bases the skinned mesh under its rig
    print('BLENDER OFFSET', offset.round(6))
    nf = [len(pr['T']) for pr in prims]; off = np.cumsum([0] + nf)
    from PIL import Image
    from scipy import ndimage
    TEX = {}
    if os.environ.get('MP_TEX', '1') == '1':
        tl = json.loads((HERE / 'work' / 'tex_list.json').read_text())
        for pr in prims:
            # Mummy: per-tier images (tex_extract.py), the guard takes the worst tier (dwarf: the kept axe has none)
            if pr['material'] not in tl:
                continue
            TEX[pr['material']] = [ndimage.gaussian_filter(np.asarray(Image.open(HERE / 'work' / f).convert('RGB'), np.float32), (1.5, 1.5, 0)) for f in tl[pr['material']]]
    if os.environ.get('MP_CHART', '0') == '1':
        CHART.update(chart_masks(prims)); print('CHART masks', list(CHART), flush=True)
    for r in ratios:
        log = []; out = {}; bl_faces = []; bl_wuv = []
        for pi, pr in enumerate(prims):
            name = pr['material']; T = pr['T']; sl = slice(off[pi], off[pi + 1])
            keep, group, lining, lined = sets['keep'][sl], sets['group'][sl], sets['lining'][sl], sets['lined'][sl]
            assert len(keep) == len(T)
            J = pr['JOINTS_0']; Wt = pr['WEIGHTS_0'].astype(np.float64); P = pr['POSITION'].astype(np.float64)
            if name in KEPT_PRIMS:
                out[name] = T; log.append(f'{name}: kept whole')
            else:
                posed = np.stack([pz[pi] for pz in poses])
                # lined-region border: GLB vertices (by position) on both a lined and an unlined outer face
                key = np.round(P, 6); _, tp = np.unique(key, axis=0, return_inverse=True); tp = tp.reshape(-1)
                inl = np.zeros(tp.max() + 1, bool); inl[tp[T[lined]].ravel()] = True
                inu = np.zeros(tp.max() + 1, bool); inu[tp[T[~lined & ~lining]].ravel()] = True
                lockv = (inl & inu)[tp]
                newT, newI = [T[keep & ~lining]], [np.flatnonzero(keep & ~lining)]
                for gl in np.unique(group[~keep & ~lining]):
                    sub = np.flatnonzero(~keep & ~lining & (group == gl))
                    ratio = r if gl == 0 else gratios.get(int(gl), 1.0)
                    if ratio >= 1.0:
                        newT.append(T[sub]); newI.append(sub); log.append(f'{name}/{gl}: kept whole ({len(sub)})'); continue
                    prim = Prim(f'{name}/{gl}', P, pr['TEXCOORD_0'].astype(np.float64), T[sub].copy(), J, Wt, posed,
                                np.zeros(len(sub), bool), lockv, TEX.get(name), seams=int(gl) in SEAM_GROUPS)
                    t_, i_ = prim.run(ratio, log); newT.append(t_); newI.append(sub[i_])
                newT, newI = np.concatenate(newT), np.concatenate(newI)
                if lining.any():
                    # twins keyed like Prim's topology (position, joints, weights): coincident centre-seam vertices with
                    # other weights have their own lining twins
                    _, tp = np.unique(np.concatenate([np.round(P, 6), J.astype(np.float64), np.round(Wt, 4)], 1), axis=0,
                                      return_inverse=True); tp = tp.reshape(-1)
                    # twins: finish_hw put each lining vertex 3 mm inside its outer vertex along the area-weighted normal
                    # of the lined faces round it; that rule predicts every lining vertex to 0.00003 mm (a few round the
                    # two unmatched collar faces to 1.2 mm), so each lined outer vertex takes the lining vertex nearest its
                    # prediction
                    lf = np.flatnonzero(lining); of = np.flatnonzero(lined)
                    lv = np.unique(T[lf]); ov = np.unique(T[of])
                    _, pk = np.unique(np.round(P, 5), axis=0, return_inverse=True); pk = pk.reshape(-1)
                    fn = np.cross(P[T[of, 1]] - P[T[of, 0]], P[T[of, 2]] - P[T[of, 0]]) / 2
                    Ns = np.zeros((pk.max() + 1, 3))
                    for c in range(3):
                        np.add.at(Ns, pk[T[of, c]], fn)
                    n_ = Ns[pk[ov]]; n_ /= np.linalg.norm(n_, axis=1, keepdims=True)
                    dd, q = cKDTree(P[lv]).query(P[ov] - 0.003 * n_)
                    twin = -np.ones(tp.max() + 1, np.int64); resid = np.full(tp.max() + 1, 9.0)
                    for j, a, e in zip(ov, lv[q], dd):
                        if e < resid[tp[j]]:
                            twin[tp[j]] = a; resid[tp[j]] = e
                    miss = 0
                    log.append(f'{name}: twin residual max {dd.max() * 1000:.2f} mm, p99 {np.percentile(dd, 99) * 1000:.2f} mm')
                    log.append(f'{name}: twins by nearest lining vertex {miss}')
                    sel = newT[lined[newI]]
                    tw = twin[tp[sel]]
                    assert (tw >= 0).all(), f'{name}: lined faces lost a twin ({int((tw < 0).any(1).sum())})'
                    linT = tw[:, ::-1]
                    log.append(f'{name}: lining {int(lining.sum())} -> {len(linT)}')
                    newT = np.concatenate([newT, linT])
                out[name] = newT
            newT = out[name]
            pb = np.c_[P[:, 0], -P[:, 2], P[:, 1]] + offset
            dist, bid = bl_tree.query(pb)
            assert dist.max() < 1e-4, (name, dist.max())   # float32 rest positions vs the Blender import (2.6e-5 m on the demon)
            bf = bid[newT]
            ok = (bf[:, 0] != bf[:, 1]) & (bf[:, 1] != bf[:, 2]) & (bf[:, 0] != bf[:, 2])
            uv = pr['TEXCOORD_0'].astype(np.float64)
            w = np.stack([uv[newT][..., 0] + 2.0 * pi, 1.0 - uv[newT][..., 1]], -1)
            bl_faces.append(bf[ok]); bl_wuv.append(w[ok].reshape(-1, 2))
        tag = int(round(r * 100))
        np.savez(HERE / 'work' / f'mp_r{tag}.npz', **out)
        F = np.concatenate(bl_faces); used = np.unique(F); m = -np.ones(len(d_in['verts']), np.int64); m[used] = np.arange(len(used))
        np.savez(HERE / 'work' / f'mesh_r{tag}.npz', verts=d_in['verts'][used], faces=m[F], wuv=np.concatenate(bl_wuv),
                 src_index=used)
        total = sum(len(v) for v in out.values())
        print('STEP', r, 'glb tris', total, 'blender tris', len(F), flush=True)
        for line in log:
            print('  ', line, flush=True)
        (HERE / 'work' / f'mp_r{tag}.json').write_text(json.dumps({'ratio': r, 'groups': gratios, 'log': log,
                                                                   'tris': {k: len(v) for k, v in out.items()}}, indent=1))


if __name__ == '__main__':
    main()
