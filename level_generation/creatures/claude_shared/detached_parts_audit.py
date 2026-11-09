#!/usr/bin/env python3
"""Detached-parts audit of runtime creature GLBs: parts that are not joined to the body (wings, legs, horns, fins that
float free of it in the bind pose or open a gap in some clip).

LOD0 (every mesh except LOD1..3 and shadow meshes) is welded by position and split into connected components. The
component with the largest surface is the body. Every pose is checked: the bind pose, then every clip sampled at --fps
with linear-blend skinning from floor/glb_pose.py (no Blender). Distances are signed: negative inside the other
surface, the sign taken from the face normal, or from the angle-weighted pseudo-normal of the nearest edge or corner
(a point far behind a thin plate's corner is outside it).

Root rules (--rules root, the default since 2026-10-30):
- A part is attached when its own root sits in or on an attached part that may hold it. It touches a holder when one
  of its vertices is within --threshold of the holder or inside it, or the holder's surface passes through one of its
  faces (a sleeve's rim through a large low-poly hand).
- Holders: the body and parts larger than the part (area at least --peer-ratio times its own); much smaller connectors
  (MM9 hangs heads on neck pieces and feet on thin shins); a neighbour of similar area (a peer), except that a plate
  (a fin, a scale) may not rest on a peer while a larger part lies alongside it within its own size. So a row of fins
  resting on each other above a tail has to reach the tail, while an eyeball on its stalk or a bone along an
  articulated leg keeps its peer.
- A plate standing on its holder (a sheet: thin, not a strip, filling its outline; the holder's normal at the contact
  in its plane) is judged along its base edge, as mm9_seamon_claude/scripts/fin_gates.py does: its lowest 35 % cut
  into 10 slices along the base, each slice's point closest to the holder (vertices and points along the edges), and
  the largest of those (the maximum over the base, not the closest vertex). A plate that touches at one corner while
  its base lifts off is 'lifted' and loose even when something else holds it. Slices with nothing of the holder under
  them do not count, and a plate needs the holder under half its slices (a wing spreading past a narrow root).
- In a clip a part's root is checked against the bind pose: its contact vertices at bind, against the holder it had at
  bind. Over half of them more than twice the threshold away (the median, so one corner still touching does not hide
  it) and it has 'parted' from that holder. A part touching with most of its surface (a dome inside a bell) has no root
  to part. The 90th percentile alone, one side of the root lifting, is listed as a root lift, advice that does not
  fail the audit: a rigid limb pivoting in its socket does the same.
- Loose parts that hold each other form a cluster; its break is reported once, on the member nearest an attached part
  (a 'floating' gap: its closest approach; a 'lifted' base gap; a 'parted' root gap), and the others are carried.
--rules chain is the old rule (any chain of touching parts to the body, closest vertex, symmetric distances); it
passed the Sea Monster r3's seven floating tail fins, and its smoothed-normal signs let a hand 1.3 cm off its sleeve
pass (Yrsa).

Intentionally separate pieces (eyeballs in sockets, teeth, claws, horns, spikes, hair locks) pass as long as their root
sits in or on an attached surface. Collapsed parts (scaled to zero in a clip) are skipped in that pose. A gap no camera
can see (rays from it in 96 directions all hit the model, or the floor right below it: a foot under a long dress) is
reported apart, as concealed. Attached parts larger than 5 % of the model that are rooted less than twice the
threshold in some pose are listed as shallow (only just attached).

    detached_parts_audit.py <glb...> [--fps 30] [--threshold 0.004] [--json out.json] [--md out.md]
                            [--crops <dir>] [--clips Walking,Death] [--rules root|chain] [--peer-ratio 1.15]

The threshold is in model units (MM9 models are in metres: 0.004 = 4 mm). Crops (--crops) render each flagged part at
its worst pose from two directions perpendicular to the gap: the part red, the rest grey, the gap yellow.
Exit status 1 when any component is visibly detached in some pose. Regression tests: test_detached_parts_audit.py.

Calibration (2026-10-30, 30 fps, root rules): see detached_parts_mm9.md. What it still cannot see: at bind, a part that
is not a plate and touches its holder at one corner (nothing says where its root should be), and a part another
neighbour still holds. detached_parts_mutation.py measures both on damaged copies of good models.
"""
import argparse
import json
import os
from pathlib import Path
import re
import sys

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import ConvexHull, QhullError, cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent / 'floor'))
import glb_pose  # noqa: E402

COLLAPSED_AREA = glb_pose.COLLAPSED_AREA
# root rules: parts whose areas differ by less than PEER_RATIO are peers. A sheet whose thinnest extent is at most
# PLATE_THINNESS of its middle one, whose longest is at most PLATE_ELONGATION times its middle one, and whose one-side
# area fills at least PLATE_FILL of its outline's box and PLATE_SOLIDITY of its outline's convex hull is a plate,
# judged by its base edge: the lowest BASE_BAND of its height, in BASE_SLICES slices. In a clip a root has parted when
# the median gap of its bind contact vertices to their holder passes ROOT_PARTED times the threshold.
PEER_RATIO = 1.15
PLATE_THINNESS = 0.25
PLATE_FILL = 0.25
PLATE_SOLIDITY = 0.65
PLATE_ELONGATION = 3.0
ROOT_PARTED = 2.0
BASE_BAND = 0.35
BASE_SLICES = 10


def closest_on_triangles(p, a, b, c):
    """Closest points of points p on triangles (a, b, c), all (n, 3); returns (points, barycentrics (n, 3))."""
    ab, ac, ap = b - a, c - a, p - a
    d1 = np.einsum('ij,ij->i', ab, ap)
    d2 = np.einsum('ij,ij->i', ac, ap)
    bp = p - b
    d3 = np.einsum('ij,ij->i', ab, bp)
    d4 = np.einsum('ij,ij->i', ac, bp)
    cp = p - c
    d5 = np.einsum('ij,ij->i', ab, cp)
    d6 = np.einsum('ij,ij->i', ac, cp)
    va = d3 * d6 - d5 * d4
    vb = d5 * d2 - d1 * d6
    vc = d1 * d4 - d3 * d2
    n = len(p)
    bary = np.zeros((n, 3))
    done = np.zeros(n, bool)

    def put(mask, w):
        nonlocal done
        m = mask & ~done
        bary[m] = w[m]
        done |= m

    one = np.ones(n)
    zero = np.zeros(n)
    put((d1 <= 0) & (d2 <= 0), np.stack([one, zero, zero], 1))
    put((d3 >= 0) & (d4 <= d3), np.stack([zero, one, zero], 1))
    put((d6 >= 0) & (d5 <= d6), np.stack([zero, zero, one], 1))
    with np.errstate(divide='ignore', invalid='ignore'):
        v = np.where(np.abs(d1 - d3) > 1e-30, d1 / (d1 - d3), 0.0)
        put((vc <= 0) & (d1 >= 0) & (d3 <= 0), np.stack([1 - v, v, zero], 1))
        w = np.where(np.abs(d2 - d6) > 1e-30, d2 / (d2 - d6), 0.0)
        put((vb <= 0) & (d2 >= 0) & (d6 <= 0), np.stack([1 - w, zero, w], 1))
        w = np.where(np.abs((d4 - d3) + (d5 - d6)) > 1e-30, (d4 - d3) / ((d4 - d3) + (d5 - d6)), 0.0)
        put((va <= 0) & ((d4 - d3) >= 0) & ((d5 - d6) >= 0), np.stack([zero, 1 - w, w], 1))
        den = va + vb + vc
        den = np.where(np.abs(den) > 1e-30, den, 1.0)
        v, w = vb / den, vc / den
    put(np.ones(n, bool), np.stack([1 - v - w, v, w], 1))
    q = bary[:, :1] * a + bary[:, 1:2] * b + bary[:, 2:] * c
    return q, bary


