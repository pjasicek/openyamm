"""Even, tightly packed UVs for a reduced creature mesh (TEXTURE_QUALITY_PASS.md), run inside Blender:

    sys.path.insert(0, '<repo>/level_generation/creatures/claude_shared'); import uv_atlas
    report = uv_atlas.unwrap(mesh_object, head_groups=('Head',), head_factor=1.8)

Default pipeline since 2026-11-12 (uv_research_20261111/REPORT.md: about 70 % atlas use against 54-57 % before, half
the visible seam, stretch p90 about 1.2):
0. Weld vertices closer than `weld` (1e-5 m; GLB imports keep vertices split at every old UV seam). Refused, mesh
   unchanged, if a face would collapse or the face order would change. The mesh must be triangulated and in its bind
   pose (armature at rest).
1. Charts: `charts='partuv'`, PartUV (Apache-2.0) with a part tree built from the skin weights, threshold
   `partuv_threshold` 1.25 (partuv_charts.py in claude_shared/partuv_venv; no PartField code or weights). If PartUV
   is missing or fails on the mesh, xatlas charts are used instead (xatlas_charts.py in xatlas_venv).
2. Charts below `merge_below` triangles are merged into the neighbour they share the longest boundary with and the
   merged charts are flattened again by Blender (`method`, SLIM). A merged chart that overlaps itself, flips, stretches
   an edge, collapses a triangle or (`max_stretch`, 'auto' = 1.25 on PartUV charts, none on xatlas charts) exceeds the
   p90 stretch limit goes back to its starting pieces. `correct_aspect=False`: a non-square image on the material
   cannot squeeze the charts.
3. Seam pass (`seam_rounds` 6, `seam_stretch` 1.25): rounds of merges of the neighbouring charts with the most
   visible shared border (per-face visibility from 72 cameras, computed here or passed as `vis`; `vis_objects` add
   occluders such as the creature's other texture sets); a merged chart that is no longer a disc is cut open along its
   least visible path; a merge is kept only if it passes the same checks and its p90 stretch stays under
   `seam_stretch`.
4. Every chart is scaled to one texel density (head charts `head_factor` times denser, linear: an island is head when
   at least half of its surface is weighted to `head_groups`; `group_factors` for more classes).
5. Pack: `packer='sparrow'` (sparrow_pack.py in claude_shared/sparrow_venv): one uniform scale, `2 x margin_px`
   texels between islands, continuous rotation, `sparrow_runs` runs of `sparrow_seconds` searching the largest scale
   that fits one `size` square (v 0..`height_share`). If sparrow is missing or fails, the xatlas packer is used
   (brute force; `fine=250, steps=0` sweeps the fast packer instead).
Every fallback is printed ('UV_ATLAS FALLBACK') and listed in the report's 'fallbacks'; 'charts_used' and
'packer_used' say what ran. The report also carries the seam measures ('seams': total, visible, exposed and hidden
seam length in creature sizes), the weld result and the seam pass log.

SWITCH BACK to the pre-2026-11-12 route (finished projects' scripts, reproducing an old layout):
    unwrap(obj, ..., charts='xatlas', packer='xatlas', seam_rounds=0)
runs exactly the old code path (xatlas charts, merge without a stretch limit, xatlas brute-force pack). The weld and
the aspect guard are no-ops on a welded mesh without a non-square image; add weld=0, correct_aspect=True for the old
behaviour on split or non-square-textured meshes too. Both routes are stochastic in packing: never re-run a UV script
once its upload went to Meshy.

Other options: cut_closed=True (meshes of separate closed pieces, the Dagrell's bones): merged charts that are closed
or have several boundary loops are cut into discs first, so a small closed piece becomes one chart instead of its
fragments; one that still fails is retried as patches of at least 8 triangles. max_stretch sends charts whose p90
stretch is above it down the same path (opened closed pieces flatten with long needles; the Dagrell's tail blade
reached 6.8); retry_stretch, if given, is the limit for those patches. packer='blender' packs with Blender's concave
packer (44-51 % on the Magreeb, worse); charts='bones' starts from one chart per dominant deform bone cut into discs
on the underside (experimental: 50 % on the Magreeb).
Replaces every UV layer of the mesh with one 'UVMap'.
"""
import os
import subprocess
import tempfile
from collections import defaultdict

import bmesh
import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
VENV = os.path.join(HERE, 'xatlas_venv', 'bin', 'python')
TOOL = os.path.join(HERE, 'xatlas_charts.py')
PARTUV_VENV = os.path.join(HERE, 'partuv_venv', 'bin', 'python')
PARTUV_TOOL = os.path.join(HERE, 'partuv_charts.py')
SPARROW_PY = os.path.join(HERE, 'sparrow_venv', 'py', 'bin', 'python')
SPARROW_BIN = os.path.join(HERE, 'sparrow_venv', 'bin', 'sparrow')
SPARROW_TOOL = os.path.join(HERE, 'sparrow_pack.py')


def _xatlas(mode, inputs, *options):
    with tempfile.TemporaryDirectory() as tmp:
        src, dst = os.path.join(tmp, 'in.npz'), os.path.join(tmp, 'out.npz')
        np.savez(src, **inputs)
        out = subprocess.run([VENV, '-I', TOOL, mode, src, dst, *map(str, options)], capture_output=True, text=True)
        print(out.stdout.strip())
        if out.returncode:
            raise RuntimeError(f'xatlas_charts.py {mode} failed:\n{out.stderr}')
        return dict(np.load(dst))


def _signed(uv):
    return ((uv[:, 1, 0] - uv[:, 0, 0]) * (uv[:, 2, 1] - uv[:, 0, 1])
            - (uv[:, 2, 0] - uv[:, 0, 0]) * (uv[:, 1, 1] - uv[:, 0, 1])) / 2


