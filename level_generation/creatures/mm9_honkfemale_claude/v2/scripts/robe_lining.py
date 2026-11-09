"""Robe lining, boots on the leg bones, shorter boot shafts (Honk bodies, 2026-10-30 night pass).

Args (Blender): <master blend> <out blend> <report json> body_png=<png> orm_png=<png> [key=value: offset 0.004, boot_cut 0.30,
                wall_top 0.94 (metres above the floor), drop_inner_below 0.70, dark_uv u,v (plain patch), hem 0 (lift of the hem, m), hem_reach 0.25, dark_lo 0.98, dark_hi 1.14, dark_pct 8]

Why (review from below and from the feet end, overnight agent):
- Meshy's robe is single-sided cloth, so with back faces culled the far wall disappears: from below, and from the feet of a corpse,
  the legs hung in empty space and the background showed through the robe. MM9 closes the tube with a dark underside. Ours gets
  the mm6_cle add_inside lining: the outer wall duplicated `offset` behind itself along the vertex normal, flipped, with its twins'
  weights, on one dark texel of the belt (MM9's underside is dark too); a rim strip closes the hem, a dark cap closes the tube's
  top so nothing shows through the waist. The male's inner funnel (a plate with a jagged edge) is deleted: the lining replaces it.
- Boots were weighted partly to the robe's X chains (the female's mostly), so they tore under the robe in Death. Boot vertices now
  use Calf, Foot and Toe0 only.
- Boot shafts stop `boot_cut` above the floor: the top of the male's shaft came through the wall in Running (robe_gate.py), and
  nothing above the cut is ever seen.
Run after the last vertex move; existing UVs are not touched."""
import bpy, bmesh, sys, json
import numpy as np
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, REP = argv[:3]
opt = dict(a.split('=', 1) for a in argv[3:])
OFFSET = float(opt.get('offset', 0.004))
CUT = float(opt.get('boot_cut', 0.30))
TOP = float(opt.get('wall_top', 0.94))
DROP = float(opt.get('drop_inner_below', 0.70))
DLO, DHI = float(opt.get('dark_lo', 0.98)), float(opt.get('dark_hi', 1.14))
DPCT = float(opt.get('dark_pct', 8))
HEM, HEM_REACH = float(opt.get('hem', 0)), float(opt.get('hem_reach', 0.25))
HEM_LIP = float(opt.get('hem_lip', 0.30))
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']
rig = body.parent
if rig.animation_data:
    rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
me = body.data
M, Mi = body.matrix_world, body.matrix_world.inverted()
floor = min((M @ v.co).z for v in me.vertices)
H = lambda co: (M @ co).z - floor
names = [g.name for g in body.vertex_groups]
gi = {n: i for i, n in enumerate(names)}


def pixels(path):
    img = bpy.data.images.load(path, check_existing=True)
    px = np.empty(img.size[0] * img.size[1] * 4, np.float32)
    img.pixels.foreach_get(px)
    return px.reshape(img.size[1], img.size[0], 4)[..., :3]


BODY_PX, ORM_PX = pixels(opt['body_png']), pixels(opt['orm_png'])


def texel(px, uv):
    h, w = px.shape[:2]
    return px[min(h - 1, max(0, int(uv.y * h))), min(w - 1, max(0, int(uv.x * w)))]


bm = bmesh.new(); bm.from_mesh(me)
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
dl = bm.verts.layers.deform.active
lh, lk = bm.faces.layers.int['head'], bm.faces.layers.int['hand']
uvb, uvh = bm.loops.layers.uv['UVMap'], bm.loops.layers.uv['HeadUV']


def components():
    comp, cid = {}, 0
    for v in bm.verts:
        if v in comp:
            continue
        st = [v]; comp[v] = cid
        while st:
            x = st.pop()
            for e in x.link_edges:
                y = e.other_vert(x)
                if y not in comp:
                    comp[y] = cid; st.append(y)
        cid += 1
    return comp, cid


comp, n = components()
share = np.zeros(n); size = np.zeros(n)
for v in bm.verts:
    size[comp[v]] += 1
    share[comp[v]] += sum(w for g, w in v[dl].items() if names[g].endswith(('Foot', 'Toe0', 'Calf')) and ' ' in names[g])
ratio = share / np.maximum(size, 1)
# the boots: the two loose parts lowest on the floor that are mostly leg, or (the female's) carry leg weights at all
low = {}
for v in bm.verts:
    low[comp[v]] = min(low.get(comp[v], 9), H(v.co))