class Creature:
    def __init__(self, path):
        self.path = Path(path)
        self.glb = glb_pose.Glb(path)
        self.model = glb_pose.Model(self.glb)
        nodes = self.glb.json['nodes']
        meshes = self.glb.json['meshes']
        keep = []
        for prim in self.model.primitives:
            node = nodes[prim['node']]
            name = (node.get('name') or '') + ' ' + (meshes[node['mesh']].get('name') or '')
            if re.search(r'shadow', name, re.I):
                continue
            keep.append(prim)
        self.model.primitives = keep
        pos, tris, off = [], [], 0
        for prim in keep:
            pos.append(prim['positions'])
            tris.append(prim['triangles'] + off)
            off += len(prim['positions'])
        self.rest = np.concatenate(pos)
        self.tris = np.concatenate(tris)
        # weld by position (UV seams and hard edges split vertices)
        scale = float(np.ptp(self.rest, axis=0).max())
        key = np.round(self.rest / max(scale * 1e-6, 1e-9)).astype(np.int64)
        _, self.weld = np.unique(key, axis=0, return_inverse=True)
        self.weld = self.weld.reshape(-1)
        nw = int(self.weld.max()) + 1
        wt = self.weld[self.tris]
        rows = np.concatenate([wt[:, 0], wt[:, 1], wt[:, 2]])
        cols = np.concatenate([wt[:, 1], wt[:, 2], wt[:, 0]])
        graph = coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(nw, nw))
        ncomp, wlabel = connected_components(graph, directed=False)
        tri_comp = wlabel[wt[:, 0]]
        used = np.unique(tri_comp)
        remap = {c: k for k, c in enumerate(used)}
        self.tri_comp = np.array([remap[c] for c in tri_comp])
        self.ncomp = len(used)
        self.comp_tris = [np.nonzero(self.tri_comp == k)[0] for k in range(self.ncomp)]
        self.comp_verts = [np.unique(self.tris[t]) for t in self.comp_tris]
        # open boundaries (welded edges used by one triangle): a point past an open tube end is outside, whatever
        # the rim's normal says
        edges = np.sort(np.stack([wt[:, [0, 1]], wt[:, [1, 2]], wt[:, [2, 0]]], 1).reshape(-1, 2), axis=1)
        ekey = edges[:, 0] * nw + edges[:, 1]
        uniq, counts = np.unique(ekey, return_counts=True)
        self.tri_edge_open = np.isin(ekey, uniq[counts == 1]).reshape(-1, 3)  # edge (0-1, 1-2, 2-0) of a triangle
        self.weld_open = np.zeros(nw, bool)
        self.weld_open[edges[np.isin(ekey, uniq[counts == 1])].reshape(-1)] = True
        # welded edge of each triangle edge (pseudo-normals of edges) and each component's welded vertices and edges
        # (the root rules walk a part's surface)
        self.tri_edge = np.searchsorted(uniq, ekey).reshape(-1, 3)
        self.nedges = len(uniq)
        self.weld_rep = np.zeros(nw, np.int64)
        self.weld_rep[self.weld] = np.arange(len(self.weld))
        self.comp_wv, self.comp_edges = [], []
        for t in self.comp_tris:
            wv = np.unique(wt[t])
            local = np.searchsorted(wv, wt[t])
            ce = np.unique(np.sort(np.concatenate([local[:, [0, 1]], local[:, [1, 2]], local[:, [2, 0]]]), axis=1),
                           axis=0)
            self.comp_wv.append(wv)
            self.comp_edges.append((ce[:, 0], ce[:, 1]))
        self.size = scale
        a, b, c = (self.rest[self.tris[:, k]] for k in range(3))
        area = 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1)
        self.comp_area = np.array([area[t].sum() for t in self.comp_tris])
        self.body = int(np.argmax(self.comp_area))
        # dominant joint of each component (a readable label)
        skin = self.glb.json.get('skins', [{}])[0]
        joint_names = [nodes[j].get('name', str(j)) for j in skin.get('joints', [])]
        jw = np.zeros((len(self.rest), max(1, len(joint_names))))
        off = 0
        for prim in keep:
            n = len(prim['positions'])
            if prim['skinned']:
                for k in range(prim['joints'].shape[1]):
                    np.add.at(jw, (np.arange(off, off + n), prim['joints'][:, k]), prim['weights'][:, k])
            off += n
        self.comp_joint = []
        for vs in self.comp_verts:
            s = jw[vs].sum(0)
            self.comp_joint.append(joint_names[int(np.argmax(s))] if joint_names and s.max() > 0 else '-')
        self.clip_names = list(self.model.clips)

    def pose(self, clip=None, time=0.0):
        world = self.model.world({} if clip is None else self.model.sample(clip, time))
        posed = self.model.skinned_positions(world)
        return np.concatenate([p for p, _ in posed])

    def clip_duration(self, clip):
        t = self.model.clip_times(clip)
        return t[-1] if t else 0.0

    def describe(self, k):
        c = self.rest[self.comp_verts[k]].mean(0)
        b = self.rest[self.comp_verts[self.body]].mean(0)
        d = c - b
        parts = []
        if abs(d[1]) > 0.1 * self.size:
            parts.append('above' if d[1] > 0 else 'below')
        if abs(d[0]) > 0.1 * self.size:
            parts.append('+x side' if d[0] > 0 else '-x side')
        if abs(d[2]) > 0.1 * self.size:
            parts.append('+z' if d[2] > 0 else '-z')
        return ', '.join(parts) or 'central'