def _overlap(uv, res=256):
    """Fraction of a chart's UV area covered twice (rasterised in the chart's own bounding box) and flipped share."""
    lo, hi = uv.reshape(-1, 2).min(0), uv.reshape(-1, 2).max(0)
    scale = res / max(float((hi - lo).max()), 1e-12)
    p = (uv - lo) * scale
    cover = np.zeros((res + 2, res + 2), np.int32)
    gy, gx = np.mgrid[0:res + 2, 0:res + 2] + 0.5
    signed = _signed(p)
    for t, s in zip(p, signed):
        if abs(s) < 1e-12:
            continue
        x0, y0 = np.floor(t.min(0)).astype(int)
        x1, y1 = np.ceil(t.max(0)).astype(int) + 1
        sx, sy = gx[y0:y1, x0:x1], gy[y0:y1, x0:x1]
        a, b, c = t
        w0 = (b[0] - a[0]) * (sy - a[1]) - (b[1] - a[1]) * (sx - a[0])
        w1 = (c[0] - b[0]) * (sy - b[1]) - (c[1] - b[1]) * (sx - b[0])
        w2 = (a[0] - c[0]) * (sy - c[1]) - (a[1] - c[1]) * (sx - c[0])
        inside = ((w0 >= 0) & (w1 >= 0) & (w2 >= 0)) | ((w0 <= 0) & (w1 <= 0) & (w2 <= 0))
        cover[y0:y1, x0:x1] += inside
    covered = (cover > 0).sum()
    double = (cover > 1).sum()
    dominant = np.sign(signed.sum())
    flipped = float(np.abs(signed[np.sign(signed) != dominant]).sum() / max(np.abs(signed).sum(), 1e-12))
    return double / max(covered, 1), flipped


def _edge_stretch(uv, xyz):
    """Largest edge length ratio (UV / 3D) over the chart's mean scale: SLIM sometimes pulls needle triangles across
    the atlas, which keeps the overlap test happy but wrecks packing and the texel density."""
    lu = np.linalg.norm(uv - np.roll(uv, -1, 1), axis=2).ravel()
    lx = np.linalg.norm(xyz - np.roll(xyz, -1, 1), axis=2).ravel()
    ok = lx > 1e-9
    a2, a3 = np.abs(_signed(uv)).sum(), np.linalg.norm(np.cross(xyz[:, 1] - xyz[:, 0], xyz[:, 2] - xyz[:, 0]),
                                                       axis=1).sum() / 2
    scale = np.sqrt(a2 / max(a3, 1e-18))
    return float((lu[ok] / lx[ok]).max() / max(scale, 1e-18))


def _stretch_ratio(uv, xyz, area3):
    """Area-weighted p90 of the UV map's singular-value ratio in one chart (as texture_quality.py reports it)."""
    e1, e2 = xyz[:, 1] - xyz[:, 0], xyz[:, 2] - xyz[:, 0]
    d1, d2 = uv[:, 1] - uv[:, 0], uv[:, 2] - uv[:, 0]
    u = e1 / np.maximum(np.linalg.norm(e1, axis=1, keepdims=True), 1e-12)
    n = np.cross(e1, e2)
    v = np.cross(n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12), u)
    x = np.stack([np.stack([(e1 * u).sum(1), (e1 * v).sum(1)], 1), np.stack([(e2 * u).sum(1), (e2 * v).sum(1)], 1)], 2)
    y = np.stack([d1, d2], 2)
    ok = np.abs(np.linalg.det(x)) > 1e-14
    if not ok.any():
        return np.inf
    s = np.linalg.svd(y[ok] @ np.linalg.inv(x[ok]), compute_uv=False)
    ratio = s[:, 0] / np.maximum(s[:, 1], 1e-9)
    order = np.argsort(ratio)
    c = np.cumsum(area3[ok][order]) / area3[ok].sum()
    return float(ratio[order][min(np.searchsorted(c, 0.9), len(c) - 1)])


def _density_ratio(uv, area3):
    """Area-weighted p95 / p5 of the per-triangle texel density inside one chart (SLIM squeezes caps); infinite when any
    triangle is below a fifth of the chart median."""
    d = np.sqrt(np.abs(_signed(uv)) / np.maximum(area3, 1e-18))
    order = np.argsort(d)
    c = np.cumsum(area3[order]) / max(area3.sum(), 1e-18)
    median = d[order][np.searchsorted(c, 0.5)]
    if not median > 0:
        return np.inf          # the whole chart collapsed to a point or a line (Bat m158 texpass: 3 charts, 92 triangles)
    if (d < 0.2 * median).any():
        return np.inf          # a collapsed triangle (SLIM squeezed a strip to a line; Magreeb v8 shipped 12)
    return float(d[order][np.searchsorted(c, 0.95)] / max(d[order][np.searchsorted(c, 0.05)], 1e-18))


