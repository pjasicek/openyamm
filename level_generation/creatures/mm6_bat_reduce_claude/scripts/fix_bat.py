"""Bat repairs on the 40 % candidate (user 2026-10-14: "fix the holes here ... fix the teeth ... and retexture",
"yeah the fangs fix aswell" = the foot claws). Adapted from mm6_cdr1_reduce_claude/scripts/build_horns.py:
- claws: the ivory regions of the front and rear feet (work/ivory_faces.npz, faces sampled ivory in the installed
  texture) are split into single claws by a persistence watershed on the geodesic height above the region border; each
  region is removed, its hole capped with a fitted skin patch, and closed round curved tubes set into the patch,
  rigid on the bone that dominates the rim;
- teeth: the four 4-triangle fang slivers are replaced by clean 6-sided cones on Head (the bat has no jaw bone),
  upper fangs hanging, lower rising, roots sunk into the gum;
- holes: the hole by the left wing root and at the tail tip are fanned shut; the rectangular notch in the left
  membrane's trailing edge is filled.
Face attribute `part`: 0 body, 1 claw, 3 teeth, 4 eyes, 5 tongue, 8 membrane. In: work/ladder.blend (REA_CAND,
default Cand_40), work/ivory_faces.npz. Out: work/fix_master.blend (object Bat + Rig), work/fix.json."""
import heapq
import json
import math
import os

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAND = os.environ.get('REA_CAND', 'Cand_40')
CUT = 0.002            # m: spike faces whose lowest vertex is above this geodesic height are replaced
PERSIST = 0.0015       # m: a tip whose peak rises less than this above its saddle merges into its neighbour
MIN_TIP = 0.003        # m: shorter bumps are not spikes
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
CLAW_REGIONS = [0, 1, 3, 14, 4, 5, 8, 11]
ivf = np.load(os.path.join(HERE, 'work', 'ivory_faces.npz')); red_faces = ivf['red']

bm = bmesh.new(); bm.from_mesh(me)
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
deform = bm.verts.layers.deform.verify()
part_layer = bm.faces.layers.int.new('part')        # before holding any references: a new layer invalidates them
tip_layer = bm.faces.layers.float.new('tip')         # claws: 0 at the toe, 1 at the tip
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
teeth_pieces = []
for p in range(n):
    sel = np.flatnonzero(fpiece == p)
    if p == main:
        continue
    cen = np.mean([bm.faces[i].calc_center_median()[:] for i in sel], 0)
    if len(sel) <= 6 and cen[1] < -.19:
        teeth_pieces.append(p); part[sel] = 3            # replaced below
    elif len(sel) < 80:
        part[sel] = 5                                   # tongue sheet in the mouth
    else:
        part[sel] = 8                                   # wing membranes
part[red_faces & (fpiece == main)] = 4                  # eyes
teeth_verts = {p: [v for v in bm.verts if comp[v.index] == p] for p in teeth_pieces}
fc = np.array([f.calc_center_median()[:] for f in bm.faces])
ids = sorted(set(region.tolist()) - {-1})
head_regions = list(CLAW_REGIONS)
print('CLAW REGIONS', head_regions)


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


for f in bm.faces:
    f[part_layer] = int(part[f.index])
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
    # one claw per tip: only the old claw goes (surface distance from the tip up to the claw length), not the toe
    kept = 0
    for root, verts in tips.items():
        h = peak[root]
        if h < MIN_TIP:
            continue
        L = min(max(h, .005), .011)
        td = {root: 0.0}; heap = [(0.0, root.index, root)]
        while heap:
            d, _, v = heapq.heappop(heap)
            if d > td.get(v, math.inf) or d > 1.6 * L:
                continue
            for e in v.link_edges:
                y = e.other_vert(v)
                if y in rv:
                    nd = d + e.calc_length()
                    if nd < td.get(y, math.inf):
                        td[y] = nd; heapq.heappush(heap, (nd, y.index, y))
        reach = 1.05 * L
        cf = [f for f in rf if all(td.get(x, math.inf) <= reach for x in f.verts)]
        while len(cf) < 3 and reach < 1.6 * L:
            reach *= 1.15; cf = [f for f in rf if all(td.get(x, math.inf) <= reach for x in f.verts)]
        if not cf:
            continue
        cv = {x for f in cf for x in f.verts}
        co = np.array([x.co[:] for x in cv]); dd = np.array([td[x] for x in cv]); top = dd.max()
        band = co[dd >= .8 * top].mean(0)
        bands = [co[(dd <= hi) & (dd > lo)].mean(0) for lo, hi in zip(np.linspace(top, 0, 7)[1:], np.linspace(top, 0, 7)[:-1])
                 if ((dd <= hi) & (dd > lo)).any()]
        spikes.append({'region': r, 'faces': cf, 'verts': cv,
                       'spikes': [{'tip': Vector(root.co), 'height': top, 'band': Vector(band), 'bands': bands,
                                   'band_verts': [Vector(x.co) for x in cv if .55 * top <= td[x] <= .9 * top]}],
                       'material': int(np.bincount([f.material_index for f in cf]).argmax()),
                       'bone': dominant_bone(list(cv))})
        kept += 1
    print('REGION', r, 'faces', len(rf), 'tips', sorted(round(peak[x] * 1000, 1) for x in tips), 'claws', kept)
    for f in rf:                                        # labels for the claw paint (geometry kept, see below)
        f[part_layer] = 1
        f[tip_layer] = float(np.mean([dist[x] / max(peak[find(basin[x])], 1e-6) for x in f.verts]))