def measure_pose(cr, P, threshold):
    """Signed distances between nearby components of one pose. Returns (gaps {k: (gap, point_on_part,
    point_on_attached)} for unattached components, attached mask, rooted depth {k: depth into its parent})."""
    tris = cr.tris
    a, b, c = P[tris[:, 0]], P[tris[:, 1]], P[tris[:, 2]]
    fn = np.cross(b - a, c - a)
    area2 = np.linalg.norm(fn, axis=1)
    nw = int(cr.weld.max()) + 1
    vn = np.zeros((nw, 3))
    for k in range(3):
        np.add.at(vn, cr.weld[tris[:, k]], fn)
    vn /= np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-20)
    tn = vn[cr.weld[tris]]  # (T, 3 corners, 3)
    visible = np.array([area2[t].sum() > COLLAPSED_AREA * len(t) for t in cr.comp_tris])
    margin = max(4 * threshold, 0.02 * cr.size)
    lo = np.array([P[v].min(0) for v in cr.comp_verts])
    hi = np.array([P[v].max(0) for v in cr.comp_verts])
    trees = {}

    def tree(j):
        if j not in trees:
            cen = (a[cr.comp_tris[j]] + b[cr.comp_tris[j]] + c[cr.comp_tris[j]]) / 3
            trees[j] = cKDTree(cen)
        return trees[j]

    def signed(i, j):
        """min signed distance of i's vertices (near j) to j's surface, with the two closest points"""
        vs = cr.comp_verts[i]
        p = P[vs]
        near = np.all((p >= lo[j] - margin) & (p <= hi[j] + margin), axis=1)
        if not near.any():
            return np.inf, None, None
        p = p[near]
        tj = cr.comp_tris[j]
        k = min(12, len(tj))
        _, idx = tree(j).query(p, k=k)
        idx = idx.reshape(len(p), k)
        cand = tj[idx]  # (m, k)
        pp = np.repeat(p, k, axis=0)
        ct = cand.reshape(-1)
        q, bary = closest_on_triangles(pp, a[ct], b[ct], c[ct])
        d = np.linalg.norm(pp - q, axis=1).reshape(len(p), k)
        best = np.argmin(d, axis=1)
        rows = np.arange(len(p))
        dist = d[rows, best]
        flat = rows * k + best
        bf, tf = bary[flat], ct[flat]
        # sign: the face normal for a point inside a face, the smoothed normal on an edge or corner; outside when the
        # nearest edge or corner is an open boundary
        n = np.einsum('ij,ijk->ik', bf, tn[tf])
        interior = np.all(bf > 1e-6, axis=1)
        n[interior] = fn[tf[interior]]
        side = np.einsum('ij,ij->i', pp[flat] - q[flat], n)
        zero = bf <= 1e-6
        on_edge = np.zeros(len(bf), bool)
        for e, (u, v) in enumerate(((0, 1), (1, 2), (2, 0))):
            w = 3 - u - v  # the corner opposite the edge has barycentric 0 on that edge
            on_edge |= zero[:, w] & ~zero[:, u] & ~zero[:, v] & cr.tri_edge_open[tf, e]
        corner = zero.sum(1) == 2
        cw = cr.weld[tris[tf, np.argmax(bf, axis=1)]]
        open_side = on_edge | (corner & cr.weld_open[cw])
        sd = np.where((side < 0) & ~open_side, -dist, dist)
        m = int(np.argmin(sd))
        return float(sd[m]), p[m], q[flat[m]]

    nc = cr.ncomp
    G = np.full((nc, nc), np.inf)
    pts = {}
    for i in range(nc):
        if not visible[i]:
            continue
        for j in range(nc):
            if j == i or not visible[j]:
                continue
            if np.any(lo[i] > hi[j] + margin) or np.any(lo[j] > hi[i] + margin):
                continue
            d, p, q = signed(i, j)
            if d < G[i, j]:
                G[i, j] = d
                pts[(i, j)] = (p, q)
    S = np.minimum(G, G.T)
    attached = np.zeros(nc, bool)
    attached[cr.body] = True
    stack = [cr.body]
    while stack:
        i = stack.pop()
        for j in np.nonzero(S[i] <= threshold)[0]:
            if not attached[j] and visible[j]:
                attached[j] = True
                stack.append(j)
    gaps = {}
    rooted = {}
    att_ids = np.nonzero(attached)[0]

    def nearest(i, ids):
        """(gap, point on i, point on the other part, other part) to the nearest of the parts ids"""
        cand = [(S[i, j], j) for j in ids if np.isfinite(S[i, j])]
        if cand:
            g, j = min(cand)
            p, q = pts.get((i, j), (None, None))
            if p is None:
                q, p = pts[(j, i)]
            return float(g), p, q, int(j)
        # far from all of them: vertex to vertex distance
        av = np.concatenate([cr.comp_verts[j] for j in ids])
        t = cKDTree(P[av])
        d, idx = t.query(P[cr.comp_verts[i]])
        m = int(np.argmin(d))
        return float(d[m]), P[cr.comp_verts[i][m]], P[av[idx[m]]], -1
    for i in range(nc):
        if not visible[i] or i == cr.body:
            continue
        if attached[i]:
            j = min((j for j in att_ids if j != i), key=lambda j: S[i, j], default=None)
            if j is not None and np.isfinite(S[i, j]):
                rooted[i] = (-float(S[i, j]), int(j))
            continue
    # unattached parts in clusters of touching parts. The clusters join the body's in a minimum spanning tree grown
    # from it (Prim): each cluster's break is the tree edge that links it, reported on the member at that edge; the
    # other members are carried by it.
    loose = [i for i in range(nc) if visible[i] and not attached[i]]
    cluster = {}
    for i in loose:
        if i in cluster:
            continue
        cluster[i] = i
        stack = [i]
        while stack:
            a = stack.pop()
            for b in np.nonzero(S[a] <= threshold)[0]:
                if visible[b] and not attached[b] and b not in cluster:
                    cluster[b] = i
                    stack.append(b)
    members = {}
    for i, c in cluster.items():
        members.setdefault(c, []).append(i)
    tree = list(att_ids)
    remaining = set(members)
    while remaining:
        best = None
        for c in remaining:
            for i in members[c]:
                for j in tree:
                    if np.isfinite(S[i, j]) and (best is None or S[i, j] < best[0]):
                        best = (float(S[i, j]), c, i, j)
        if best is None:  # nothing near the tree: vertex to vertex distance
            tv = np.concatenate([cr.comp_verts[j] for j in tree])
            kt = cKDTree(P[tv])
            for c in remaining:
                for i in members[c]:
                    d, idx = kt.query(P[cr.comp_verts[i]])
                    m = int(np.argmin(d))
                    if best is None or d[m] < best[0]:
                        best = (float(d[m]), c, i, (P[cr.comp_verts[i][m]], P[tv[idx[m]]]))
        g, c, i, j = best
        if isinstance(j, tuple):
            lp, lq = j
        else:
            lp, lq = pts.get((i, j), (None, None))
            if lp is None:
                lq, lp = pts[(j, i)]
        for k in members[c]:
            ga, pa, qa, ja = nearest(k, att_ids)
            gaps[k] = (ga, pa, qa, ja, g, lp, lq) if k == i else (ga, pa, qa, ja, 0.0, None, None)
        tree.extend(members[c])
        remaining.discard(c)
    return gaps, attached, rooted, visible