def _bone_segments(obj, tri, pos, edge_faces, edge_len, min_segment):
    """Charts by skeleton: each face goes to its dominant deform bone (a few majority-vote passes straighten the
    borders), segments under min_segment triangles join the neighbour with the longest shared border, and each
    segment is cut into a disc: every extra boundary loop is joined to the first by the cheapest edge path, which
    prefers edges on faces turned down (seams on the underside of limbs and body). Closed or holed segments get
    label -1 (left to xatlas). Returns per-face labels and the set of cut edges."""
    import heapq
    me = obj.data
    n = len(tri)
    weights = np.zeros((len(me.vertices), len(obj.vertex_groups)))
    for v in me.vertices:
        for g in v.groups:
            weights[v.index, g.group] = g.weight
    label = weights[tri].sum(1).argmax(1)
    neighbours = [[] for _ in range(n)]
    for e, faces in edge_faces.items():
        if len(faces) == 2:
            a, b = faces
            neighbours[a].append(b)
            neighbours[b].append(a)
    for _ in range(3):
        new = label.copy()
        for f in range(n):
            votes = np.bincount([label[g] for g in neighbours[f]] + [label[f]])
            if votes.max() >= 2 and votes[label[f]] < votes.max():
                new[f] = votes.argmax()
        label = new
    # connected pieces of each bone become separate segments
    seg = -np.ones(n, np.int64)
    count = 0
    for f in range(n):
        if seg[f] >= 0:
            continue
        stack, seg[f] = [f], count
        while stack:
            g = stack.pop()
            for h in neighbours[g]:
                if seg[h] < 0 and label[h] == label[f]:
                    seg[h] = count
                    stack.append(h)
        count += 1
    while True:
        sizes = np.bincount(seg, minlength=count)
        small = [c for c in np.argsort(sizes) if 0 < sizes[c] < min_segment]
        if not small:
            break
        c = small[0]
        shared = defaultdict(float)
        for e, faces in edge_faces.items():
            labels = {int(seg[f]) for f in faces}
            if c in labels and len(labels) > 1:
                for other in labels - {c}:
                    shared[other] += edge_len[e]
        if not shared:
            sizes[c] = min_segment
            seg[seg == c] = count
            count += 1
            continue
        seg[seg == c] = max(shared, key=shared.get)
    world = obj.matrix_world.to_3x3()
    normal_z = np.array([(world @ p.normal).normalized().z for p in me.polygons])
    cuts = set()
    for c in np.unique(seg):
        faces = np.nonzero(seg == c)[0]
        fset = set(faces.tolist())
        edges = {}
        for e, fs in edge_faces.items():
            inside = [f for f in fs if f in fset]
            if inside:
                edges[e] = (len(inside), len(fs))
        verts = {v for e in edges for v in e}
        boundary = [e for e, (k, total) in edges.items() if k == 1]
        chi = len(verts) - len(edges) + len(faces)
        # boundary loops
        parent = {v: v for e in boundary for v in e}

        def find(v):
            while parent[v] != v:
                parent[v] = parent[parent[v]]
                v = parent[v]
            return v

        for a, b in boundary:
            parent[find(a)] = find(b)
        loops = defaultdict(set)
        for v in parent:
            loops[find(v)].add(v)
        loops = list(loops.values())
        if not loops or chi != 2 - len(loops):
            seg[faces] = -1                  # closed or not genus 0: xatlas
            continue
        adjacency = defaultdict(list)
        for (a, b), (k, total) in edges.items():
            if k == 2 or total == 1:
                down = np.mean([normal_z[f] for f in edge_faces[(a, b)] if f in fset])
                w = edge_len[(a, b)] * (0.5 + (1.0 + down))
                adjacency[a].append((b, w, (a, b)))
                adjacency[b].append((a, w, (a, b)))
        connected = set(loops[0])
        remaining = [set(l) for l in loops[1:]]
        while remaining:
            dist = {v: 0.0 for v in connected}
            prev = {}
            heap = [(0.0, v) for v in connected]
            heapq.heapify(heap)
            target = None
            targets = set().union(*remaining)
            while heap:
                d, v = heapq.heappop(heap)
                if d > dist.get(v, np.inf):
                    continue
                if v in targets:
                    target = v
                    break
                for u, w, e in adjacency[v]:
                    if d + w < dist.get(u, np.inf):
                        dist[u] = d + w
                        prev[u] = (v, e)
                        heapq.heappush(heap, (d + w, u))
            if target is None:
                seg[faces] = -1
                break
            v = target
            while v in prev:
                v, e = prev[v]
                cuts.add(e)
                connected.add(v)
            hit = next(l for l in remaining if target in l)
            remaining.remove(hit)
            connected |= hit
    return seg, cuts


def _disc_cuts(faces, tri, edge_faces, edge_len, normal_z):
    """Seam edges that open one connected chart into a disc, or None when its topology has handles. A chart with no
    boundary (a whole closed piece, the Dagrell's bones: Blender cannot unwrap those) is cut along its longest shortest
    path; several boundary loops are joined by shortest paths. Paths prefer edges on faces turned down."""
    import heapq
    fset = set(int(f) for f in faces)
    edges = {}
    for f in fset:
        t = tri[f]
        for k in range(3):
            a, b = int(t[k]), int(t[(k + 1) % 3])
            edges[(min(a, b), max(a, b))] = 0
    for e in edges:
        edges[e] = sum(1 for f in edge_faces[e] if f in fset)
    verts = {v for e in edges for v in e}
    boundary = [e for e, k in edges.items() if k == 1]
    parent = {v: v for e in boundary for v in e}

    def find(v):
        while parent[v] != v:
            parent[v] = parent[parent[v]]
            v = parent[v]
        return v

    for a, b in boundary:
        parent[find(a)] = find(b)
    loops = defaultdict(set)
    for v in parent:
        loops[find(v)].add(v)
    loops = list(loops.values())
    if len(verts) - len(edges) + len(fset) != 2 - len(loops):
        return None
    adjacency = defaultdict(list)
    for (a, b), k in edges.items():
        if k == 2:
            up = np.mean([normal_z[f] for f in edge_faces[(a, b)] if f in fset])
            w = edge_len[(a, b)] * (1.5 + up)
            adjacency[a].append((b, w, (a, b)))
            adjacency[b].append((a, w, (a, b)))

    def sweep(sources):
        dist, prev = {v: 0.0 for v in sources}, {}
        heap = [(0.0, v) for v in sources]
        heapq.heapify(heap)
        while heap:
            d, v = heapq.heappop(heap)
            if d > dist[v]:
                continue
            for u, w, e in adjacency[v]:
                if d + w < dist.get(u, np.inf):
                    dist[u], prev[u] = d + w, (v, e)
                    heapq.heappush(heap, (d + w, u))
        return dist, prev

    cuts = set()
    if not loops:
        far = max(sweep([next(iter(verts))])[0].items(), key=lambda kv: kv[1])[0]
        dist, prev = sweep([far])
        v = max(dist.items(), key=lambda kv: kv[1])[0]
        while v in prev:
            v, e = prev[v]
            cuts.add(e)
        return cuts
    connected, remaining = set(loops[0]), [set(l) for l in loops[1:]]
    while remaining:
        dist, prev = sweep(connected)
        targets = [(dist[v], v) for l in remaining for v in l if v in dist]
        if not targets:
            return None
        v = min(targets)[1]
        hit = next(l for l in remaining if v in l)
        while v in prev:
            v, e = prev[v]
            cuts.add(e)
            connected.add(v)
        remaining.remove(hit)
        connected |= hit
    return cuts