tall = {}
for v in bm.verts:
    tall[comp[v]] = max(tall.get(comp[v], -9), H(v.co))
boots = sorted([c for c in low if low[c] < 0.02 and tall[c] < 0.7], key=lambda c: -size[c])[:2]
assert len(boots) == 2, (boots, low, tall)
rep = {'boots': {int(c): {'verts': int(size[c]), 'leg_share_before': round(float(ratio[c]), 3), 'top': round(tall[c], 3)} for c in boots}}

# ---- boots on the leg bones only
legs = {s: [gi[f'Bip01 {s} {b}'] for b in ('Calf', 'Foot', 'Toe0')] for s in 'LR'}
keep = set(legs['L'] + legs['R'])
# which way the toes point in Blender's rest pose: from the ankle towards the toe bone
_a = rig.matrix_world @ rig.data.bones['Bip01 L Foot'].head_local
_b = rig.matrix_world @ rig.data.bones['Bip01 L Toe0'].head_local
FWD = 1.0 if _b.y > _a.y else -1.0
for c in boots:
    vs = [v for v in bm.verts if comp[v] == c]
    side = 'L' if sum(sum(w for g, w in v[dl].items() if g in legs['L']) for v in vs) >= sum(sum(w for g, w in v[dl].items() if g in legs['R']) for v in vs) else 'R'
    calf, foot, toe = legs[side]
    moved = 0
    ankle = (rig.matrix_world @ rig.data.bones[f'Bip01 {side} Foot'].head_local).z - floor
    ball = (rig.matrix_world @ rig.data.bones[f'Bip01 {side} Toe0'].head_local)
    for v in vs:
        if opt.get('boot_weights') == 'height':
            # the part was mostly on robe chains: nothing to keep, so a smooth ankle and ball of the foot from the bones
            co = M @ v.co
            t = min(1.0, max(0.0, (H(v.co) - (ankle - 0.02)) / 0.14))
            wc = t * t * (3 - 2 * t)
            q = min(1.0, max(0.0, (co.y * FWD - ball.y * FWD + 0.05) / 0.08))
            wt = (1 - wc) * q * q * (3 - 2 * q)
            for g in list(v[dl].keys()):
                del v[dl][g]
            for g, x in ((calf, wc), (foot, 1 - wc - wt), (toe, wt)):
                if x > 1e-3:
                    v[dl][g] = x
            moved += 1
            continue
        w = {g: x for g, x in v[dl].items() if g in legs[side]}
        tot_old = sum(v[dl].values())
        lost = tot_old - sum(w.values())
        moved += lost > 0.01
        if lost > 1e-4 or not w:
            # the part the robe chains held goes by height: shaft to the calf, ankle down to the foot
            h = H(v.co)
            target = calf if h > 0.16 else foot
            w[target] = w.get(target, 0.0) + lost
        tot = sum(w.values())
        for g in list(v[dl].keys()):
            del v[dl][g]
        for g, x in w.items():
            v[dl][g] = x / tot
    rep['boots'][int(c)]['side'] = side
    rep['boots'][int(c)]['verts_reweighted'] = int(moved)

# ---- Meshy's forearm remnants inside the sleeves: small loose skin-painted parts that poke through the cuff as shards
if opt.get('drop_forearm_parts') == '1':
    drop = []
    for c in range(n):
        vs = [v for v in bm.verts if comp[v] == c]
        if not 20 < len(vs) < 120:
            continue
        fs = {f for v in vs for f in v.link_faces}
        if any(f[lh] or f[lk] for f in fs):
            continue
        share = sum(w for v in vs for g, w in v[dl].items() if 'Forearm' in names[g] or names[g].endswith(' Hand')) / len(vs)
        if share > 0.8:
            drop += list(fs)
    rep['forearm_faces_dropped'] = len(drop)
    bmesh.ops.delete(bm, geom=drop, context='FACES_ONLY')
    for v in [v for v in bm.verts if not v.link_faces]:
        bm.verts.remove(v)
    bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    comp, n = components()