class PoseGeometry:
    """One pose's surfaces: unit face normals and angle-weighted pseudo-normals of welded vertices and edges, so the
    sign of a point's distance is right next to an edge or a corner too (a point far behind a thin plate's corner is
    outside it)."""

    def __init__(self, cr, P):
        self.cr, self.P = cr, P
        tris = cr.tris
        self.a, self.b, self.c = P[tris[:, 0]], P[tris[:, 1]], P[tris[:, 2]]
        fn = np.cross(self.b - self.a, self.c - self.a)
        self.area2 = np.linalg.norm(fn, axis=1)
        self.fu = fn / np.maximum(self.area2[:, None], 1e-30)
        corners = (self.a, self.b, self.c)
        nw = int(cr.weld.max()) + 1
        vn = np.zeros((nw, 3))
        for k in range(3):
            e1 = corners[(k + 1) % 3] - corners[k]
            e2 = corners[(k + 2) % 3] - corners[k]
            cosang = np.einsum('ij,ij->i', e1, e2) / np.maximum(
                np.linalg.norm(e1, axis=1) * np.linalg.norm(e2, axis=1), 1e-30)
            np.add.at(vn, cr.weld[tris[:, k]], self.fu * np.arccos(np.clip(cosang, -1, 1))[:, None])
        self.vn = vn / np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-30)
        en = np.zeros((cr.nedges, 3))
        for e in range(3):
            np.add.at(en, cr.tri_edge[:, e], self.fu)
        self.en = en / np.maximum(np.linalg.norm(en, axis=1, keepdims=True), 1e-30)
        self.trees = {}

    def tree(self, j):
        if j not in self.trees:
            t = self.cr.comp_tris[j]
            self.trees[j] = cKDTree((self.a[t] + self.b[t] + self.c[t]) / 3)
        return self.trees[j]

    def signed(self, p, j, normals=False):
        """Signed distances of points p (n, 3) to component j's surface (negative inside) and the nearest points (and
        j's outward normals there)."""
        cr = self.cr
        tj = cr.comp_tris[j]
        k = min(16, len(tj))
        _, idx = self.tree(j).query(p, k=k)
        idx = np.asarray(idx).reshape(len(p), k)
        ct = tj[idx].reshape(-1)
        pp = np.repeat(p, k, axis=0)
        q, bary = closest_on_triangles(pp, self.a[ct], self.b[ct], self.c[ct])
        d = np.linalg.norm(pp - q, axis=1).reshape(len(p), k)
        best = np.argmin(d, axis=1)
        rows = np.arange(len(p))
        flat = rows * k + best
        bf, tf, qf = bary[flat], ct[flat], q[flat]
        dist = d[rows, best]
        zero = bf <= 1e-6
        nz = zero.sum(1)
        n = self.fu[tf].copy()
        # nearest on an edge: the edge's pseudo-normal (edge 0-1 has corner 2 at zero, 1-2 corner 0, 2-0 corner 1)
        on_edge = nz == 1
        zc = np.argmax(zero, axis=1)
        e = np.array([1, 2, 0])[zc]
        n[on_edge] = self.en[cr.tri_edge[tf[on_edge], e[on_edge]]]
        corner = nz >= 2
        cw = cr.weld[cr.tris[tf, np.argmax(bf, axis=1)]]
        n[corner] = self.vn[cw[corner]]
        side = np.einsum('ij,ij->i', p - qf, n)
        # outside when the nearest edge or corner is an open boundary (past an open tube end)
        open_side = (on_edge & cr.tri_edge_open[tf, e]) | (corner & cr.weld_open[cw])
        sd = np.where((side < 0) & ~open_side, -dist, dist)
        return (sd, qf, n) if normals else (sd, qf)


def plate_axes(X, area):
    """Principal axes (columns, thinnest first) of a part that is a plate: a sheet, thin (thinnest extent at most
    PLATE_THINNESS of the middle one), at most PLATE_ELONGATION times as long as wide, and with one side's area at least
    PLATE_FILL of its outline's box and PLATE_SOLIDITY of its outline's convex hull (so a flat limb or a limb bent
    into an L in a plane is not one). None for other parts."""
    if len(X) < 4:
        return None
    c = X - X.mean(0)
    _, vec = np.linalg.eigh(c.T @ c)
    ext = np.ptp(c @ vec, axis=0)
    if (ext[2] <= 0 or ext[0] > PLATE_THINNESS * ext[1] or ext[2] > PLATE_ELONGATION * ext[1]
            or 0.5 * area < PLATE_FILL * ext[1] * ext[2]):
        return None
    try:
        hull = ConvexHull(c @ vec[:, 1:]).volume  # the outline's convex area in the plate's plane
    except QhullError:
        return None
    if 0.5 * area < PLATE_SOLIDITY * hull:  # an arm bent into an L, not a sheet
        return None
    return vec


def plate_base_gap(X, edges, sd, Q, normal, vec):
    """A plate (plate_axes) standing on its holder (a fin, a sail, a flat spike: its plane holds the holder's normal
    at the contact) is judged by its base edge, as mm9_seamon_claude/scripts/fin_gates.py does: the plate's lowest
    BASE_BAND of its height, cut into BASE_SLICES slices along the base; in each slice the point closest to the
    holder (on the vertices and along the edges, distances interpolated), and the largest of those. A plate that
    touches at one corner while the rest of its base lifts off fails. A slice counts only where the holder lies under
    it (its nearest point within about 25 degrees of straight down), and the plate stands on the holder only when at
    least half its slices do: a wing spreading out past a narrow root has no holder under its outer base. Q: the
    nearest holder points of X; vec: the plate's axes. Returns (gap, point, holder point), or None when the plate
    leans or lies on the holder, or does not stand on it along its base."""
    plate_n = vec[:, 0]
    if abs(float(plate_n @ normal)) > 0.35:  # leaning or lying on the holder (more than 20 degrees off upright)
        return None
    up = normal - plate_n * float(plate_n @ normal)
    up /= max(np.linalg.norm(up), 1e-12)
    along = np.cross(plate_n, up)
    h = X @ up
    t = X @ along
    step = max(np.ptp(t), 1e-12) / (4 * BASE_SLICES)
    # points along the edges, so a long base edge between two far vertices fills every slice it crosses
    eu, ev = edges
    k = np.maximum(1, np.ceil(np.abs(t[ev] - t[eu]) / step).astype(int))
    rep = np.repeat(np.arange(len(eu)), k + 1)
    f = (np.arange(len(rep)) - np.repeat(np.cumsum(k + 1) - (k + 1), k + 1)) / np.repeat(k, k + 1)
    pu, pv = eu[rep], ev[rep]
    pts = X[pu] + f[:, None] * (X[pv] - X[pu])
    psd = sd[pu] + f * (sd[pv] - sd[pu])
    pq = Q[pu] + f[:, None] * (Q[pv] - Q[pu])
    ph, pt = h[pu] + f * (h[pv] - h[pu]), t[pu] + f * (t[pv] - t[pu])
    base = ph <= h.min() + BASE_BAND * np.ptp(h)
    pts, psd, pt, pq = pts[base], psd[base], pt[base], pq[base]
    sl = np.minimum(((pt - t.min()) / max(np.ptp(t), 1e-12) * BASE_SLICES).astype(int), BASE_SLICES - 1)
    worst, slices, under = None, 0, 0
    for s_ in np.unique(sl):
        slices += 1
        idx = np.nonzero(sl == s_)[0]
        m = idx[int(np.argmin(psd[idx]))]
        down = pq[m] - pts[m]
        if psd[m] > 0 and float(down @ up) > -0.9 * np.linalg.norm(down):
            continue  # nothing of the holder under this slice
        under += 1
        if worst is None or psd[m] > psd[worst]:
            worst = m
    if worst is None or 2 * under < slices:
        return None  # not standing on the holder along its base
    return float(psd[worst]), pts[worst], pq[worst]