def _is_disc(faces, tri, edge_faces):
    fset = set(int(f) for f in faces)
    edges = {}
    for f in fset:
        t = tri[f]
        for k in range(3):
            a, b = int(t[k]), int(t[(k + 1) % 3])
            e = (min(a, b), max(a, b))
            edges[e] = edges.get(e, 0) + 1
    verts = {v for e in edges for v in e}
    boundary = [e for e, k in edges.items() if k == 1]
    parent = {v: v for e in boundary for v in e}

    def find(v):
        while parent[v] != v:
            parent[v] = parent[parent[v]]
            v = parent[v]
        return v

    for a, b in boundary:
        parent[find(a)] = find(b)
    loops = len({find(v) for v in parent})
    return loops == 1 and len(verts) - len(edges) + len(fset) == 1


def _hidden_cuts(faces, tri, edge_faces, edge_len, vis, vis_floor):
    """Like _disc_cuts, but the path cost is length x (edge visibility + vis_floor): the cut goes where the
    cameras see least."""
    import heapq
    fset = set(int(f) for f in faces)
    edges = {}
    for f in fset:
        t = tri[f]
        for k in range(3):
            a, b = int(t[k]), int(t[(k + 1) % 3])
            edges[(min(a, b), max(a, b))] = 0
    for e in edges:
        edges[e] = sum(1 for f in edge_faces[e] if f in fset)
    verts = {v for e in edges for v in e}
    boundary = [e for e, k in edges.items() if k == 1]
    parent = {v: v for e in boundary for v in e}

    def find(v):
        while parent[v] != v:
            parent[v] = parent[parent[v]]
            v = parent[v]
        return v

    for a, b in boundary:
        parent[find(a)] = find(b)
    loops = defaultdict(set)
    for v in parent:
        loops[find(v)].add(v)
    loops = list(loops.values())
    if len(verts) - len(edges) + len(fset) != 2 - len(loops):
        return None
    adjacency = defaultdict(list)
    for (a, b), k in edges.items():
        if k == 2:
            v = np.mean([vis[f] for f in edge_faces[(a, b)] if f in fset])
            w = edge_len[(a, b)] * (v + vis_floor)
            adjacency[a].append((b, w, (a, b)))
            adjacency[b].append((a, w, (a, b)))

    def sweep(sources):
        dist, prev = {v: 0.0 for v in sources}, {}
        heap = [(0.0, v) for v in sources]
        heapq.heapify(heap)
        while heap:
            d, v = heapq.heappop(heap)
            if d > dist[v]:
                continue
            for u, w, e in adjacency[v]:
                if d + w < dist.get(u, np.inf):
                    dist[u], prev[u] = d + w, (v, e)
                    heapq.heappush(heap, (d + w, u))
        return dist, prev

    cuts = set()
    if not loops:
        return None
    connected, remaining = set(loops[0]), [set(l) for l in loops[1:]]
    while remaining:
        dist, prev = sweep(connected)
        targets = [(dist[v], v) for l in remaining for v in l if v in dist]
        if not targets:
            return None
        v = min(targets)[1]
        hit = next(l for l in remaining if v in l)
        while v in prev:
            v, e = prev[v]
            cuts.add(e)
            connected.add(v)
        remaining.remove(hit)
        connected |= hit
    return cuts


def _seam_removal(obj, me, tri, p3, area3, edge_faces, edge_len, label, uv, cuts, vis, flatten, write, rounds,
                  seam_stretch, seam_pairs, vis_floor, seam_min, max_overlap, max_edge_stretch, max_density_ratio,
                  log):
    """Greedy: merge the chart pairs with the most visible shared border; keep merges whose flattened chart passes
    the checks. label, uv and cuts are updated in place / returned."""
    n = len(tri)
    tried = set()
    for r in range(rounds):
        border = defaultdict(float)
        for e, faces in edge_faces.items():
            if len(faces) == 2 and e not in cuts:
                a, b = int(label[faces[0]]), int(label[faces[1]])
                if a != b:
                    border[(min(a, b), max(a, b))] += edge_len[e] * (vis[faces[0]] + vis[faces[1]]) / 2
        order = sorted(((w, pr) for pr, w in border.items() if pr not in tried and w > seam_min), reverse=True)
        used, chosen = set(), []
        for w, (a, b) in order:
            if a in used or b in used:
                continue
            used |= {a, b}
            chosen.append((a, b, w))
            if len(chosen) >= seam_pairs:
                break
        if not chosen:
            break
        before_uv, before_label, before_cuts = uv.copy(), label.copy(), set(cuts)
        new_cuts = {}
        for a, b, w in chosen:
            tried.add((a, b))
            label[label == b] = a
            faces = np.nonzero(label == a)[0]
            if not _is_disc(faces, tri, edge_faces):
                found = _hidden_cuts(faces, tri, edge_faces, edge_len, vis, vis_floor)
                if found:
                    new_cuts[a] = found
                    cuts |= found
        chosen_faces = np.isin(label, [a for a, _, _ in chosen])
        write(uv)
        uv = flatten(chosen_faces)
        kept = 0
        for a, b, w in chosen:
            faces = np.nonzero(label == a)[0]
            double, flipped = _overlap(uv[faces])
            stretch, ratio = _edge_stretch(uv[faces], p3[faces]), _density_ratio(uv[faces], area3[faces])
            sp90 = _stretch_ratio(uv[faces], p3[faces], area3[faces])
            bad = (double > max_overlap or flipped > max_overlap or stretch > max_edge_stretch
                   or ratio > max_density_ratio or sp90 > seam_stretch)
            if bad:
                print(f'UV_SEAM reject {a}+{b}: {len(faces)} tris, overlap {double:.3f} flipped {flipped:.3f} '
                      f'edge {stretch:.1f} density {ratio:.1f} p90 {sp90:.2f}', flush=True)
                restore = np.isin(np.arange(n), faces)
                uv[restore] = before_uv[restore]
                label[restore] = before_label[restore]
                for e in new_cuts.get(a, ()):
                    if e not in before_cuts:
                        cuts.discard(e)
            else:
                kept += 1
        log.append({'round': r, 'tried': len(chosen), 'kept': kept,
                    'charts': int(len(np.unique(label)))})
        print(f'UV_SEAM round {r}: tried {len(chosen)} kept {kept} charts {len(np.unique(label))}', flush=True)
    return uv


