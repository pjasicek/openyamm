"""Step 2 (Blender): crown shells and card selection per LOD, from work/<id>/cards.npz. Works in glTF coordinates
(y up). Usage: blender --background --python shell.py -- <id>

Shell (per LOD 0..2): a metaball union of one element per clump (LOD2: per clump group) at `shell.scale[lod]` x the
clump radius (an isolated ball's surface; neighbouring clumps blend into one crown), axes stretched by the spread of
the clump's cards, meshed at `shell.resolution` m, decimated to `shell.tris[lod]`, outward winding, smooth normals.
Cards: a card goes when its centre and its corners pulled `cards.inside_shrink[lod]` toward the centre all lie
inside the shell, or when none of those points sees out past the shell along any of 96 view directions (16 azimuths
x elevations -50..75 degrees). The rest are ranked by exposure (mean over the directions of the transmittance past the
shell and the other kept cards, each card hit passing 45 %); `cards.keep[lod]` of them stay, most exposed first.
Shell colour: per vertex the mean seen colour of the dropped cards near it (Gaussian, sigma = the median clump
radius) x a sky term (1 - ao + ao x visibility / mean visibility; visibility = cosine-weighted
upper-hemisphere rays through the kept cards) x a per-vertex value jitter (`shell.jitter`). Shading normals lean up
(`shell.normal_out` of the outward normal), so the sun does not paint one smooth lit side on the shell.
Writes work/<id>/shell.npz: l<lod>_verts, _faces, _normals, _colours, _keep (bool per card), _reason."""
import bpy, bmesh, json, math, os, sys
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common, surface_nets

tid = sys.argv[sys.argv.index('--') + 1]
spec = common.load(tid); W = spec['work']; S = spec['shell']; C = spec['cards']
d = np.load(os.path.join(W, 'cards.npz'))
rng = np.random.default_rng(7)


def per_lod(v, lod):
    return v[lod] if isinstance(v, (list, tuple)) else v


def view_dirs():
    out = []
    for el in (-50, -25, 0, 25, 50, 75):
        for az in range(16):
            a = 2 * math.pi * (az + 0.5 * (el % 50 == 0)) / 16; e = math.radians(el)
            out.append(Vector((math.cos(e) * math.cos(a), math.sin(e), math.cos(e) * math.sin(a))))
    return out


VIEW = view_dirs()
sky = rng.normal(0, 1, (4096, 3)); sky /= np.linalg.norm(sky, axis=1, keepdims=True)
sky = sky[sky[:, 1] > 0.05][:64]


def far_root(o, u, cen, semi):
    """Farthest distance from o along unit u inside the union of the ellipsoids (cen, semi axes); 0 if none."""
    oo = (o - cen) / semi; dd = u / semi
    qa = (dd * dd).sum(1); qb = 2 * (oo * dd).sum(1); qc = (oo * oo).sum(1) - 1
    disc = qb * qb - 4 * qa * qc
    t = np.where(disc >= 0, (-qb + np.sqrt(np.maximum(disc, 0))) / (2 * qa), 0.0)
    return float(max(t.max(), 0.0))