def root_link(cr, geo, i, j, threshold, reach, size_i, area_i):
    """How part i sits on part j: ('rooted', -depth, p, q, depth) when it touches j (a vertex within threshold of j
    or inside it, or j's surface through one of i's faces) and, for a standing plate, its whole base does
    (plate_base_gap); ('lifted', gap, p, q, depth) for a standing plate touching j with its base off it (gap: the
    largest base slice gap); ('floating', gap, p, q, None) when it does not touch j (gap: its closest approach). p is
    the point on i, q the nearest point on j."""
    P = geo.P
    X = P[cr.weld_rep[cr.comp_wv[i]]]
    jv = P[cr.comp_verts[j]]
    lo, hi = jv.min(0) - reach, jv.max(0) + reach
    near = np.all((X >= lo) & (X <= hi), axis=1)
    sd = np.full(len(X), np.inf)
    Q = np.zeros_like(X)
    N = np.zeros_like(X)
    if near.any():
        sd[near], Q[near], N[near] = geo.signed(X[near], j, normals=True)
    contact = sd <= threshold
    # j's surface piercing i between i's vertices (a sleeve's rim through a large hand face): j's vertices near or in
    # i are contacts too (no deeper than a quarter of i's size: past that a thin part's inside means nothing)
    ilo, ihi = X.min(0) - threshold, X.max(0) + threshold
    jn = jv[np.all((jv >= ilo) & (jv <= ihi), axis=1)]
    pierced = None
    touch = [X[contact]]
    if len(jn):
        sdj, qj = geo.signed(jn, i)
        hit = np.nonzero((sdj <= threshold) & (sdj >= -0.25 * size_i))[0]
        if len(hit):
            m = hit[int(np.argmin(sdj[hit]))]
            pierced = (float(-sdj[m]), qj[m], jn[m])
            touch.append(qj[hit])
    if not contact.any() and pierced is None:
        if not np.isfinite(sd).any():
            dd, idx = cKDTree(jv).query(X)
            m = int(np.argmin(dd))
            return 'floating', float(dd[m]), X[m], jv[idx[m]], None
        m = int(np.argmin(sd))
        return 'floating', float(sd[m]), X[m], Q[m], None
    if contact.any():
        m = int(np.argmin(sd))
        deep = (float(-sd[m]), X[m], Q[m])
        normal = N[contact].sum(0)
        nl = np.linalg.norm(normal)
        axes = plate_axes(X, area_i) if nl > 1e-12 else None
        if axes is not None:
            far = ~np.isfinite(sd)
            if far.any():
                sd[far], Q[far] = geo.signed(X[far], j)
            base = plate_base_gap(X, cr.comp_edges[i], sd, Q, normal / nl, axes)
            if base is not None and base[0] > threshold:
                q = geo.signed(base[1][None], j)[1][0]
                return 'lifted', base[0], base[1], q, deep[0], np.concatenate(touch).mean(0)
    else:
        deep = pierced
    return 'rooted', -deep[0], deep[1], deep[2], deep[0], np.concatenate(touch).mean(0), np.nonzero(contact)[0]


def measure_pose_root(cr, P, threshold, peer_ratio=PEER_RATIO, roots=None):
    """Root rules (the default). A part is attached when its own root sits in or on an attached part that may hold it
    (root_link). Who may hold a part:
    - the body and parts larger than it (area at least peer_ratio times its own);
    - a much smaller connector (MM9 hangs heads on neck pieces and feet on thin shins);
    - a neighbour of similar area (a peer); a plate (plate_axes: a fin, a scale) only when no larger part lies
      alongside it within its own size, so a row of fins resting on each other above a tail has to reach the tail
      (an eyeball on its stalk or a bone along an articulated leg keeps its peer).
    A standing plate whose base lifts off the body or a larger part it touches is loose even when it is held. Loose
    parts that hold each other form a cluster whose break is reported once, on the member nearest an attached part;
    the others are carried. roots: each part's root at bind ({part: (holder, contact vertices)}, left in cr.last_roots
    by the bind pose's call). In a clip a part whose root has parted from that holder (the median gap of those
    vertices over ROOT_PARTED times the threshold) no longer sits on it, so one corner still touching does not hide
    it. The 90th percentile is left in cr.last_lifts: a rigid limb pivoting in its socket raises one side of its root
    while the other sinks, so that alone is advice, not a failure. Returns what measure_pose does, plus each break's
    kind ('floating', 'lifted' or 'parted')."""
    geo = PoseGeometry(cr, P)
    nc = cr.ncomp
    visible = np.array([geo.area2[t].sum() > COLLAPSED_AREA * len(t) for t in cr.comp_tris])
    margin = max(4 * threshold, 0.02 * cr.size)
    lo = np.array([P[v].min(0) for v in cr.comp_verts])
    hi = np.array([P[v].max(0) for v in cr.comp_verts])
    ext = np.linalg.norm(hi - lo, axis=1)
    area = cr.comp_area
    order = [int(k) for k in np.argsort(-area, kind='stable') if k != cr.body and visible[k]]

    def box_gap(i, j):
        return float(np.linalg.norm(np.maximum(0.0, np.maximum(lo[i] - hi[j], lo[j] - hi[i]))))

    def larger(i, j):
        return j == cr.body or area[j] >= peer_ratio * area[i]

    links = {}

    def link(i, j):
        if (i, j) not in links:
            links[(i, j)] = root_link(cr, geo, i, j, threshold, max(margin, 0.5 * ext[i]), ext[i], area[i])
        return links[(i, j)]

    def alongside(i, j, big):
        """Whether a larger part lies alongside part i rather than behind its contact with j: i grows from that
        contact towards its centre; a larger part off that line (a tail under a row of fins) is alongside, one behind
        the contact (the body behind an eyeball's stalk) is not."""
        grow = P[cr.comp_verts[i]].mean(0) - link(i, j)[5]
        grow /= max(np.linalg.norm(grow), 1e-12)
        for b in big:
            kind, g, p, q = link(i, b)[:4]
            if kind != 'floating':
                return True  # touching it: judged against it
            if g > ext[i]:
                continue
            d = q - p
            if abs(float(d @ grow)) < 0.5 * max(np.linalg.norm(d), 1e-12):
                return True
        return False

    holders = {}
    for i in order:
        reach = max(margin, 0.5 * ext[i])
        near = [j for j in range(nc) if j != i and visible[j] and box_gap(i, j) <= reach]
        big = [j for j in near if larger(i, j)]
        small = [j for j in near if not larger(i, j) and area[j] * peer_ratio <= area[i]]
        plate = plate_axes(P[cr.comp_verts[i]], area[i]) is not None
        peers = [j for j in near if not larger(i, j) and area[j] * peer_ratio > area[i]
                 and (not plate or link(i, j)[0] == 'floating' or not alongside(i, j, big))]
        holders[i] = big + small + peers
    cr.last_lifts = {}
    for i, (h, idx) in (roots or {}).items():
        if visible[i] and visible[h] and h in holders.get(i, []):
            X = P[cr.weld_rep[cr.comp_wv[i]]][idx]
            sd, Q = geo.signed(X, h)
            g = float(np.median(sd))
            worst = int(np.argmax(sd))
            cr.last_lifts[i] = (float(np.percentile(sd, 90)), h)
            if g > ROOT_PARTED * threshold:
                links[(i, h)] = ('parted', g, X[worst], Q[worst], None, X.mean(0))
    # a standing plate whose base hovers over the body or a larger part it touches is loose, whatever else holds it
    # (a fin overlapping the end of a sail while its base floats over the tail)
    lifted = {i for i in order if any(link(i, j)[0] == 'lifted' for j in holders[i] if larger(i, j))}
    attached = np.zeros(nc, bool)
    attached[cr.body] = True
    parent = {}
    changed = True
    while changed:
        changed = False
        for i in order:
            if attached[i] or i in lifted:
                continue
            for j in holders[i]:
                if attached[j] and link(i, j)[0] == 'rooted':
                    attached[i], parent[i], changed = True, j, True
                    break
    rooted = {i: (link(i, j)[4], j) for i, j in parent.items()}
    # a part touching with most of its surface (a dome inside a bell) has no root to part
    cr.last_roots = {i: (j, link(i, j)[6]) for i, j in parent.items()
                     if 2 <= len(link(i, j)[6]) <= 0.5 * len(cr.comp_wv[i])}
    loose = [i for i in order if not attached[i]]
    # clusters of loose parts holding each other
    cluster = {i: i for i in loose}

    def find(x):
        while cluster[x] != x:
            cluster[x] = cluster[cluster[x]]
            x = cluster[x]
        return x
    for i in loose:
        for j in holders[i]:
            if j in cluster and link(i, j)[0] == 'rooted' and i not in lifted and j not in lifted:
                cluster[find(i)] = find(j)
    best = {}
    for i in loose:
        b = None
        for j in holders[i]:
            if i in lifted and (link(i, j)[0] != 'lifted' or not larger(i, j)):
                continue
            if attached[j] or i in lifted:
                kind, g, p, q = link(i, j)[:4]
                if b is None or (g > b[1] if i in lifted else g < b[1]):
                    b = (kind, g, p, q, j)
        if b is None:  # no attached part near: the surface distance to the nearest few attached parts
            for j in sorted(np.nonzero(attached)[0], key=lambda j: box_gap(i, j))[:4]:
                kind, g, p, q = root_link(cr, geo, i, int(j), threshold, np.inf, ext[i], area[i])[:4]
                g = max(g, 0.0)  # a part it touches but may not rest on
                if b is None or g < b[1]:
                    b = ('floating', g, p, q, int(j))
        best[i] = b
    breaks = {}
    for i in loose:
        c = find(i)
        if c not in breaks or best[i][1] < best[breaks[c]][1]:
            breaks[c] = i
    gaps, kinds = {}, {}
    for i in loose:
        if breaks[find(i)] != i:
            gaps[i] = (0.0, None, None, -1, 0.0, None, None)  # carried by the cluster's break
            continue
        kind, g, p, q, j = best[i]
        gaps[i] = (g, p, q, j, g, p, q)
        kinds[i] = kind
    return gaps, attached, rooted, visible, kinds


