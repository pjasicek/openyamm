"""PartUV study copy of claude_shared/uv_atlas.py (2026-11-11) with one change: charts_npz=<path> starts from given
charts (per-face corner UVs `uv` M x 3 x 2 and `chart` M, e.g. partuv_run.py output) instead of xatlas charts; the
small-chart merge, SLIM re-flatten, checks, density and packing are unchanged. Original docstring:

Even, tightly packed UVs for a reduced creature mesh (TEXTURE_QUALITY_PASS.md), run inside Blender:

    sys.path.insert(0, '<repo>/level_generation/creatures/claude_shared'); import uv_atlas
    report = uv_atlas.unwrap(mesh_object, head_groups=('Head',), head_factor=1.8)

1. xatlas cuts and flattens charts (xatlas_charts.py in claude_shared/xatlas_venv). On a reduced Meshy body it
   still leaves a few hundred one- to seven-triangle charts at spikes, teeth and serrated edges; each costs a
   padding ring and Meshy paints each as a separate blotch.
2. Charts below `merge_below` triangles are merged into the neighbour they share the longest boundary with, and the
   merged charts are flattened again by Blender (`method`, SLIM minimum stretch by default). A merged chart that
   overlaps itself or flips triangles goes back to its xatlas pieces.
3. Every chart is scaled to one texel density (head charts `head_factor` times denser, linear: an island is head when
   at least half of its surface is weighted to `head_groups`).
4. xatlas packs them into one square `size` atlas with `margin_px` texels between islands, at the largest uniform
   scale that fits (brute force, rotation). `height_share` below 1 packs into the lower part of the square only
   (v 0..height_share), for a set with a strip painted by other means above it (Dragon King head set).
Option cut_closed=True (meshes of separate closed pieces, the Dagrell's bones): merged charts that are closed or have
several boundary loops are cut into discs first, so a small closed piece becomes one chart instead of its fragments;
one that still fails is retried as patches of at least 8 triangles. max_stretch sends charts whose p90 stretch is above
it down the same path (opened closed pieces flatten with long needles; the Dagrell's tail blade reached 6.8);
retry_stretch, if given, is the limit for those patches.
Options: packer='blender' packs with Blender's concave packer instead (44-51 % on the Magreeb, worse); charts='bones'
starts from one chart per dominant deform bone cut into discs on the underside instead of xatlas (experimental: spiky
segments collapse under SLIM and fall back to xatlas pieces; 50 % on the Magreeb).
Replaces every UV layer of the mesh with one 'UVMap'. The mesh must be triangulated (a reduced creature body always
is) and in its bind pose (armature at rest). Returns a report (charts before/after merging, reverted merges, use).
"""
import os
import subprocess
import tempfile
from collections import defaultdict

import bmesh
import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
VENV = os.path.join(HERE, '..', '..', 'claude_shared', 'xatlas_venv', 'bin', 'python')
TOOL = os.path.join(HERE, 'partuv_xatlas_charts.py')


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


def unwrap(obj, head_groups=(), head_factor=1.0, margin_px=2, size=2048, max_cost=2.0, roundness=0.5,
           merge_below=12, method='MINIMUM_STRETCH', max_overlap=0.003, max_edge_stretch=3.0, packer='xatlas',
           charts='xatlas', min_segment=24, max_density_ratio=2.5, height_share=1.0, cut_closed=False, fine=0, steps=10, max_stretch=None,
           retry_stretch=None, group_factors=None, charts_npz=None):
    me = obj.data
    if any(len(p.vertices) != 3 for p in me.polygons):
        raise ValueError(f'{obj.name} must be triangulated')
    n = len(me.polygons)
    pos = np.array([v.co for v in me.vertices], np.float64)
    tri = np.array([p.vertices[:] for p in me.polygons], np.int32)
    if charts_npz:
        given = np.load(charts_npz)
        res = {'uv': given['uv'], 'chart': np.unique(given['chart'], return_inverse=True)[1]}
        assert len(res['chart']) == n
    else:
        res = _xatlas('charts', {'positions': pos.astype(np.float32), 'triangles': tri},
                      '--max-cost', max_cost, '--roundness', roundness)
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

    # ---- xatlas UVs everywhere, merged charts re-flattened by Blender between seams at the chart boundaries
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
        bpy.ops.uv.unwrap(method=method, fill_holes=True, correct_aspect=True, margin=0.0)
        bpy.ops.mesh.reveal(select=False)
        bpy.ops.object.mode_set(mode='OBJECT')
        out = read()
        untouched = ~chosen & np.any(np.abs(out - before) > 1e-6, axis=(1, 2))
        assert not untouched.any(), f'unwrap changed {int(untouched.sum())} faces outside the merged charts'
        return out

    def verify(uv, groups, limit):
        """Sends bad charts back to their xatlas pieces; returns their faces."""
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
                # xatlas charts cut by the segment, so the reverted faces never join a chart outside the segment
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
    for e in me.edges:
        e.use_seam = False

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
    if packer == 'xatlas':
        packed = _xatlas('pack', {'uv': uv.astype(np.float32), 'vert': tri}, '--size', size, '--padding',
                         margin_px, '--height-share', height_share, '--fine', fine, '--steps', steps)['uv']
        write(packed)
    else:
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
    return {'chart_mode': charts, 'xatlas_charts': int(chart.max() + 1), 'charts': int(len(np.unique(label))),
            'merged': len(merged),
            'reverted': reverted, 'use': round(use, 4), 'margin_px': margin_px, 'size': size, 'max_cost': max_cost,
            'merge_below': merge_below, 'head_factor': head_factor, 'method': method, 'packer': packer}