def _weld(obj, dist):
    """Merge vertices closer than dist (GLB imports keep vertices split at every old UV seam, which makes hundreds of
    loose pieces). Refused, with the mesh unchanged, when any face would collapse or the face order would change.
    Returns (vertices before, after, note)."""
    me = obj.data
    before = len(me.vertices)
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    doubles = bmesh.ops.find_doubles(bm, verts=bm.verts, dist=dist)['targetmap']
    if not doubles:
        bm.free()
        return before, before, 'nothing to weld'
    target = {v.index: t.index for v, t in doubles.items()}
    for f in bm.faces:
        ids = [target.get(v.index, v.index) for v in f.verts]
        if len(set(ids)) < len(ids):
            bm.free()
            return before, before, 'refused: a face would collapse'
    centres = [tuple(round(c, 7) for c in f.calc_center_median()) for f in bm.faces]
    bmesh.ops.weld_verts(bm, targetmap=doubles)
    bm.faces.ensure_lookup_table()
    if len(bm.faces) != len(centres) or any(tuple(round(c, 7) for c in f.calc_center_median()) != centres[i]
                                            for i, f in enumerate(bm.faces)):
        bm.free()
        return before, before, 'refused: the face order would change'
    bm.to_mesh(me)
    bm.free()
    me.update()
    return before, len(me.vertices), 'welded'


def _visibility(obj, tri, extra=(), elevations=(5.0, 20.0, 35.0), azimuths=24):
    """Per-face visibility (0 hidden .. 1 exposed): cosine-weighted share of orthographic game views slightly above the
    creature, all around (72 by default), that see the face; occlusion by BVH ray casts on the bind pose (the object
    plus `extra` meshes, e.g. the creature's other texture sets), divided by its 95th percentile and clipped to 1."""
    import math
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    me = obj.data
    mw = obj.matrix_world
    verts = [mw @ v.co for v in me.vertices]
    polys = [tuple(int(i) for i in t) for t in tri]
    all_verts, all_polys = list(verts), list(polys)
    for other in extra:
        offset = len(all_verts)
        all_verts += [other.matrix_world @ v.co for v in other.data.vertices]
        all_polys += [tuple(offset + i for i in p.vertices) for p in other.data.polygons]
    bvh = BVHTree.FromPolygons(all_verts, all_polys, all_triangles=False)
    pts = np.array(verts)
    extent = float(np.ptp(pts, 0).max())
    dirs = []
    for e in elevations:
        for k in range(azimuths):
            a = 2 * math.pi * k / azimuths
            dirs.append((math.cos(math.radians(e)) * math.cos(a), math.cos(math.radians(e)) * math.sin(a),
                         math.sin(math.radians(e))))
    dirs = np.array(dirs)
    eps = extent * 1e-4
    raw = np.zeros(len(polys))
    for f, p in enumerate(polys):
        a, b, c = (verts[i] for i in p)
        n = (b - a).cross(c - a)
        if n.length == 0:
            continue
        n.normalize()
        centre = (a + b + c) / 3
        acc = 0.0
        for d, dot in zip(dirs, dirs @ np.array(n)):
            if dot <= 0.05:
                continue
            hit = bvh.ray_cast(centre + n * eps + Vector(d) * eps, Vector(d), extent * 4)
            if hit[0] is None:
                acc += dot
        raw[f] = acc / len(dirs)
    return np.clip(raw / max(np.percentile(raw, 95), 1e-9), 0, 1)


def _seam_metrics(uv, tri, pos, vis, edge_faces):
    """Seam lengths on the final UVs in creature sizes (largest bounding-box extent): an edge is a seam when its two
    faces disagree in UV at either end, or when it is open. 'visible' = length x the faces' mean visibility."""
    extent = float(np.ptp(pos, 0).max()) or 1.0

    def corner(f, v):
        return uv[f][int(np.nonzero(tri[f] == v)[0][0])]

    length, seen = [], []
    for (a, b), faces in edge_faces.items():
        if len(faces) == 2:
            f, g = faces
            if (np.abs(corner(f, a) - corner(g, a)).max() <= 1e-6
                    and np.abs(corner(f, b) - corner(g, b)).max() <= 1e-6):
                continue
            v = (vis[f] + vis[g]) / 2
        else:
            v = float(np.mean([vis[f] for f in faces]))
        length.append(np.linalg.norm(pos[a] - pos[b]) / extent)
        seen.append(v)
    length, seen = np.array(length), np.array(seen)
    total = float(length.sum()) or 1e-12
    return {'total_len': round(total, 2), 'visible_len': round(float((length * seen).sum()), 2),
            'exposed_len': round(float(length[seen >= 0.5].sum()), 2),
            'hidden_len': round(float(length[seen < 0.15].sum()), 2),
            'hidden_share_pct': round(100 * float(length[seen < 0.15].sum()) / total, 1),
            'note': 'creature sizes; visible = length x face visibility from 72 cameras (exposed >= 0.5, '
                    'hidden < 0.15)'}


