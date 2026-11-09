"""Head horns and frill spikes rebuilt as smooth round horns (user 2026-10-14: "re-do the bones from his head like
the horns ... so that they have proper shape (check the restored x2 master)"). The reduced candidate's head ivory
regions (work/ivory_faces.npz, faces sampled ivory in the installed texture) are split into single spikes by a
persistence watershed on the geodesic distance from the region's skin border: each local maximum is a tip. Per spike,
the faces above a low cut are deleted and a new tube is stitched to the hole's rim (no hidden holes, no floating
pieces): rings follow a quadratic Bezier fitted to the old spike's medial line, round, tapering to a sharp tip. The
main horns get the reference's sweep (concave up, a slight inward crescent at the tip). Tubes are rigid on the bone
that dominates their rim.
Face attribute `part`: 0 skin, 1 rebuilt horn/spike (ivory), 2 crest spike (gold), 3 teeth, 4 eyes, 5 tongue,
6 other ivory (claws, wing spurs), 7 dorsal spines. In: work/ladder.blend (REA_CAND, default Cand_55),
work/ivory_faces.npz. Out: work/horns_master.blend (object Body + Rig), work/horns.json."""
import heapq
import json
import math
import os

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAND = os.environ.get('REA_CAND', 'Cand_55')
CUT = 0.002            # m: spike faces whose lowest vertex is above this geodesic height are replaced
PERSIST = 0.004        # m: a tip whose peak rises less than this above its saddle merges into its neighbour
MIN_TIP = 0.008        # m: shorter bumps are not spikes
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'ladder.blend'))
src = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']; o = bpy.data.objects[CAND]
rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
g = o.vertex_groups.get('ReduceProtect')
if g:
    o.vertex_groups.remove(g)
region = np.load(os.path.join(HERE, 'work', 'ivory_faces.npz'))['region']
me = o.data
mats = [m.name for m in me.materials]
HEAD_MAT = mats.index('DragonHead_A')

bm = bmesh.new(); bm.from_mesh(me)
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
deform = bm.verts.layers.deform.verify()
part_layer = bm.faces.layers.int.new('part')        # before holding any references: a new layer invalidates them
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
gnames = [x.name for x in o.vertex_groups]

# --- piece classes (separate connected pieces) -------------------------------------------------------------------
comp = np.full(len(bm.verts), -1); n = 0
for v in bm.verts:
    if comp[v.index] >= 0:
        continue
    stack = [v]; comp[v.index] = n
    while stack:
        x = stack.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if comp[y.index] < 0:
                comp[y.index] = n; stack.append(y)
    n += 1
fpiece = np.array([comp[f.verts[0].index] for f in bm.faces])
main = np.bincount(fpiece).argmax()
part = np.zeros(len(bm.faces), np.int32)
for p in range(n):
    sel = np.flatnonzero(fpiece == p)
    if p == main:
        continue
    mat = np.bincount([bm.faces[i].material_index for i in sel]).argmax()
    if mat != HEAD_MAT:
        part[sel] = 7                                   # gold dorsal spines on the body
    elif len(sel) <= 12:
        part[sel] = 3                                   # teeth
    elif len(sel) > 110:
        part[sel] = 5                                   # tongue
    else:
        part[sel] = 4                                   # eyes
fc = np.array([f.calc_center_median()[:] for f in bm.faces])
ids = sorted(set(region.tolist()) - {-1})
head_regions = []
for r in ids:
    sel = region == r
    c = fc[sel]
    if sel.sum() >= 5 and c[:, 1].mean() < -1.1 and c[:, 2].mean() > .8:
        head_regions.append(r)
    else:
        part[sel] = 6                                   # claws, wing spurs: kept, painted ivory
print('HEAD REGIONS', head_regions)


def dominant_bone(verts):
    acc = {}
    for v in verts:
        for gi, w in v[deform].items():
            acc[gi] = acc.get(gi, 0) + w
    return max(acc, key=acc.get)