# left/right symmetry: a -x region takes the mirrored spikes and bone of its +x partner
M = Vector((-1, 1, 1))
centre = {R['region']: sum((f.calc_center_median() for f in R['faces']), Vector()) / len(R['faces']) for R in spikes}
for R in spikes if os.environ.get('FB_MIRROR') else []:
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
report = []


def new_vert(co, weights):
    v = bm.verts.new(co)
    for gi, w in weights.items():
        v[deform][gi] = w
    return v


smooth_set = set()
spikes = []                                         # claws are labelled, not rebuilt
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
    if False:
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
        base = S['band'].copy()                              # the old claw's base ring (a fit on a toe tip is unstable)
        chord = (tip - base).normalized(); length = (tip - base).length
        pts = [np.array(base)] + [np.array(x) for x in S['bands'][1:]] + [np.array(tip)]
        cl = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]); tt = cl / cl[-1]
        P0, P2 = np.array(base), np.array(tip); Bw = 2 * tt * (1 - tt)
        rhs = np.array(pts) - ((1 - tt) ** 2)[:, None] * P0 - (tt ** 2)[:, None] * P2
        p1 = Vector((Bw[:, None] * rhs).sum(0) / max((Bw ** 2).sum(), 1e-9))
        mid = (base + tip) / 2; bow = p1 - mid
        if bow.length > .3 * length:                         # few medial bands can throw the fit far off
            p1 = mid + bow.normalized() * .3 * length
        crest = False
        is_main = False
        if is_main:
            up = (Vector((0, 0, 1)) - chord * chord.z).normalized()
            out = Vector((1 if base.x > 0 else -1, 0, 0)); out = (out - chord * chord.dot(out)).normalized()
            p1 = (base + tip) / 2 - up * .16 * length + out * .07 * length
        # root radius from the old spike's lower band, round
        bv = S['band_verts'] or [S['band']]
        r_band = np.mean([((x - base) - chord * (x - base).dot(chord)).length for x in bv])
        r_root = float(np.clip(r_band, .0012, .0035))
        r_root = min(r_root, max(.0012, .8 * rim_mean))           # a root wider than its patch cuts the skin
        if crest:
            r_root = min(r_root, .006)
        sides, nring, power = 6, 4, .9
        p0 = base - chord * r_root * 1.5                     # root sunk into the toe along the claw
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
# --- teeth: clean cones on Head ---------------------------------------------------------------------------------
head_gi = gnames.index('Head'); teeth = []
for p in teeth_pieces:
    vs = teeth_verts[p]; co = np.array([v.co[:] for v in vs]); upper = co[:, 2].mean() > .208
    order = np.argsort(-co[:, 2] if upper else co[:, 2])
    base = Vector(co[order[:max(2, len(vs) // 3)]].mean(0)); tip0 = Vector(co[order[-1]])
    axis = (tip0 - base).normalized(); length = max((tip0 - base).length, .008 if upper else .006)
    rad = .0022 if upper else .0018; tip = base + axis * length; root = base - axis * length * (.2 if upper else .1)
    bmesh.ops.delete(bm, geom=vs, context='VERTS')
    u = axis.orthogonal().normalized(); w = axis.cross(u)
    ring = [new_vert(root + rad * (math.cos(a) * u + math.sin(a) * w), {head_gi: 1.0}) for a in (k * math.tau / 6 for k in range(6))]
    apex = new_vert(tip, {head_gi: 1.0}); bot = new_vert(root - axis * rad * .3, {head_gi: 1.0}); tf = []
    for k in range(6):
        tf.append(bm.faces.new((ring[k], ring[(k + 1) % 6], apex))); tf.append(bm.faces.new((ring[(k + 1) % 6], ring[k], bot)))
    bmesh.ops.recalc_face_normals(bm, faces=tf)
    for f in tf:
        f.material_index = 0; f[part_layer] = 3; f.smooth = True
    teeth.append({'upper': bool(upper), 'base': list(base), 'tip': list(tip), 'length_mm': round(length * 1000, 1)})


def boundary_cycles():
    out = {}
    for e in bm.edges:
        if e.is_boundary:
            f = e.link_faces[0]; l = next(l for l in f.loops if l.edge is e)
            out.setdefault(l.link_loop_next.vert, []).append(l.vert)
    cycles = []
    while any(out.values()):
        st = next(v for v, lst in out.items() if lst); path = [st]
        while True:
            nxt = out[path[-1]].pop() if out.get(path[-1]) else None
            if nxt is None:
                break
            if nxt in path:
                i = path.index(nxt); cycles.append(path[i:]); path = path[:i + 1]
                if not out.get(path[-1]):
                    break
                continue
            path.append(nxt)
    return cycles


def fan(poly, mat, prt):
    c = new_vert(sum((x.co for x in poly), Vector()) / len(poly), dict(poly[0][deform].items()))
    return [bm.faces.new((a, b, c)) for a, b in zip(poly, poly[1:] + poly[:1])], c


# --- holes and the membrane notch -------------------------------------------------------------------------------
filled = []
for cyc in boundary_cycles():
    per = sum((cyc[i].co - cyc[(i + 1) % len(cyc)].co).length for i in range(len(cyc)))
    parts = {f[part_layer] for x in cyc for f in x.link_faces}
    if per < .15 and 5 not in parts:
        fs, _ = fan(cyc, 0, 0)
        mat = cyc[0].link_faces[0].material_index
        for f in fs:
            f.material_index = mat; f[part_layer] = 8 if parts == {8} else 0; f.smooth = True
        filled.append({'kind': 'hole', 'vertices': len(cyc), 'perimeter_mm': round(per * 1000, 1),
                       'centre': list(sum((x.co for x in cyc), Vector()) / len(cyc))})
    elif per > .5 and parts == {8}:
        L = len(cyc); seg = [(cyc[i].co - cyc[(i + 1) % L].co).length for i in range(L)]; best = None
        nw = sum((f.normal * f.calc_area() for x in cyc for f in x.link_faces), Vector()).normalized()

        def signed(poly):
            return sum(a.co.cross(b.co).dot(nw) for a, b in zip(poly, poly[1:] + poly[:1]))
        whole = signed(cyc)
        for i in range(L):
            for k in range(2, 7):
                path = sum(seg[(i + m) % L] for m in range(k)); chord = (cyc[i].co - cyc[(i + k) % L].co).length
                sub = [cyc[(i + m) % L] for m in range(k + 1)]
                inward = signed(sub) * whole < 0                    # a notch turns against the outline; a tip with it
                if inward and path > .02 and chord < .35 * path and (best is None or chord / path < best[0]):
                    best = (chord / path, i, k)
        if best:
            _, i, k = best; poly = [cyc[(i + m) % L] for m in range(k + 1)]
            fs, _ = fan(poly, 0, 8)
            for f in fs:
                f.material_index = poly[0].link_faces[0].material_index; f[part_layer] = 8; f.smooth = True
            filled.append({'kind': 'notch', 'vertices': k + 1, 'ratio': round(best[0], 3),
                           'centre': list(sum((x.co for x in poly), Vector()) / len(poly))})
print('TEETH', teeth); print('FILLED', filled)

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
o.name = 'Bat'; o.hide_render = False
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'fix_master.blend'))
json.dump({'triangles': len(me.polygons), 'claws': report, 'teeth': teeth, 'filled': filled}, open(os.path.join(HERE, 'work', 'fix.json'), 'w'), indent=1)
print('HORNS triangles', len(me.polygons), 'caps', sum(x.get('cap_tris', 0) for x in report), 'horns', sum(x.get('tris', 0) for x in report), 'removed', sum(x.get('removed_tris', 0) for x in report))
for x in report:
    print(' ', {k: v for k, v in x.items() if k not in ('base', 'tip')})