def _islands(uv, tri):
    """UV-connected pieces per face: two faces join across an edge when both ends share UV coordinates."""
    parent = list(range(len(tri)))

    def find(f):
        while parent[f] != f:
            parent[f] = parent[parent[f]]
            f = parent[f]
        return f

    corners = {}
    for f, t in enumerate(tri):
        for k in range(3):
            a, b = int(t[k]), int(t[(k + 1) % 3])
            key = (min(a, b), max(a, b))
            ua, ub = uv[f][k], uv[f][(k + 1) % 3]
            if a > b:
                ua, ub = ub, ua
            corners.setdefault(key, []).append((f, ua, ub))
    for faces in corners.values():
        for i in range(1, len(faces)):
            f, ua, ub = faces[0]
            g, va, vb = faces[i]
            if np.abs(ua - va).max() <= 1e-9 and np.abs(ub - vb).max() <= 1e-9:
                parent[find(g)] = find(f)
    return np.unique([find(f) for f in range(len(tri))], return_inverse=True)[1].ravel()


def _partuv(obj, pos, tri, threshold):
    """PartUV charts with the skin-weight part tree (partuv_charts.py in partuv_venv); PAMO (CUDA) first, then CPU."""
    weights = np.zeros((len(pos), max(len(obj.vertex_groups), 1)), np.float32)
    for v in obj.data.vertices:
        for g in v.groups:
            weights[v.index, g.group] = g.weight
    if not obj.vertex_groups:
        weights[:] = 1.0
    if not os.path.exists(PARTUV_VENV):
        raise RuntimeError(f'{PARTUV_VENV} is missing (setup: TEXTURE_QUALITY_PASS.md)')
    errors = []
    with tempfile.TemporaryDirectory() as tmp:
        src, dst = os.path.join(tmp, 'in.npz'), os.path.join(tmp, 'out.npz')
        np.savez(src, pos=pos, tri=tri, weights=weights)
        for extra in ([], ['--no-pamo']):
            out = subprocess.run([PARTUV_VENV, '-I', PARTUV_TOOL, src, dst, '--threshold', str(threshold), *extra],
                                 capture_output=True, text=True, cwd=tmp)
            lines = [l for l in out.stdout.splitlines() if l.startswith('PARTUV')]
            if lines:
                print(lines[-1], flush=True)
            if out.returncode == 0:
                return dict(np.load(dst))
            errors.append((out.stderr or out.stdout)[-600:])
    raise RuntimeError('partuv_charts.py failed: ' + ' | '.join(errors))


def _sparrow(uv, island, size, height_share, sep, seconds, runs, fill):
    if not (os.path.exists(SPARROW_PY) and os.path.exists(SPARROW_BIN)):
        raise RuntimeError(f'{SPARROW_BIN} or its Python is missing (setup: TEXTURE_QUALITY_PASS.md)')
    with tempfile.TemporaryDirectory() as tmp:
        src, dst = os.path.join(tmp, 'in.npz'), os.path.join(tmp, 'out.npz')
        np.savez(src, uv=uv, island=island)
        out = subprocess.run([SPARROW_PY, '-I', SPARROW_TOOL, src, dst, '--size', str(size), '--height-share',
                              str(height_share), '--sep', str(sep), '--seconds', str(seconds), '--runs', str(runs),
                              '--fill', str(fill), '--sparrow', SPARROW_BIN], capture_output=True, text=True, cwd=tmp)
        for line in out.stdout.splitlines():
            if line.startswith('SPARROW'):
                print(line, flush=True)
        if out.returncode:
            raise RuntimeError('sparrow_pack.py failed: ' + (out.stderr or out.stdout)[-600:])
        result = dict(np.load(dst))
        return result['uv'], float(result['k'])