def bezier(p0, p1, p2, t):
    return (1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t * t * p2


def bezier_d(p0, p1, p2, t):
    return 2 * (1 - t) * (p1 - p0) + 2 * t * (p2 - p1)


spikes = []
for r in head_regions:
    rf = [bm.faces[i] for i in np.flatnonzero(region == r)]
    rset = set(rf)
    rv = {v for f in rf for v in f.verts}
    border = {v for v in rv if any(f not in rset for f in v.link_faces)}
    # geodesic height above the skin border, inside the region
    dist = {v: (0.0 if v in border else math.inf) for v in rv}
    heap = [(0.0, v.index, v) for v in border]
    while heap:
        d, _, v = heapq.heappop(heap)
        if d > dist[v]:
            continue
        for e in v.link_edges:
            y = e.other_vert(v)
            if y in rv:
                nd = d + e.calc_length()
                if nd < dist[y]:
                    dist[y] = nd; heapq.heappush(heap, (nd, y.index, y))
    # persistence watershed (descending height); basin id = its peak vertex
    order = sorted(rv, key=lambda v: -dist[v])
    parent, peak, basin = {}, {}, {}

    def find(x):
        while parent[x] is not x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for v in order:
        roots = {find(basin[y]) for e in v.link_edges for y in [e.other_vert(v)] if y in basin}
        if not roots:
            parent[v] = v; peak[v] = dist[v]; basin[v] = v
            continue
        roots = sorted(roots, key=lambda x: -peak[x])
        top = roots[0]; basin[v] = top
        for other in roots[1:]:
            if peak[other] - dist[v] < PERSIST:
                parent[other] = top
    tips = {}
    for v in rv:
        tips.setdefault(find(basin[v]), []).append(v)
    region_spikes = []
    for root, verts in tips.items():
        h = peak[root]
        if h < MIN_TIP:
            continue
        band = [v for v in verts if dist[v] <= .2 * h] or verts
        co = np.array([v.co[:] for v in verts]); d = np.array([dist[v] for v in verts])
        bands = [co[(d >= a) & (d < b)].mean(0) for a, b in zip(np.linspace(0, h, 9)[:-1], np.linspace(0, h, 9)[1:])
                 if ((d >= a) & (d < b)).any()]
        region_spikes.append({'tip': Vector(root.co), 'height': h, 'band': Vector(np.mean([v.co[:] for v in band], 0)),
                              'bands': bands, 'band_verts': [Vector(v.co) for v in verts if .1 * h <= dist[v] <= .3 * h]})
    print('REGION', r, 'faces', len(rf), 'tips', sorted(round(peak[x] * 1000, 1) for x in tips),
          'kept', len(region_spikes))
    spikes.append({'region': r, 'faces': rf, 'verts': rv, 'spikes': region_spikes,
                   'material': int(np.bincount([f.material_index for f in rf]).argmax()),
                   'bone': dominant_bone(list(border))})

# left/right symmetry: a -x region takes the mirrored spikes and bone of its +x partner
M = Vector((-1, 1, 1))
centre = {R['region']: sum((f.calc_center_median() for f in R['faces']), Vector()) / len(R['faces']) for R in spikes}
for R in spikes:
    cr = centre[R['region']]
    if cr.x > -.012:
        continue
    partner = min((P for P in spikes if centre[P['region']].x > .012),
                  key=lambda P: (centre[P['region']] * M - cr).length)
    if (centre[partner['region']] * M - cr).length > .03:
        continue
    mir = lambda v: Vector((-v.x, v.y, v.z))
    R['spikes'] = [{'tip': mir(S['tip']), 'height': S['height'], 'band': mir(S['band']),
                    'bands': [np.array([-b[0], b[1], b[2]]) for b in S['bands']],
                    'band_verts': [mir(x) for x in S['band_verts']]} for S in partner['spikes']]
    R['bone'] = partner['bone']; R['mirror_of'] = partner['region']
    print('MIRROR', R['region'], '<-', partner['region'])

# --- rebuild: remove each head ivory region, cap the hole with a fitted skin patch, set closed horns into it ----------
for f in bm.faces:
    f[part_layer] = int(part[f.index])
report = []


def new_vert(co, weights):
    v = bm.verts.new(co)
    for gi, w in weights.items():
        v[deform][gi] = w
    return v


smooth_set = set()
spike_verts = {v for R in spikes for v in R['verts']} - {v for R in spikes for v in R['verts']
                                                         if any(f not in set(R['faces']) for f in v.link_faces)}
for R in spikes:
    print('BUILD', R['region'], 'valid verts', sum(v.is_valid for v in R['verts']), 'of', len(R['verts']), flush=True)
    # every face whose three vertices are region vertices goes too: no pinched (bowtie) rims
    rset = {f for v in R['verts'] if v.is_valid for f in v.link_faces if all(x in R['verts'] for x in f.verts)}
    rset |= {f for f in R['faces'] if f.is_valid}
    outside = {f for v in R['verts'] if v.is_valid for f in v.link_faces if f not in rset}
    n_out = sum((f.normal for f in outside), Vector()).normalized()
    old_tris = sum(len(f.verts) - 2 for f in rset)
    del_edges = {e for f in rset for e in f.edges}
    bmesh.ops.delete(bm, geom=list(rset), context='FACES')
    # rim cycles, directed against the surviving neighbour faces' winding; a pinched rim splits into closed cycles
    out = {}
    for e in del_edges:
        if not e.is_valid or not e.is_boundary:
            continue
        f = e.link_faces[0]
        l = next(l for l in f.loops if l.edge is e)
        out.setdefault(l.link_loop_next.vert, []).append(l.vert)
    loops = []
    while any(out.values()):
        st = next(v for v, lst in out.items() if lst)
        path = [st]
        while True:
            cur = path[-1]
            if not out.get(cur):
                raise AssertionError(f'open rim chain at region {R["region"]}')
            nxt = out[cur].pop()
            if nxt in path:
                i = path.index(nxt)
                loops.append(path[i:]); path = path[:i + 1]
                if len(path) == 1 and not out.get(path[0]):
                    break
                if nxt is st and len(path) == 1:
                    break
                continue
            path.append(nxt)
    loops = [lp for lp in loops if len(lp) >= 3]
    print('LOOPS', R['region'], [len(lp) for lp in loops], flush=True)
    loops.sort(key=len, reverse=True)
    rim = loops[0]
    c = sum((x.co for x in rim), Vector()) / len(rim)
    # local frame and a quadratic height field fitted to the surrounding skin and the rim
    nz = n_out; ux = (rim[0].co - c); ux = (ux - nz * ux.dot(nz)).normalized(); wy = nz.cross(ux)
    rad = max((x.co - c).length for x in rim)
    # the surrounding skin: three edge rings out from the rim (a ball also caught the far side of the neck)
    near, front = set(rim), set(rim)
    for _ in range(3):
        front = {e.other_vert(x) for x in front for e in x.link_edges} - near
        front = {v for v in front if v.link_faces and v not in spike_verts and all(f[part_layer] == 0 for f in v.link_faces)}
        near |= front
    near = list(near)
    P = np.array([[(v.co - c).dot(ux), (v.co - c).dot(wy), (v.co - c).dot(nz)] for v in near])
    A = np.stack([np.ones(len(P)), P[:, 0], P[:, 1], P[:, 0] ** 2, P[:, 0] * P[:, 1], P[:, 1] ** 2], 1)
    keep = np.ones(len(P), bool)
    for _ in range(4):                                       # robust: the old horn sheath sits above the head
        coef = np.linalg.lstsq(A[keep], P[keep, 2], rcond=None)[0]
        keep = (P[:, 2] - A @ coef) < .004
    big = any(S['height'] > .12 for S in R['spikes']) or abs(c.x) < .012
    near_other = {y for P in spikes if P is not R for v in P['verts'] if v.is_valid
                  for e in v.link_edges for y in e.verts}
    if True:
        # flatten the old sheath (skin that stood out of the head around the horn base) onto the fitted head
        flat = 0
        for v, (px, py, pz) in zip(near, P):
            fit = float(coef @ [1, px, py, px * px, px * py, py * py])
            if pz - fit > .003 and math.hypot(px, py) < 1.25 * rad and v not in near_other:
                v.co = c + ux * px + wy * py + nz * (fit + .003); flat += 1; smooth_set.add(v)
        print('FLATTEN', R['region'], flat, flush=True)

    def surf(x, y):
        return c + ux * x + wy * y + nz * float(coef @ [1, x, y, x * x, x * y, y * y])
    # rim orientation: counter-clockwise around +nz (outward faces)
    ang = [math.atan2((x.co - c).dot(wy), (x.co - c).dot(ux)) for x in rim]
    turn = sum(((b - a + math.pi) % math.tau - math.pi) for a, b in zip(ang, ang[1:] + ang[:1]))
    wavg = {}
    for x in rim:
        for gi, w in x[deform].items():
            wavg[gi] = wavg.get(gi, 0) + w / len(rim)
    rim_mean = float(np.mean([(x.co - c).length for x in rim]))
    rings = [rim]
    for frac in (.66, .33):
        ring = []
        for x in rim:
            q = x.co - c; px, py = q.dot(ux) * frac, q.dot(wy) * frac
            ring.append(new_vert(surf(px, py), wavg))
        rings.append(ring)
    centre = new_vert(surf(0, 0), wavg)
    smooth_set.update(rim); smooth_set.update(x for r_ in rings[1:] for x in r_); smooth_set.add(centre)
    cap = []
    for ra_, rb_ in zip(rings, rings[1:]):
        k = len(ra_)
        for i in range(k):
            cap.append(bm.faces.new((ra_[i], ra_[(i + 1) % k], rb_[(i + 1) % k], rb_[i])))
    last = rings[-1]
    for i in range(len(last)):
        cap.append(bm.faces.new((last[i], last[(i + 1) % len(last)], centre)))
    for f in cap:
        f.material_index = R['material']; f[part_layer] = 0; f.smooth = True
    for extra in loops[1:]:
        if len(extra) >= 3:
            cc = new_vert(sum((x.co for x in extra), Vector()) / len(extra), dict(extra[0][deform].items()))
            for a, b in zip(extra, extra[1:] + extra[:1]):
                f = bm.faces.new((a, b, cc)); f.material_index = R['material']; f[part_layer] = 0; f.smooth = True
    bmesh.ops.recalc_face_normals(bm, faces=cap)
    if sum((f.normal for f in cap), Vector()).dot(nz) < 0:
        bmesh.ops.reverse_faces(bm, faces=cap)
    cap_tris = sum(len(f.verts) - 2 for f in cap)
    # closed horns, roots sunk below the cap
    bone = R['bone']
    for S in R['spikes']:
        tip = S['tip']; h = S['height']
        b = S['band'] - c; base = surf(b.dot(ux), b.dot(wy))
        chord = (tip - base).normalized(); length = (tip - base).length
        pts = [np.array(base)] + [np.array(x) for x in S['bands'][1:]] + [np.array(tip)]
        cl = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]); tt = cl / cl[-1]
        P0, P2 = np.array(base), np.array(tip); Bw = 2 * tt * (1 - tt)
        rhs = np.array(pts) - ((1 - tt) ** 2)[:, None] * P0 - (tt ** 2)[:, None] * P2
        p1 = Vector((Bw[:, None] * rhs).sum(0) / max((Bw ** 2).sum(), 1e-9))
        mid = (base + tip) / 2; bow = p1 - mid
        if bow.length > .3 * length:                         # few medial bands can throw the fit far off
            p1 = mid + bow.normalized() * .3 * length
        crest = abs(base.x) < .012
        is_main = length > .12 and not crest
        if is_main:
            up = (Vector((0, 0, 1)) - chord * chord.z).normalized()
            out = Vector((1 if base.x > 0 else -1, 0, 0)); out = (out - chord * chord.dot(out)).normalized()
            p1 = (base + tip) / 2 - up * .16 * length + out * .07 * length
        # root radius from the old spike's lower band, round
        bv = S['band_verts'] or [S['band']]
        r_band = np.mean([((x - base) - chord * (x - base).dot(chord)).length for x in bv])
        r_root = float(np.clip(r_band, .004, .02 if is_main else .009))
        r_root = min(r_root, max(.004, .8 * rim_mean))           # a root wider than its patch cuts the skin
        if crest:
            r_root = min(r_root, .006)
        sides, nring, power = (10, 10, .8) if is_main else ((6, 6, 1.0) if crest else (7, 5, 1.0))
        p0 = base - nz * r_root * 1.2                        # root sunk under the cap, along the surface normal
        tan = bezier_d(p0, p1, tip, 0).normalized()
        nrm = tan.orthogonal().normalized(); prev = tan; rv_ = []
        for k in range(nring):
            t = k / nring
            cc = bezier(p0, p1, tip, t); tg = bezier_d(p0, p1, tip, t).normalized()
            ax = prev.cross(tg)
            if ax.length > 1e-9:
                nrm.rotate(Matrix.Rotation(prev.angle(tg), 3, ax.normalized()))
            prev = tg; bi = tg.cross(nrm).normalized(); nrm = bi.cross(tg).normalized()
            rr = r_root * (1 - t * .97) ** power
            rv_.append([new_vert(cc + rr * (math.cos(a) * nrm + math.sin(a) * bi), {bone: 1.0})
                        for a in (j * math.tau / sides for j in range(sides))])
        apex = new_vert(tip, {bone: 1.0}); bottom = new_vert(p0 - tan * r_root * .2, {bone: 1.0})
        hf = []
        for ra_, rb_ in zip(rv_, rv_[1:]):
            for j in range(sides):
                hf.append(bm.faces.new((ra_[j], ra_[(j + 1) % sides], rb_[(j + 1) % sides], rb_[j])))
        for j in range(sides):
            hf.append(bm.faces.new((rv_[-1][j], rv_[-1][(j + 1) % sides], apex)))
            hf.append(bm.faces.new((rv_[0][(j + 1) % sides], rv_[0][j], bottom)))
        bmesh.ops.recalc_face_normals(bm, faces=hf)
        for f in hf:
            f.material_index = R['material']; f[part_layer] = 2 if crest else 1; f.smooth = True
        report.append({'region': int(R['region']), 'kind': 'main horn' if is_main else ('crest' if crest else 'spike'),
                       'bone': gnames[bone], 'height_mm': round(h * 1000, 1), 'length_mm': round(length * 1000, 1),
                       'root_radius_mm': round(r_root * 1000, 1), 'bow_mm': round(((p1 - (base + tip) / 2).length) * 1000, 1),
                       'tris': sum(len(f.verts) - 2 for f in hf), 'base': list(base), 'tip': list(tip)})
    report.append({'region': int(R['region']), 'kind': 'cap', 'removed_tris': old_tris, 'cap_tris': cap_tris,
                   'rim_vertices': len(rim), 'extra_loops': len(loops) - 1})