# ---- shaft cut
geom = [f for f in bm.faces if comp[f.verts[0]] in boots]
geom = list({x for f in geom for x in (f, *f.verts, *f.edges)})
bmesh.ops.bisect_plane(bm, geom=geom, plane_co=Mi @ Vector((0, 0, floor + CUT)), plane_no=(Mi.to_3x3().transposed() @ Vector((0, 0, 1))).normalized(), clear_inner=False, clear_outer=False)
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
comp, n = components()
boot_parts = {comp[v] for v in bm.verts if v.link_faces and H(v.co) < 0.02 and sum(w for g, w in v[dl].items() if g in keep) > 0.999}
cutf = [f for f in bm.faces if comp[f.verts[0]] in boot_parts and all(H(v.co) > CUT - 1e-4 for v in f.verts)]
rep['boot_faces_cut'] = len(cutf)
bmesh.ops.delete(bm, geom=cutf, context='FACES_ONLY')
for v in [v for v in bm.verts if not v.link_faces]:
    bm.verts.remove(v)
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
comp, n = components()
boot_v = {v for v in bm.verts if v.link_faces and H(v.co) < CUT + 0.02 and sum(w for g, w in v[dl].items() if g in keep) > 0.999}


def arm(v):
    w = v[dl]
    if not len(w):
        return False
    g = max(w.items(), key=lambda kv: kv[1])[0]
    return any(k in names[g] for k in ('Forearm', 'UpperArm', 'Hand', 'Clavicle', 'Finger', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky'))


cand = [f for f in bm.faces if not f[lh] and not f[lk] and not all(v in boot_v for v in f.verts)
        and H(f.calc_center_median()) < TOP and not any(arm(v) for v in f.verts)]
main = np.bincount([comp[f.verts[0]] for f in cand]).argmax()
cand = [f for f in cand if comp[f.verts[0]] == main]
# radial ray test: a face with cloth further out is an inner layer
T = np.array([[tuple(M @ v.co) for v in f.verts] for f in cand])
axis = T.reshape(-1, 3)[:, :2].mean(0)
cen = T.mean(1)
rad = cen - np.r_[axis, 0]
rad[:, 2] = 0
rad /= np.maximum(np.linalg.norm(rad, axis=1, keepdims=True), 1e-9)
A, e1, e2 = T[:, 0], T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]
inner = np.zeros(len(cand), bool)
for i in range(len(cand)):
    h = np.cross(rad[i], e2)
    det = (e1 * h).sum(1)
    o = cen[i] - A
    with np.errstate(divide='ignore', invalid='ignore'):
        u = (o * h).sum(1) / det
        q = np.cross(o, e1)
        w = (q * rad[i]).sum(1) / det
        t = (e2 * q).sum(1) / det
    inner[i] = ((np.abs(det) > 1e-14) & (u >= 0) & (w >= 0) & (u + w <= 1) & (t > 0.01)).any()
# a face turned towards the tube's axis is an inner layer too: the male's folded hem lip
for i, f in enumerate(cand):
    if not inner[i] and H(f.calc_center_median()) < HEM_LIP:      # only at the hem: higher up these are the wall's own pleats, and deleting them opened a slit in the side of the robe
        n_ = np.array((M.to_3x3() @ f.normal).normalized())
        if n_ @ rad[i] < -0.05:
            inner[i] = True
drop = [f for f, b in zip(cand, inner) if b and H(f.calc_center_median()) < DROP]
outer = [f for f, b in zip(cand, inner) if not b]
rep.update(wall_faces=len(outer), inner_dropped=len(drop))
# dark texel: the belt
belt = [f for f in bm.faces if not f[lh] and not f[lk] and comp[f.verts[0]] == main and DLO < H(f.calc_center_median()) < DHI
        and not any(arm(v) for v in f.verts)]
if len(belt) < 8:
    belt = [f for f in bm.faces if not f[lh] and not f[lk] and DLO < H(f.calc_center_median()) < DHI and not any(arm(v) for v in f.verts)]


def centre_uv(f):
    return sum((Vector(tuple(l[uvb].uv)) for l in f.loops), Vector((0, 0))) / len(f.loops)


lum = np.array([texel(BODY_PX, centre_uv(f)) @ np.array([0.299, 0.587, 0.114]) for f in belt])
order = np.argsort(lum)[:max(1, int(len(lum) * DPCT / 100))]
dark = belt[int(max(order, key=lambda i: texel(ORM_PX, centre_uv(belt[i]))[1]))]
dark_uv = tuple(centre_uv(dark))
if 'dark_uv' in opt:            # a plain dark patch painted by medallion_paint.py: no leather grain, no shine
    dark_uv = tuple(float(x) for x in opt['dark_uv'].split(','))
rep['dark_rgb'] = [round(float(x), 3) for x in texel(BODY_PX, Vector(dark_uv))]
template = outer[0]
bmesh.ops.delete(bm, geom=drop, context='FACES_ONLY')
for v in [v for v in bm.verts if not v.link_faces]:
    bm.verts.remove(v)
bm.faces.ensure_lookup_table(); bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table()
# ---- hem raised off the shoes (MM9's hem clears them; the female's ran along the floor): the lowest HEM metres of the wall lift
if HEM > 0:
    moved = {}
    for f in outer:
        for v in f.verts:
            moved[v] = max(0.0, 1 - H(v.co) / HEM_REACH)
    for v, x in moved.items():
        v.co = Mi @ ((M @ v.co) + Vector((0, 0, HEM * x * x * (3 - 2 * x))))
    rep['hem_raised'] = HEM
    bm.normal_update()
# ---- lining
normal = {}
for f in outer:
    for v in f.verts:
        normal[v] = normal.get(v, Vector()) + f.normal * f.calc_area()
was_boundary = {e for e in bm.edges if e.is_boundary}
out = bmesh.ops.duplicate(bm, geom=outer)
vmap = out['vert_map']
# a deep inward pleat has cloth right behind its wall: a full offset would cross it and show as a dark line on the outside, so each vertex goes at most half way to the next cloth
from mathutils.bvhtree import BVHTree
_i = {v: k for k, v in enumerate(bm.verts)}
_bvh = BVHTree.FromPolygons([M @ v.co for v in bm.verts], [[_i[x] for x in f.verts] for f in outer])
clamped = 0
for v, nrm in normal.items():
    n_ = (M.to_3x3() @ nrm).normalized()
    o_ = (M @ v.co) - n_ * 0.0015
    hit = _bvh.ray_cast(o_, -n_, OFFSET * 2.2)
    off = OFFSET
    if hit[0] is not None:
        off = min(OFFSET, max(0.001, (hit[3] + 0.0015) * 0.5))
        clamped += off < OFFSET
    vmap[v].co = Mi @ ((M @ v.co) - n_ * off)
rep['lining_verts_clamped'] = clamped
lining = [g for g in out['geom'] if isinstance(g, bmesh.types.BMFace)]
bmesh.ops.reverse_faces(bm, faces=lining)
for f in lining:
    for l in f.loops:
        l[uvb].uv = dark_uv; l[uvh].uv = dark_uv
    f[lh] = 0; f[lk] = 0
# rim where the outer wall has an open edge (hem, slits)
oset = set(outer)
rim = []
for e in list(was_boundary):
    if not e.is_valid or not e.is_boundary or e.link_faces[0] not in oset:
        continue
    f0 = e.link_faces[0]
    a, b = e.verts
    a2, b2 = vmap[a], vmap[b]
    for tri in ((a, b, b2), (a, b2, a2)):
        f = bm.faces.new(tri)
        f[lh] = 0; f[lk] = 0; f.smooth = f0.smooth
        f.normal_update()
        if f.normal.dot(f.calc_center_median() - f0.calc_center_median()) < 0:
            f.normal_flip()
        for l in f.loops:
            l[uvb].uv = dark_uv; l[uvh].uv = dark_uv
        rim.append(f)
# cap where only the lining is open: the tube's top
lset = set(lining)
open_edges = [e for e in bm.edges if e.is_boundary and e.link_faces[0] in lset]
loops, seen = [], set()
for e in open_edges:
    if e in seen:
        continue
    lp, st = [], [e]
    while st:
        x = st.pop()
        if x in seen:
            continue
        seen.add(x); lp.append(x)
        for v in x.verts:
            st += [y for y in v.link_edges if y.is_boundary and y.link_faces[0] in lset and y not in seen]
    loops.append(lp)
rep['open_loops_on_lining'] = [len(x) for x in loops]
cap = []
for lp in loops:
    if len(lp) < 6:
        continue
    vs = {v for e in lp for v in e.verts}
    c = sum((v.co for v in vs), Vector()) / len(vs)
    cv = bm.verts.new(c)
    acc = {}
    for v in vs:
        for g, w in v[dl].items():
            acc[g] = acc.get(g, 0) + w / len(vs)
    top = sorted(acc.items(), key=lambda kv: -kv[1])[:4]
    tot = sum(w for _, w in top)
    for g, w in top:
        cv[dl][g] = w / tot
    # planar cap: the ring is not flat, and a fan on it shades as facets, or stands a sliver edge-on and shows a bright slash into the lit robe. The cap has its own
    # ring on one plane (hidden inside the lining's dark): one normal, so plain dark
    zm_ = sum((M @ v.co).z for v in vs) / len(vs)
    flat = {}
    for v in vs:
        q_ = M @ v.co
        nv_ = bm.verts.new(Mi @ Vector((q_.x, q_.y, zm_)))
        for g, w in v[dl].items():
            nv_[dl][g] = w
        flat[v] = nv_
    cv.co = Mi @ Vector(((M @ cv.co).x, (M @ cv.co).y, zm_))
    # a strip joins the flat cap to the wandering ring: without it the gaps show the lit robe as bright spikes round a black disc
    for e in lp:
        a_, b_ = e.verts
        for tri in ((a_, b_, flat[b_]), (a_, flat[b_], flat[a_])):
            if len({id(x) for x in tri}) < 3 or (tri[0].co - tri[2].co).length < 1e-6 or (tri[1].co - tri[2].co).length < 1e-6 or (tri[0].co - tri[1].co).length < 1e-6:
                continue
            f = bm.faces.new(tri)
            f[lh] = 0; f[lk] = 0; f.smooth = False
            f.normal_update()
            cen_ = M @ f.calc_center_median()
            if (M.to_3x3() @ f.normal).dot(Vector((M @ c).to_tuple()) - cen_) < 0:      # faces the tube's axis
                f.normal_flip()
            for l in f.loops:
                l[uvb].uv = dark_uv; l[uvh].uv = dark_uv
            cap.append(f)
    for e in lp:
        f = bm.faces.new((flat[e.verts[0]], flat[e.verts[1]], cv))
        f[lh] = 0; f[lk] = 0; f.smooth = False
        f.normal_update()
        if (M.to_3x3() @ f.normal).z > 0:      # faces down, into the tube
            f.normal_flip()
        for l in f.loops:
            l[uvb].uv = dark_uv; l[uvh].uv = dark_uv
        cap.append(f)
    # a loop that does not quite close leaves a wedge between two spokes, a bright slit into the robe: close it
    spokes = [e for e in cv.link_edges if len(e.link_faces) == 1]
    ends = [e.other_vert(cv) for e in spokes]
    for a_, b_ in zip(ends[::2], ends[1::2]):
        f = bm.faces.new((a_, b_, cv))
        f[lh] = 0; f[lk] = 0; f.smooth = False
        f.normal_update()
        if (M.to_3x3() @ f.normal).z > 0:
            f.normal_flip()
        for l in f.loops:
            l[uvb].uv = dark_uv; l[uvh].uv = dark_uv
        cap.append(f)
    rep['cap_wedges_closed'] = rep.get('cap_wedges_closed', 0) + len(ends) // 2
    if opt.get('seal', '0') != '1':
        continue
    # seal disc: the ring is not planar, so a sliver of the fan can stand edge-on and let the lit robe show as a bright slash. A small flat dark disc just above
    # the fan, on the fan centre's weights, covers it from below
    rr = sum(((M @ v.co) - (M @ c)).length for v in vs) / len(vs)
    ring_d = []
    X_ = Vector((1, 0, 0)); Y_ = Vector((0, 1, 0))
    wc = M @ c + Vector((0, 0, 0.012))
    for k in range(12):
        a_ = 2 * 3.14159265 * k / 12
        d = bm.verts.new(Mi @ (wc + X_ * (0.62 * rr * np.cos(a_)) + Y_ * (0.62 * rr * np.sin(a_))))
        for g, w in cv[dl].items():
            d[dl][g] = w
        ring_d.append(d)
    dc = bm.verts.new(Mi @ wc)
    for g, w in cv[dl].items():
        dc[dl][g] = w
    for k in range(12):
        f = bm.faces.new((ring_d[k], ring_d[(k + 1) % 12], dc))
        f[lh] = 0; f[lk] = 0; f.smooth = False
        f.normal_update()
        if (M.to_3x3() @ f.normal).z > 0:
            f.normal_flip()
        for l in f.loops:
            l[uvb].uv = dark_uv; l[uvh].uv = dark_uv
        cap.append(f)
rep.update(lining_faces=len(lining), rim_faces=len(rim), cap_faces=len(cap), tris_after=len(bm.faces))
bm.to_mesh(me); bm.free(); me.update()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('ROBE_LINING', json.dumps(rep))
json.dump(rep, open(REP, 'w'), indent=1)