def _sphere_directions(n=96):
    k = np.arange(n) + 0.5
    phi = np.arccos(1 - 2 * k / n)
    theta = np.pi * (1 + 5 ** 0.5) * k
    return np.stack([np.cos(theta) * np.sin(phi), np.cos(phi), np.sin(theta) * np.sin(phi)], 1)


DIRECTIONS = _sphere_directions()


def concealed(cr, P, p, q, leak=0.04, skip=None):
    """Whether a gap (p on the part, q on the attached surface) is hidden from every camera: rays from three points
    along it in DIRECTIONS all hit the model (any part, the detached one included unless it is `skip`) or, pointing
    down, the floor (y = 0) within a quarter of the model's size (a foot under a dress). At most `leak` of the rays
    may escape."""
    tris = cr.tris if skip is None else cr.tris[cr.tri_comp != skip]
    A, B, C = P[tris[:, 0]], P[tris[:, 1]], P[tris[:, 2]]
    e1, e2 = B - A, C - A
    for f in (0.25, 0.5, 0.75):
        o = p + (q - p) * f
        D = DIRECTIONS
        h = np.cross(D[:, None, :], e2[None, :, :])  # (R, T, 3)
        a = np.einsum('tk,rtk->rt', e1, h)
        ok = np.abs(a) > 1e-12
        inv = np.where(ok, 1.0 / np.where(ok, a, 1.0), 0.0)
        sv = o[None, :] - A  # (T, 3)
        u = inv * np.einsum('tk,rtk->rt', sv, h)
        qv = np.cross(sv, e1)  # (T, 3)
        v = inv * np.einsum('rk,tk->rt', D, qv)
        t = inv * np.einsum('tk,tk->t', e2, qv)[None, :]
        hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-5)
        blocked = hit.any(1)
        down = D[:, 1] < -1e-6
        tf = np.where(down, -o[1] / np.where(down, D[:, 1], -1.0), np.inf)
        blocked |= down & (tf >= 0) & (tf < 0.25 * cr.size)
        if (~blocked).mean() > leak:
            return False
    return True