# light Laplacian smoothing of the patched and flattened skin (horn tubes are separate pieces, untouched)
for _ in range(3):
    pos = {}
    for v in smooth_set:
        nb = [e.other_vert(v).co for e in v.link_edges]
        pos[v] = v.co * .5 + sum(nb, Vector()) / len(nb) * .5
    for v, p_ in pos.items():
        v.co = p_
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
bm.to_mesh(me); bm.free(); me.update()
assert all(v.groups for v in me.vertices), 'unweighted vertex'
bpy.data.objects.remove(src, do_unlink=True)
for x in list(bpy.data.objects):
    if x.name.startswith('Cand_') and x is not o:
        bpy.data.objects.remove(x, do_unlink=True)
o.name = 'Body'; o.hide_render = False
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'horns_master.blend'))
json.dump({'triangles': len(me.polygons), 'spikes': report}, open(os.path.join(HERE, 'work', 'horns.json'), 'w'), indent=1)
print('HORNS triangles', len(me.polygons), 'caps', sum(x.get('cap_tris', 0) for x in report), 'horns', sum(x.get('tris', 0) for x in report), 'removed', sum(x.get('removed_tris', 0) for x in report))
for x in report:
    print(' ', {k: v for k, v in x.items() if k not in ('base', 'tip')})