def unwrap(obj, head_groups=(), head_factor=1.0, margin_px=2, size=2048, max_cost=2.0, roundness=0.5,
           merge_below=12, method='MINIMUM_STRETCH', max_overlap=0.003, max_edge_stretch=3.0, packer='sparrow',
           charts='partuv', min_segment=24, max_density_ratio=2.5, height_share=1.0, cut_closed=False, fine=0, steps=10,
           max_stretch='auto', retry_stretch=None, group_factors=None, seam_rounds=6, seam_stretch=1.25,
           seam_pairs=60, vis_floor=0.05, seam_min=0.0, vis=None, vis_objects=(), partuv_threshold=1.25,
           weld=1e-5, correct_aspect=False, sparrow_seconds=60, sparrow_runs=5, sparrow_fill=0.66):
    fallbacks = []
    weld_note = None
    if weld:
        before, after, note = _weld(obj, weld)
        weld_note = {'distance': weld, 'vertices_before': before, 'vertices_after': after, 'result': note}
        if after != before or note.startswith('refused'):
            print(f'UV_ATLAS weld {weld}: {before} -> {after} vertices ({note})', flush=True)
    me = obj.data
    if any(len(p.vertices) != 3 for p in me.polygons):
        raise ValueError(f'{obj.name} must be triangulated')
    n = len(me.polygons)
    pos = np.array([v.co for v in me.vertices], np.float64)
    tri = np.array([p.vertices[:] for p in me.polygons], np.int32)
    charts_used = charts
    res = None
    if charts == 'partuv':
        try:
            res = _partuv(obj, pos, tri, partuv_threshold)
            res['chart'] = np.unique(res['chart'], return_inverse=True)[1].ravel()
            if len(res['chart']) != n or not np.isfinite(res['uv']).all():
                raise RuntimeError('PartUV returned an incomplete chart set')
        except Exception as error:      # any PartUV failure: the xatlas charts below
            note = f'charts: PartUV failed ({str(error)[:300]}), fell back to xatlas charts'
            print('UV_ATLAS FALLBACK ' + note, flush=True)
            fallbacks.append(note)
            res, charts_used = None, 'xatlas'
    if res is None:
        res = _xatlas('charts', {'positions': pos.astype(np.float32), 'triangles': tri},
                      '--max-cost', max_cost, '--roundness', roundness)
    if max_stretch == 'auto':
        max_stretch = 1.25 if charts_used == 'partuv' else None   # SLIM merges on PartUV charts re-add stretch
    corner, chart = res['uv'].astype(np.float64), res['chart']
    p3 = pos[tri]
    area3 = np.linalg.norm(np.cross(p3[:, 1] - p3[:, 0], p3[:, 2] - p3[:, 0]), axis=1) / 2

    # ---- merge small charts into the neighbour with the longest shared boundary
    edge_faces = defaultdict(list)
    for f, t in enumerate(tri):
        for k in range(3):
            a, b = sorted((t[k], t[(k + 1) % 3]))
            edge_faces[(a, b)].append(f)
    edge_len = {e: float(np.linalg.norm(pos[e[0]] - pos[e[1]])) for e in edge_faces}
    label = chart.copy()
    merged = set()
    while True:
        counts = np.bincount(label, minlength=label.max() + 1)
        small = [c for c in np.argsort(counts) if 0 < counts[c] < merge_below]
        changed = False
        for c in small:
            faces = np.nonzero(label == c)[0]
            if not len(faces) or len(faces) >= merge_below:
                continue
            shared = defaultdict(float)
            for f in faces:
                t = tri[f]
                for k in range(3):
                    e = tuple(sorted((t[k], t[(k + 1) % 3])))
                    for g in edge_faces[e]:
                        if label[g] != c:
                            shared[label[g]] += edge_len[e]
            if not shared:
                continue
            target = max(shared, key=shared.get)
            label[faces] = target
            merged.add(int(target))
            merged.discard(int(c))
            changed = True
        if not changed:
            break
    merged = {c for c in merged if (label == c).any()}
    cuts = set()
    if charts == 'bones':
        label, cuts = _bone_segments(obj, tri, pos, edge_faces, edge_len, min_segment)
        fallback = label < 0
        merged = set(int(c) for c in np.unique(label[~fallback]))
        label[fallback] = label.max() + 1 + chart[fallback]
    elif cut_closed:
        # separate closed pieces: merged charts cover a whole piece, which only unwraps once it is cut open
        normal_z = np.array([p.normal.z for p in me.polygons])
        for c in sorted(merged):
            found = _disc_cuts(np.nonzero(label == c)[0], tri, edge_faces, edge_len, normal_z)
            if found:
                cuts |= found

    # ---- starting charts everywhere, merged charts re-flattened by Blender between seams at the chart boundaries
    for layer in list(me.uv_layers):
        me.uv_layers.remove(layer)
    me.uv_layers.new(name='UVMap')

    def write(uv):
        flat = np.zeros((len(me.loops), 2), np.float32)
        for p in me.polygons:
            flat[list(p.loop_indices)] = uv[p.index]
        me.uv_layers['UVMap'].data.foreach_set('uv', flat.ravel())   # fresh: edit mode reallocates layers

    def read():
        flat = np.zeros(len(me.loops) * 2, np.float32)
        me.uv_layers['UVMap'].data.foreach_get('uv', flat)
        flat = flat.reshape(-1, 2)
        return np.array([flat[list(p.loop_indices)] for p in me.polygons], np.float64)

    write(corner)
    bpy.context.view_layer.objects.active = obj
    for o in bpy.context.view_layer.objects:
        o.select_set(o == obj)
    reverted = 0

    def flatten(chosen):
        key_to_edge = {tuple(sorted(e.vertices)): e for e in me.edges}   # fresh: edit mode reallocates the mesh
        for e, faces in edge_faces.items():
            key_to_edge[e].use_seam = len({int(label[f]) for f in faces}) > 1 or e in cuts
        before = read()
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.context.scene.tool_settings.use_uv_select_sync = True
        bpy.ops.mesh.select_mode(type='FACE')
        bpy.ops.mesh.reveal()
        bpy.ops.mesh.select_all(action='DESELECT')
        bm = bmesh.from_edit_mesh(me)
        bm.faces.ensure_lookup_table()
        for f in bm.faces:                   # only the merged charts: the others are hidden from the unwrap
            if chosen[f.index]:
                f.select_set(True)
            else:
                f.hide_set(True)
        bmesh.update_edit_mesh(me)
        # correct_aspect=True would squeeze every chart by the aspect of a non-square image on the material (an
        # installed 4128 x 2048 atlas gave p90 stretch 2.2); False is the default since 2026-11-12
        bpy.ops.uv.unwrap(method=method, fill_holes=True, correct_aspect=correct_aspect, margin=0.0)
        bpy.ops.mesh.reveal(select=False)
        bpy.ops.object.mode_set(mode='OBJECT')
        out = read()
        untouched = ~chosen & np.any(np.abs(out - before) > 1e-6, axis=(1, 2))
        assert not untouched.any(), f'unwrap changed {int(untouched.sum())} faces outside the merged charts'
        return out

    def verify(uv, groups, limit):
        """Sends bad charts back to their starting pieces; returns their faces."""
        nonlocal reverted
        failed = []
        for c in groups:
            faces = np.nonzero(label == c)[0]
            double, flipped = _overlap(uv[faces])
            stretch, ratio = _edge_stretch(uv[faces], p3[faces]), _density_ratio(uv[faces], area3[faces])
            bad = (double > max_overlap or flipped > max_overlap or stretch > max_edge_stretch
                   or ratio > max_density_ratio)
            if limit is not None:
                bad = bad or _stretch_ratio(uv[faces], p3[faces], area3[faces]) > limit
            if bad:
                print(f'UV_ATLAS revert chart {c}: {len(faces)} triangles, overlap {double:.3f}, '
                      f'flipped {flipped:.3f}, '
                      f'edge stretch {stretch:.1f}, density p95/p5 {ratio:.1f}')
                uv[faces] = corner[faces]
                # starting charts cut by the segment, so the reverted faces never join a chart outside the segment
                label[faces] = (label.max() + 1) + chart[faces]
                reverted += 1
                failed.append(faces)
        return failed

    if merged:
        uv = flatten(np.array([int(label[f]) in merged for f in range(n)]))
        failed = verify(uv, merged, max_stretch)
        if failed and cut_closed:
            # second try on whatever a closed piece could not do whole: its xatlas pieces under 8 triangles join their
            # neighbours only up to that size, so the patches stay open and flatten, and no fragments are left
            groups = set()
            for faces in failed:
                while True:
                    sizes = {c: int((label[faces] == c).sum()) for c in np.unique(label[faces])}
                    small = sorted((k, c) for c, k in sizes.items() if k < 8)
                    best = None
                    for _, c in small:
                        shared = defaultdict(float)
                        for f in faces[label[faces] == c]:
                            t = tri[f]
                            for k in range(3):
                                e = tuple(sorted((t[k], t[(k + 1) % 3])))
                                for g in edge_faces[e]:
                                    if label[g] != c and label[g] in sizes:
                                        shared[label[g]] += edge_len[e]
                        if shared:
                            best = (c, max(shared, key=lambda o: shared[o] / sizes[o]))
                            break
                    if best is None:
                        break
                    label[label == best[0]] = best[1]
                    groups.discard(int(best[0]))
                    groups.add(int(best[1]))
            normal_z = np.array([p.normal.z for p in me.polygons])
            for c in sorted(groups):
                found = _disc_cuts(np.nonzero(label == c)[0], tri, edge_faces, edge_len, normal_z)
                if found:
                    cuts |= found
            write(uv)
            uv = flatten(np.array([int(label[f]) in groups for f in range(n)]))
            verify(uv, groups, retry_stretch if retry_stretch is not None else max_stretch)
    else:
        uv = corner

    # ---- seam pass: merge across the most visible chart borders, cut tubes along their least visible path
    if vis is None:
        vis = _visibility(obj, tri, vis_objects)
    vis = np.asarray(vis, np.float64)
    seam_log = []
    if seam_rounds:
        uv = _seam_removal(obj, me, tri, p3, area3, edge_faces, edge_len, label, uv, cuts, vis, flatten, write,
                           seam_rounds, seam_stretch, seam_pairs, vis_floor, seam_min, max_overlap, max_edge_stretch,
                           max_density_ratio, seam_log)
    for e in me.edges:
        e.use_seam = False
    seams = _seam_metrics(uv, tri, pos, vis, edge_faces)

    # ---- one texel density (head denser), then pack
    head = np.zeros(n, bool)
    if head_groups:
        groups = {obj.vertex_groups[g].index for g in head_groups if g in obj.vertex_groups}
        weight = np.array([sum(g.weight for g in v.groups if g.group in groups) for v in me.vertices])
        head = weight[tri].mean(1) >= 0.5
    # group_factors {vertex group: density factor}: more density classes than the head (default off)
    factor_faces = []
    for name, value in (group_factors or {}).items():
        if name in obj.vertex_groups:
            gi = obj.vertex_groups[name].index
            weight = np.array([sum(g.weight for g in v.groups if g.group == gi) for v in me.vertices])
            factor_faces.append((weight[tri].mean(1) >= 0.5, value))
    area2 = np.abs(_signed(uv))
    for c in np.unique(label):
        faces = label == c
        a2, a3 = area2[faces].sum(), area3[faces].sum()
        if a2 <= 0 or a3 <= 0:
            continue
        s = np.sqrt(a3 / a2)
        if head_factor != 1.0 and area3[faces & head].sum() >= 0.5 * a3:
            s *= head_factor
        for chosen, value in factor_faces:
            if area3[faces & chosen].sum() >= 0.5 * a3:
                s *= value
        centre = uv[faces].reshape(-1, 2).mean(0)
        uv[faces] = centre + (uv[faces] - centre) * s
    packer_used = packer
    sparrow_k = None
    if packer == 'sparrow':
        try:
            packed, sparrow_k = _sparrow(uv, _islands(uv, tri), size, height_share, 2 * margin_px, sparrow_seconds,
                                         sparrow_runs, sparrow_fill)
            write(packed)
        except Exception as error:      # missing or failing sparrow: the xatlas packer below
            note = f'packer: sparrow failed ({str(error)[:300]}), fell back to the xatlas packer'
            print('UV_ATLAS FALLBACK ' + note, flush=True)
            fallbacks.append(note)
            packer_used = 'xatlas'
    if packer_used == 'xatlas':
        packed = _xatlas('pack', {'uv': uv.astype(np.float32), 'vert': tri}, '--size', size, '--padding',
                         margin_px, '--height-share', height_share, '--fine', fine, '--steps', steps)['uv']
        write(packed)
    elif packer_used != 'sparrow':
        write(uv / np.abs(uv).max())
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.context.scene.tool_settings.use_uv_select_sync = True
        bpy.ops.mesh.reveal()
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.pack_islands(udim_source='CLOSEST_UDIM', rotate=True, rotate_method='ANY', scale=True,
                                merge_overlap=False, margin_method='FRACTION', margin=margin_px / size,
                                shape_method='CONCAVE')
        bpy.ops.object.mode_set(mode='OBJECT')
        packed = read()
    use = float(np.abs(_signed(packed.astype(np.float64))).sum())
    if fallbacks:
        print('UV_ATLAS fallbacks: ' + ' | '.join(fallbacks), flush=True)
    return {'chart_mode': charts, 'charts_used': charts_used, 'xatlas_charts': int(chart.max() + 1),
            'start_charts': int(chart.max() + 1), 'charts': int(len(np.unique(label))),
            'merged': len(merged),
            'reverted': reverted, 'use': round(use, 4), 'margin_px': margin_px, 'size': size, 'max_cost': max_cost,
            'merge_below': merge_below, 'head_factor': head_factor, 'method': method, 'packer': packer,
            'packer_used': packer_used, 'sparrow_k': sparrow_k, 'fallbacks': fallbacks,
            'partuv_threshold': partuv_threshold if charts_used == 'partuv' else None, 'max_stretch': max_stretch,
            'seam_rounds': seam_rounds, 'seam_stretch': seam_stretch, 'seam_log': seam_log, 'seams': seams,
            'weld': weld_note, 'correct_aspect': correct_aspect}