def audit(path, fps=30.0, threshold=0.004, clips=None, log=print, rules='root', peer_ratio=PEER_RATIO):
    cr = Creature(path)
    result = {'glb': str(path), 'components': cr.ncomp, 'body': cr.body, 'size': cr.size,
              'threshold': threshold, 'fps': fps, 'rules': rules, 'parts': {}}
    if rules == 'root':
        result.update(peer_ratio=peer_ratio)
    poses = [('bind', None, 0.0, 0)]
    for clip in cr.clip_names:
        if clips and clip not in clips:
            continue
        dur = cr.clip_duration(clip)
        n = max(1, int(np.floor(dur * fps + 1e-6)) + 1)
        for f in range(n):
            poses.append((clip, clip, min(f / fps, dur), f))
    roots = None
    parts = {}
    for k in range(cr.ncomp):
        if k == cr.body:
            continue
        ext = float(np.linalg.norm(np.ptp(cr.rest[cr.comp_verts[k]], axis=0)))
        parts[k] = {'joint': cr.comp_joint[k], 'where': cr.describe(k), 'triangles': int(len(cr.comp_tris[k])),
                    'extent': round(ext, 4),
                    'bind_gap': None, 'bind_rooted_depth': None, 'worst': None, 'detached_poses': 0, 'poses': 0,
                    'clips': {}, 'shallowest': None, 'concealed_poses': 0, 'worst_concealed': None,
                    'carried_poses': 0, 'root_lift': None}
    for label, clip, t, f in poses:
        P = cr.pose(clip, t)
        if rules == 'root':
            gaps, attached, rooted, visible, kinds = measure_pose_root(cr, P, threshold, peer_ratio, roots)
            if label == 'bind':
                roots = cr.last_roots
            for k, (g, h) in getattr(cr, 'last_lifts', {}).items():
                if k in parts and g > ROOT_PARTED * threshold and (parts[k]['root_lift'] is None
                                                                   or g > parts[k]['root_lift']['gap']):
                    parts[k]['root_lift'] = {'gap': round(g, 5), 'on': cr.comp_joint[h], 'clip': label, 'frame': f,
                                             'time': round(t, 4)}
        else:
            gaps, attached, rooted, visible = measure_pose(cr, P, threshold)
            kinds = {}
        for k, part in parts.items():
            if not visible[k]:
                continue
            part['poses'] += 1
            if label == 'bind':
                part['bind_gap'] = 0.0
                if k in rooted:
                    part['bind_rooted_depth'] = round(rooted[k][0], 5)
            if k in rooted and (part['shallowest'] is None or rooted[k][0] < part['shallowest']['depth']):
                part['shallowest'] = {'depth': round(rooted[k][0], 5), 'on': cr.comp_joint[rooted[k][1]],
                                      'clip': label, 'frame': f, 'time': round(t, 4)}
            if k in gaps:
                g, p, q, j, lg, lp, lq = gaps[k]
                if label == 'bind':
                    part['bind_gap'] = round(lg, 5) if lp is not None else 0.0
                if lp is None:
                    # touching its neighbours: carried off by a break elsewhere (that part is reported)
                    part['carried_poses'] += 1
                    continue
                # a lifted or parted part's own faces do not hide the gap at its root
                if concealed(cr, P, lp, lq, skip=k if kinds.get(k) in ('lifted', 'parted') else None):
                    part['concealed_poses'] += 1
                    if part['worst_concealed'] is None or lg > part['worst_concealed']['gap']:
                        part['worst_concealed'] = {'gap': round(lg, 5), 'clip': label, 'frame': f,
                                                   'time': round(t, 4)}
                    continue
                part['detached_poses'] += 1
                cl = part['clips'].setdefault(label, {'max_gap': 0.0, 'frame': None, 'time': None, 'frames': 0})
                cl['frames'] += 1
                if lg > cl['max_gap']:
                    cl.update(max_gap=round(lg, 5), frame=f, time=round(t, 4))
                if part['worst'] is None or lg > part['worst']['gap']:
                    part['worst'] = {'gap': round(lg, 5), 'to_body_cluster': round(g, 5), 'clip': label, 'frame': f,
                                     'time': round(t, 4), 'part_point': [round(float(x), 5) for x in lp],
                                     'attached_point': [round(float(x), 5) for x in lq],
                                     'kind': kinds.get(k, 'floating'),
                                     'against': cr.comp_joint[j] if j >= 0 else '-'}
    for k, part in parts.items():
        if part['worst'] is not None:
            result['parts'][k] = part
    result['component_summary'] = {
        'total': cr.ncomp, 'attached_in_every_pose': cr.ncomp - 1 - len(result['parts'])}
    # detached only where nothing can see the gap (inside a dress, a shell or a socket)
    result['concealed'] = {k: p for k, p in parts.items() if p['worst'] is None and p['worst_concealed'] is not None}
    # attached in every pose, but at some pose only just (rooted less than twice the threshold, or touching across a
    # gap within it): worth a look when the part should grow out of the body
    # (small studs, teeth and bumps that sit on the surface are left out: under 5 % of the model's size)
    result['shallow'] = {k: p for k, p in parts.items()
                         if p['worst'] is None and p['shallowest'] is not None
                         and p['shallowest']['depth'] < 2 * threshold and p['extent'] > 0.05 * cr.size}
    # attached in every pose, but one side of the root lifts in some pose (a limb pivoting in its socket, or the start
    # of a gap): worth a look, not a failure
    result['root_lift'] = {k: p for k, p in parts.items() if p['worst'] is None and p['root_lift'] is not None}
    result['_creature'] = cr
    return result