def star_shell(cen, semi, lod):
    """Star-shaped shell around the crown centre (MM8 broadleaf method): a sphere grid (`shell.grid[lod]` =
    [segments, rings], poles up and down), each vertex at the far crossing of the shrunken clump union along its
    direction, capped at (1 - `shell.inset` - `shell.inset_down` x the downward part of the direction) x the card envelope
    there (85th percentile of the card corners' distance within 25 degrees), then smoothed (`shell.smooth` passes)."""
    segments, rings = per_lod(S['grid'], lod)
    corners = d[f'c{lod}_corners'].reshape(-1, 3)
    centre = np.array([0.0, float(np.average(cen[:, 1], weights=semi.mean(1) ** 2)), 0.0])
    if S.get('centre_y') is not None:
        centre[1] = S['centre_y']
    rel = corners - centre; dist = np.linalg.norm(rel, axis=1); dirs = rel / dist[:, None]
    inset = per_lod(S.get('inset', 0.12), lod)
    cos_lim = math.cos(math.radians(25))

    inset_down = per_lod(S.get('inset_down', 0.25), lod)

    def radius(u):
        r = far_root(centre, u, cen, semi)
        near = dirs @ u > cos_lim
        if near.sum() >= 8:     # deeper below the crown centre: seen from under the tree the cards stay in front
            r = min(r, (1 - inset - inset_down * max(0.0, -u[1])) * float(np.percentile(dist[near], 85)))
        return r

    grid_u = []; radii_ = []
    for i in range(1, rings):
        el = math.pi / 2 - math.pi * i / rings
        row_u = []; row_r = []
        for j in range(segments):
            az = 2 * math.pi * (j + 0.5 * (i % 2)) / segments
            u = np.array([math.cos(el) * math.cos(az), math.sin(el), math.cos(el) * math.sin(az)])
            row_u.append(u); row_r.append(radius(u))
        grid_u.append(row_u); radii_.append(row_r)
    top = radius(np.array([0.0, 1.0, 0.0])); bottom = radius(np.array([0.0, -1.0, 0.0]))
    rad = np.array(radii_)
    filled = rad[rad > 0]
    floor_r = float(np.percentile(filled, 10)) if len(filled) else 0.3
    rad = np.where(rad > 0, rad, 0.6 * floor_r)
    for _ in range(S.get('smooth', 1)):
        sm = rad.copy()
        for i in range(rad.shape[0]):
            for j in range(segments):
                nb = [rad[i, (j - 1) % segments], rad[i, (j + 1) % segments]]
                if i > 0: nb.append(rad[i - 1, j])
                if i < rad.shape[0] - 1: nb.append(rad[i + 1, j])
                sm[i, j] = 0.5 * rad[i, j] + 0.5 * float(np.mean(nb))
        rad = sm
    top = top or float(rad[0].mean()); bottom = bottom or float(rad[-1].mean())
    verts = [centre + np.array([0, top, 0]), centre - np.array([0, bottom, 0])]
    rows = []
    for i in range(len(grid_u)):
        rows.append([]);
        for j in range(segments):
            verts.append(centre + grid_u[i][j] * rad[i, j]); rows[-1].append(len(verts) - 1)
    faces = []
    for j in range(segments):
        faces.append((0, rows[0][(j + 1) % segments], rows[0][j]))
        faces.append((1, rows[-1][j], rows[-1][(j + 1) % segments]))
    for i in range(len(rows) - 1):
        for j in range(segments):
            a_, b_ = rows[i][j], rows[i][(j + 1) % segments]
            c_, d_ = rows[i + 1][(j + 1) % segments], rows[i + 1][j]
            faces.append((a_, d_, c_)); faces.append((a_, c_, b_))
    bm = bmesh.new()
    bv = [bm.verts.new(tuple(v)) for v in verts]
    for f in faces:
        bm.faces.new([bv[i] for i in f])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.verts.ensure_lookup_table(); bm.normal_update()
    out_v = np.array([v.co[:] for v in bm.verts]); out_f = np.array([[v.index for v in f.verts] for f in bm.faces])
    out_n = np.array([v.normal[:] for v in bm.verts])
    bm.free()
    return out_v, out_f, out_n