# ------------------------------------------------------------------ crops (software render, no Blender)
def render_crop(cr, P, part, p_part, p_att, out, size=420, extent=None):
    from PIL import Image, ImageDraw
    gap = p_att - p_part
    gl = float(np.linalg.norm(gap))
    centre = (p_part + p_att) / 2
    # framed on the part (its size when given: a 30 cm fin on a 7 m creature) and the gap
    half = max(3.0 * gl, 0.12 * cr.size) if extent is None else max(3.0 * gl, 0.6 * extent, 0.02 * cr.size)
    g = gap / gl if gl > 1e-9 else np.array([0.0, 1.0, 0.0])
    up = np.array([0.0, 1.0, 0.0])
    v1 = np.cross(g, up)
    if np.linalg.norm(v1) < 1e-3:
        v1 = np.cross(g, np.array([1.0, 0.0, 0.0]))
    v1 /= np.linalg.norm(v1)
    v2 = np.cross(g, v1)
    v2 /= np.linalg.norm(v2)
    images = []
    light = np.array([0.3, 0.8, 0.5])
    light /= np.linalg.norm(light)
    for view in (v1, v2):
        # camera looks along -view; screen x axis = g projected, y = up-ish
        sx = g - view * g.dot(view)
        if np.linalg.norm(sx) < 1e-6:
            sx = np.cross(view, up)
        sx /= np.linalg.norm(sx)
        sy = np.cross(view, sx)
        if sy[1] < 0:
            sy, sx = -sy, -sx
        img = Image.new('RGB', (size, size), (52, 54, 60))
        dr = ImageDraw.Draw(img)
        tris = cr.tris
        A, B, C = P[tris[:, 0]], P[tris[:, 1]], P[tris[:, 2]]
        cen = (A + B + C) / 3 - centre
        # a slab around the gap: geometry far in front of it (other limbs) would hide it
        inside = (np.abs(cen @ sx) < half * 1.3) & (np.abs(cen @ sy) < half * 1.3) & (np.abs(cen @ view) < half)
        fn = np.cross(B - A, C - A)
        fl = np.linalg.norm(fn, axis=1)
        ok = inside & (fl > 1e-14)
        idx = np.nonzero(ok)[0]
        depth = cen[idx] @ view
        order = idx[np.argsort(depth)]  # far (most negative along view = behind) first
        scale = size / (2 * half)

        def scr(pt):
            d = pt - centre
            return (size / 2 + d @ sx * scale, size / 2 - d @ sy * scale)
        part_set = set(cr.comp_tris[part].tolist())
        for t in order:
            n = fn[t] / fl[t]
            facing = n @ view
            shade = 0.35 + 0.65 * abs(float(n @ light))
            if t in part_set:
                col = (int(230 * shade), int(60 * shade), int(50 * shade))
            else:
                col = (int(180 * shade), int(176 * shade), int(168 * shade))
            if facing < 0:
                col = tuple(int(x * 0.55) for x in col)
            dr.polygon([scr(A[t]), scr(B[t]), scr(C[t])], fill=col)
        a2, b2 = scr(p_part), scr(p_att)
        dr.line([a2, b2], fill=(255, 230, 0), width=3)
        for pt in (a2, b2):
            dr.ellipse([pt[0] - 4, pt[1] - 4, pt[0] + 4, pt[1] + 4], outline=(255, 230, 0), width=2)
        images.append(img)
    sheet = Image.new('RGB', (size * 2 + 6, size), (20, 20, 20))
    sheet.paste(images[0], (0, 0))
    sheet.paste(images[1], (size + 6, 0))
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('glbs', nargs='+')
    ap.add_argument('--fps', type=float, default=30.0)
    ap.add_argument('--threshold', type=float, default=0.004, help='model units (MM9: metres)')
    ap.add_argument('--clips', default=None, help='comma separated clip names (default: all)')
    ap.add_argument('--json', default=None)
    ap.add_argument('--md', default=None)
    ap.add_argument('--crops', default=None, help='directory for render crops of flagged parts')
    ap.add_argument('--rules', choices=('root', 'chain'), default='root',
                    help='root (default): each part rooted in the body or a larger part, judged over its root region; '
                         'chain: the old rule (any chain of touching parts to the body, closest vertex)')
    ap.add_argument('--peer-ratio', type=float, default=PEER_RATIO,
                    help='root rules: parts whose areas differ by less than this factor are peers; a peer holds a part '
                         'only where no larger part is within the part\'s size')
    args = ap.parse_args()
    clips = set(args.clips.split(',')) if args.clips else None
    results = []
    bad = False
    for path in args.glbs:
        r = audit(path, args.fps, args.threshold, clips, rules=args.rules, peer_ratio=args.peer_ratio)
        cr = r.pop('_creature')
        name = Path(path).stem
        print(f"{name}: {cr.ncomp} components, body {cr.ncomp and len(cr.comp_tris[cr.body])} tris, "
              f"{len(r['parts'])} detached in some pose")
        for k, p in sorted(r['parts'].items(), key=lambda kv: -kv[1]['worst']['gap']):
            w = p['worst']
            print(f"  part {k} ({p['joint']}, {p['where']}, {p['triangles']} tris): bind gap {p['bind_gap']:.4f}, "
                  f"worst {w['gap']:.4f} in {w['clip']} frame {w['frame']} ({w['time']:.3f} s), "
                  f"detached {p['detached_poses']}/{p['poses']} poses (and carried by a break elsewhere in "
                  f"{p['carried_poses']}; up to {w['to_body_cluster']:.4f} from the body's cluster)"
                  + (f" [{w['kind']} off {w['against']}]" if args.rules == 'root' else ''))
            if args.crops:
                crop = Path(args.crops) / f"{name}_part{k}.png"
                P = cr.pose(None if w['clip'] == 'bind' else w['clip'], w['time'])
                render_crop(cr, P, k, np.array(w['part_point']), np.array(w['attached_point']), crop,
                            extent=p['extent'] if args.rules == 'root' else None)
                p['crop'] = str(crop)
        for k, p in sorted(r['concealed'].items()):
            w = p['worst_concealed']
            print(f"  concealed: part {k} ({p['joint']}, {p['triangles']} tris) gap up to {w['gap']:.4f} in "
                  f"{w['clip']} frame {w['frame']}, hidden from every direction in {p['concealed_poses']} poses")
        for k, p in sorted(r['root_lift'].items()):
            w = p['root_lift']
            print(f"  root lift: part {k} ({p['joint']}, {p['triangles']} tris) 90th percentile {w['gap']:.4f} off "
                  f"{w['on']} in {w['clip']} frame {w['frame']}")
        for k, p in sorted(r['shallow'].items()):
            sh = p['shallowest']
            print(f"  shallow: part {k} ({p['joint']}, {p['triangles']} tris) rooted {sh['depth']:.4f} on {sh['on']} "
                  f"in {sh['clip']} frame {sh['frame']}")
        bad = bad or bool(r['parts'])
        results.append(r)
    if args.json:
        Path(args.json).write_text(json.dumps(results, indent=1, default=str))
    if args.md:
        write_md(results, Path(args.md))
    sys.exit(1 if bad else 0)


def write_md(results, out):
    """Per creature: the detached parts (gap, worst clip and frame, crop) and the shallow ones."""
    lines = []
    for r in results:
        name = Path(r['glb']).stem
        lines.append(f"### {name}")
        lines.append('')
        lines.append(f"{r['components']} components, {len(r['parts'])} visibly detached in some pose, "
                     f"{len(r['concealed'])} detached out of sight, {len(r['shallow'])} only just attached, "
                     f"{len(r.get('root_lift', {}))} with one side of the root lifting.")
        lines.append('')
        if r['parts']:
            lines.append('| Part | Joint | Where | Tris | Bind gap | Worst gap | Worst clip, frame (s) '
                         '| Detached poses |')
            lines.append('|---|---|---|---|---|---|---|---|')
            for k, p in sorted(r['parts'].items(), key=lambda kv: -kv[1]['worst']['gap']):
                w = p['worst']
                kind = {'lifted': ' (base lifted)', 'floating': ' (floating)', 'parted': ' (root parted)'}.get(
                    w.get('kind'), '')
                lines.append(f"| {k} | {p['joint']} | {p['where']} | {p['triangles']} | {p['bind_gap'] * 1000:.1f} mm "
                             f"| {w['gap'] * 1000:.1f} mm{kind} | {w['clip']} {w['frame']} ({w['time']:.2f}) "
                             f"| {p['detached_poses']}/{p['poses']} |")
            lines.append('')
            for k, p in sorted(r['parts'].items(), key=lambda kv: -kv[1]['worst']['gap']):
                if p.get('crop'):
                    rel = os.path.relpath(Path(p['crop']).resolve(), out.resolve().parent)
                    lines.append(f"![{name} part {k}]({rel})")
            lines.append('')
        if r['concealed']:
            lines.append('Detached only where no camera can see the gap: ' + ', '.join(
                f"part {k} ({p['joint']}, {p['triangles']} tris) up to {p['worst_concealed']['gap'] * 1000:.1f} mm "
                f"({p['concealed_poses']} poses)" for k, p in sorted(r['concealed'].items())) + '.')
            lines.append('')
        if r.get('root_lift'):
            lines.append('One side of the root lifts in a clip (90th percentile of its bind contact; a pivoting limb '
                         'does this too): ' + ', '.join(
                f"part {k} ({p['joint']}, {p['triangles']} tris) {p['root_lift']['gap'] * 1000:.1f} mm off "
                f"{p['root_lift']['on']} in {p['root_lift']['clip']} {p['root_lift']['frame']}"
                for k, p in sorted(r['root_lift'].items(), key=lambda kv: -kv[1]['root_lift']['gap'])) + '.')
            lines.append('')
        if r['shallow']:
            lines.append('Only just attached (shallowest rooting over all poses): ' + ', '.join(
                f"part {k} ({p['joint']}, {p['triangles']} tris) {p['shallowest']['depth'] * 1000:.1f} mm on "
                f"{p['shallowest']['on']} in {p['shallowest']['clip']} {p['shallowest']['frame']}"
                for k, p in sorted(r['shallow'].items())) + '.')
            lines.append('')
    out.write_text('\n'.join(lines) + '\n')


if __name__ == '__main__':
    main()