def build_shell(lod):
    if lod == 2:
        centres, radii = d['group_centre'], d['group_radius']
        members = json.loads(str(d['group_members']))
        axes = np.array([d['clump_axes'][m].mean(0) for m in members])
        inner = np.array([all(d['clump_inner'][k] for k in m) for m in members])
    else:
        centres, radii, axes, inner = d['clump_centre'], d['clump_radius'], d['clump_axes'], d['clump_inner']
    scale = per_lod(S['scale'], lod)
    keep_el = ~inner if S['skip_inner'] else np.ones(len(centres), bool)
    ax = np.clip(axes, 0.6, 1.6) ** S.get('axis_power', 0.5)
    semi = (scale * radii[:, None] * ax)[keep_el]; cen = centres[keep_el]
    if S.get('mode', 'star') == 'star':
        return star_shell(cen, semi, lod)
    step = S['resolution']; k = S.get('blend', 0.1)
    lo = (cen - semi).min(0) - 3 * step; hi = (cen + semi).max(0) + 3 * step
    n = np.ceil((hi - lo) / step).astype(int) + 1
    gx, gy, gz = (lo[i] + step * np.arange(n[i]) for i in range(3))
    P = np.stack(np.meshgrid(gx, gy, gz, indexing='ij'), -1).reshape(-1, 3)
    acc = np.zeros(len(P))
    for c, a_ in zip(cen, semi):          # smooth union of the ellipsoids (signed distance approx., metres)
        q = np.linalg.norm((P - c) / a_, axis=1)
        dist = (q - 1.0) * a_.mean()
        acc += np.exp(-np.clip(dist, -5 * k, 50 * k) / k)
    field = (-k * np.log(np.maximum(acc, 1e-30))).reshape(tuple(n))
    vs, qs = surface_nets.mesh(field, lo, step)
    me = bpy.data.meshes.new(f'shell{lod}_raw')
    me.from_pydata([tuple(v) for v in vs], [], [tuple(int(i) for i in q) for q in qs])
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    for _ in range(S.get('smooth', 3)):
        bmesh.ops.smooth_vert(bm, verts=bm.verts[:], factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
    bm.to_mesh(me); bm.free()
    obj = bpy.data.objects.new(f'shell{lod}', me); bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    target = per_lod(S['tris'], lod)
    tris = sum(len(p.vertices) - 2 for p in me.polygons)
    mod = obj.modifiers.new('dec', 'DECIMATE'); mod.decimate_type = 'COLLAPSE'; mod.ratio = min(1.0, target / tris)
    mod.use_collapse_triangulate = True
    dg = bpy.context.evaluated_depsgraph_get()
    me2 = bpy.data.meshes.new_from_object(obj.evaluated_get(dg))
    bm = bmesh.new(); bm.from_mesh(me2)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.verts.ensure_lookup_table()
    verts = np.array([v.co[:] for v in bm.verts]); faces = np.array([[v.index for v in f.verts] for f in bm.faces])
    normals = np.array([v.normal[:] for v in bm.verts])
    bm.free()
    return verts, faces, normals


def card_points(corners, shrink):
    c = corners.mean(0)
    return [c] + [c + (q - c) * shrink for q in corners]


def inside(bvh, p):
    loc, nrm, _, dist = bvh.find_nearest(Vector(p))
    return loc is not None and (Vector(p) - loc).dot(nrm) < 0


out = {}
for lod in (0, 1, 2):
    verts, faces, normals = build_shell(lod)
    sbvh = BVHTree.FromPolygons([tuple(v) for v in verts], [tuple(int(i) for i in f) for f in faces])
    corners = d[f'c{lod}_corners']; colour = d[f'c{lod}_colour']; n = len(corners)
    shrink = per_lod(C['inside_shrink'], lod)
    reason = np.zeros(n, np.int8)          # 0 kept, 1 inside the shell, 2 hidden by it, 3 thinned
    far = 50.0
    for k in range(n):
        pts = card_points(corners[k], shrink)
        if all(inside(sbvh, p) for p in pts):
            reason[k] = 1; continue
        seen = False
        for p in pts:
            if inside(sbvh, p):
                continue
            o = Vector(p)
            for dv in VIEW:
                if sbvh.ray_cast(o + dv * 0.005, dv, far)[0] is None:
                    seen = True; break
            if seen:
                break
        if not seen:
            reason[k] = 2
    alive = np.where(reason == 0)[0]
    keep_frac = per_lod(C['keep'], lod)
    if keep_frac < 1.0 and len(alive):
        tv, ti = [], []
        for j, k in enumerate(alive):
            q = corners[k]; b = len(tv)
            tv += [tuple(x) for x in q]; ti += [(b, b + 1, b + 2), (b, b + 2, b + 3)]
        cbvh = BVHTree.FromPolygons(tv, ti)
        expo = np.zeros(len(alive))
        for j, k in enumerate(alive):
            o0 = Vector(corners[k].mean(0)); tot = 0.0
            for dv in VIEW:
                o = o0 + dv * 0.005
                if sbvh.ray_cast(o, dv, far)[0] is not None:
                    continue
                t = 1.0
                for _ in range(8):
                    loc, _, idx, _ = cbvh.ray_cast(o, dv, far)
                    if loc is None:
                        break
                    if idx // 2 != j:
                        t *= 0.45
                        if t < 0.02:
                            break
                    o = loc + dv * 0.005
                tot += t
            expo[j] = tot / len(VIEW)
        owner = d[f'c{lod}_clump'][alive]
        carry = 0.0
        for ci in np.unique(owner):          # per clump: the density stays even over the crown
            sel = np.where(owner == ci)[0]
            carry += keep_frac * len(sel)     # fractions carried over between clumps (LOD2 has 4 cards each)
            nkeep = max(1, int(carry)); carry -= nkeep
            order = sel[np.argsort(-expo[sel])]
            reason[alive[order[nkeep:]]] = 3
    keep = reason == 0
    # card BVH of the kept cards: sky visibility of the shell vertices
    tv, ti = [], []
    for k in np.where(keep)[0]:
        q = corners[k]; b = len(tv)
        tv += [tuple(x) for x in q]; ti += [(b, b + 1, b + 2), (b, b + 2, b + 3)]
    kbvh = BVHTree.FromPolygons(tv, ti) if tv else None
    vis = np.zeros(len(verts))
    for i, (p, nn) in enumerate(zip(verts, normals)):
        tot = 0.0; wsum = 0.0
        for s in sky:
            w = max(0.0, float(np.dot(s, nn))) + 0.15
            dv = Vector(s); o = Vector(p) + Vector(nn) * 0.01 + dv * 0.005
            if sbvh.ray_cast(o, dv, far)[0] is not None:
                wsum += w; continue
            t = 1.0
            if kbvh is not None:
                for _ in range(10):
                    loc, _, _, _ = kbvh.ray_cast(o, dv, far)
                    if loc is None:
                        break
                    t *= 0.45
                    if t < 0.02:
                        break
                    o = loc + dv * 0.005
            tot += w * t; wsum += w
        vis[i] = tot / wsum
    dropped = ~keep
    src = dropped if dropped.sum() >= 20 else np.ones(n, bool)
    cc = corners[src].mean(1); cl = colour[src]
    sigma = float(np.median(d['clump_radius']))
    dist2 = ((verts[:, None, :] - cc[None]) ** 2).sum(-1)
    wgt = np.exp(-dist2 / (2 * sigma ** 2)) + 1e-9
    base = (wgt[..., None] * cl[None]).sum(1) / wgt.sum(1)[:, None]
    ao = per_lod(S['ao'], lod)
    term = 1 - ao + ao * vis / max(vis.mean(), 1e-6)
    jit = S.get('jitter', 0.25)                      # per-vertex value mottling, so a gap never shows a smooth wash
    term *= 1 + jit * rng.uniform(-1, 1, len(verts))
    col = base * term[:, None]                     # x shell.value in compose.py (tune.py fits it)
    # shading normals: mostly up, a little outward (the sun would otherwise paint one smooth lit side on the shell;
    # the leaf cards' own shading normals are broken up per clump)
    w = per_lod(S.get('normal_out', 0.35), lod)
    if per_lod(S.get('dark_under', False), lod):
        lean = (1 - w) * np.clip(0.5 + 0.5 * normals[:, 1:2], 0, 1)    # the underside keeps its downward normals
    else:
        # seen from under the tree the leaves are lit (translucent, two-sided): the underside's normals turn up
        # (no downward component), so it never reads as a black heart
        normals = normals.copy(); normals[:, 1] = np.maximum(normals[:, 1], S.get('under_up', 0.3))
        normals /= np.linalg.norm(normals, axis=1, keepdims=True)
        lean = 1 - w
    normals = normals * w + np.array([0.0, 1.0, 0.0]) * lean
    normals /= np.linalg.norm(normals, axis=1, keepdims=True)
    out.update({f'l{lod}_verts': verts, f'l{lod}_faces': faces, f'l{lod}_normals': normals,
                f'l{lod}_colours': col, f'l{lod}_keep': keep, f'l{lod}_reason': reason})
    print(f'SHELL LOD{lod} tris {len(faces)} cards {n} -> {int(keep.sum())} (inside {int((reason == 1).sum())}, '
          f'hidden {int((reason == 2).sum())}, thinned {int((reason == 3).sum())}); shell colour mean '
          f'{col.mean(0).round(4).tolist()} vis {vis.mean():.2f}')
np.savez(os.path.join(W, 'shell.npz'), **out)
