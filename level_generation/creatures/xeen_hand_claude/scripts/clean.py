"""Carnage Hand: clean the Smart Topology body and build the palm mouth. Reads work/clean_v1.blend and
work/mouth_frame.json, writes work/clean_v2.blend (one mesh 'Hand', face attribute 'part') and work/mouth.json.

Meshy returned the hand double-walled (an inner copy of the whole skin, joined to the outer one through the slit of
the lips) with soft lumpy lips and nine thin rod fangs. Here:
  - the lip region (an ellipse of 0.105 x 0.062 m round the mouth in the palm plane) and the rod fangs are deleted;
    the outer skin is then its own connected component (the inner shell is the other one) and is kept alone;
  - small holes of the outer skin (<= 12 edges) are filled; the skin is collapse-decimated (SKIN_RATIO);
  - the mouth is hand-built in the palm frame (O, n out of the palm, U along the slit, V up the palm):
      part 1  rim: a strip that zips the ragged cut to a clean elliptical aperture (a 0.075 x b 0.045)
      part 2  gullet: a funnel from the aperture 0.085 m into the palm (the palm is 0.19 m thick there)
      part 3  tongue: a low ellipsoid at the bottom of the gullet
      part 4  fangs: a ring of conical fangs on the aperture rim pointing inward (long canines near the corners)
      part 5/6 upper / lower lip lids: closed shells (outer dome, rolled slit edge, inner gum face) that meet at the
              slit and cover the aperture when closed; each turns about a hinge axis along U, D = 0.06 m behind the
              palm, so opening slides it up (down) under the palm skin like an eyelid and bares the fang ring.
  - part 0 skin."""
import bpy, os, sys, json, math, bmesh
import numpy as np
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIN_RATIO = 0.62
EA, EB = 0.105, 0.062            # lip cut
AA, AB = 0.075, 0.045            # aperture
LA, LB, LH, LT = 0.100, 0.062, 0.022, 0.006   # lids: half axes, dome height, thickness
HINGE_D = 0.035
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'clean_v1.blend'))
ob = bpy.data.objects['Hand']; me = ob.data
F = json.load(open(os.path.join(HERE, 'work', 'mouth_frame.json')))
O, n, U, V = (np.array(F[k]) for k in ('O', 'n', 'U', 'V'))
hid = np.zeros(len(me.polygons), np.int32); me.attributes['hidden'].data.foreach_get('value', hid)
pc = np.zeros(len(me.polygons), np.int32); me.attributes['piece'].data.foreach_get('value', pc)
for name in ('hidden', 'piece'):
    me.attributes.remove(me.attributes[name])
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()


def uvh(p):
    d = np.array(tuple(p)) - O
    return d @ U, d @ V, d @ n


def lip(f):
    u, v, h = uvh(f.calc_center_median())
    return (u / EA) ** 2 + (v / EB) ** 2 < 1 and abs(h) < 0.06


for f in bm.faces: f.tag = bool(hid[f.index])
bmesh.ops.delete(bm, geom=[f for f in bm.faces if pc[f.index] or lip(f)], context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bm.faces.ensure_lookup_table()
comp = {}; cid = 0; members = []
for f in bm.faces:
    if f.index in comp: continue
    st = [f]; comp[f.index] = cid; mem = [f]
    while st:
        x = st.pop()
        for e in x.edges:
            for g in e.link_faces:
                if g.index not in comp: comp[g.index] = cid; st.append(g); mem.append(g)
    members.append(mem); cid += 1
keep = min(range(cid), key=lambda k: sum(f.tag for f in members[k]) / len(members[k]))
drop = [f for k in range(cid) if k != keep for f in members[k]]
print('COMPONENTS', [(len(m), sum(f.tag for f in m)) for m in members], 'kept', keep)
bmesh.ops.delete(bm, geom=drop, context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')


def boundary_loops(bm):
    seen = set(); out = []
    for e in bm.edges:
        if not e.is_boundary or e.index in seen: continue
        comp = []; st = [e]; seen.add(e.index)
        while st:
            x = st.pop(); comp.append(x)
            for v in x.verts:
                for y in v.link_edges:
                    if y.is_boundary and y.index not in seen: seen.add(y.index); st.append(y)
        out.append(comp)
    return out


bm.edges.index_update()
small = [e for L in boundary_loops(bm) if len(L) <= 12 for e in L]
res = bmesh.ops.holes_fill(bm, edges=small, sides=12)
print('HOLES filled', len(res['faces']))
bmesh.ops.triangulate(bm, faces=bm.faces[:])
bm.to_mesh(me); bm.free(); me.update()
# decimate the skin
bpy.context.view_layer.objects.active = ob
for o in bpy.data.objects: o.select_set(o == ob)
t0 = len(me.polygons)
m = ob.modifiers.new('dec', 'DECIMATE'); m.decimate_type = 'COLLAPSE'; m.ratio = SKIN_RATIO
m.use_collapse_triangulate = True
bpy.ops.object.modifier_apply(modifier='dec')
me = ob.data
print('SKIN', t0, '->', len(me.polygons))

bm = bmesh.new(); bm.from_mesh(me)
loops = boundary_loops(bm)
print('LOOPS after decimate', sorted(len(L) for L in loops))
res = bmesh.ops.holes_fill(bm, edges=[e for L in loops if len(L) <= 12 for e in L], sides=12)
bmesh.ops.triangulate(bm, faces=res['faces'])
loops = boundary_loops(bm)
mouth = max(loops, key=len)


def folds(bm):
    bm.normal_update()
    out = set()
    for e in bm.edges:
        if len(e.link_faces) == 2 and e.link_faces[0].normal.dot(e.link_faces[1].normal) < -0.2:
            out.update(e.link_faces)
    return out


for it in range(6):                     # folded shards (Meshy skin and decimation): relax their vertices
    fs = folds(bm)
    print('FOLDS pass', it, len(fs))
    if not fs: break
    vs_ = {v for f in fs for v in f.verts}
    vs_ |= {o for v in list(vs_) for e in v.link_edges for o in e.verts}
    for _ in range(4):
        new = {v: sum((e.other_vert(v).co for e in v.link_edges), Vector()) / len(v.link_edges) for v in vs_
               if not v.is_boundary}
        for v, c in new.items(): v.co = v.co * 0.3 + c * 0.7
for it in range(4):                     # pinched spikes / dimples: umbrella offset large against the edge length
    bad = []
    for v in bm.verts:
        if v.is_boundary or not v.link_edges: continue
        nb = [e.other_vert(v).co for e in v.link_edges]
        avg = sum(nb, Vector()) / len(nb); el = sum((c - v.co).length for c in nb) / len(nb)
        if (avg - v.co).length > 0.45 * el: bad.append(v)
    print('SPIKES pass', it, len(bad))
    if not bad: break
    vs_ = set(bad) | {e.other_vert(v) for v in bad for e in v.link_edges}
    for _ in range(3):
        new = {v: sum((e.other_vert(v).co for e in v.link_edges), Vector()) / len(v.link_edges) for v in vs_
               if not v.is_boundary}
        for v, c in new.items(): v.co = v.co * 0.4 + c * 0.6
# the ragged cut: smooth the boundary loop along itself in the palm plane, heights onto the skin fit (below)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
# skin height model near the mouth: quadratic fit h(u, v) to skin vertices just outside the cut
P = np.array([uvh(v.co) for v in bm.verts])
r = (P[:, 0] / 0.17) ** 2 + (P[:, 1] / 0.12) ** 2
sel = (r < 1) & (np.abs(P[:, 2]) < 0.04)
A_ = np.c_[np.ones(sel.sum()), P[sel, 0], P[sel, 1], P[sel, 0] ** 2, P[sel, 0] * P[sel, 1], P[sel, 1] ** 2]
coef = np.linalg.lstsq(A_, P[sel, 2], rcond=None)[0]
skin_h = lambda u, v: float(coef @ np.array([1, u, v, u * u, u * v, v * v]))
print('SKIN fit', sel.sum(), 'h(0,0)', round(skin_h(0, 0), 4), 'rms', round(float(np.sqrt(np.mean((A_ @ coef - P[sel, 2]) ** 2))), 4))
X = lambda u, v, h: Vector((O + U * u + V * v + n * h).tolist())
mv = {v for e in mouth for v in e.verts}
for _ in range(12):
    new = {}
    for v in mv:
        nb = [e.other_vert(v) for e in v.link_edges if e.is_boundary]
        new[v] = (sum((o.co for o in nb), Vector()) / len(nb)) * 0.5 + v.co * 0.5
    for v, c in new.items(): v.co = c
for v in mv:
    u_, v_, h_ = uvh(v.co)
    v.co = X(u_, v_, skin_h(u_, v_))
part = bm.faces.layers.int.new('part')
for f in bm.faces: f[part] = 0

# ordered mouth loop
vs = {}
for e in mouth:
    for v in e.verts:
        vs.setdefault(v, []).append(e)
start = mouth[0].verts[0]; order = [start]; prev_e = None; cur = start
while True:
    es = [e for e in vs[cur] if e is not prev_e]
    e = es[0]; nxt = e.other_vert(cur)
    if nxt is start: break
    order.append(nxt); prev_e = e; cur = nxt
ang = lambda u, v, a, b: math.atan2(v / b, u / a)
ra = np.unwrap([ang(*uvh(v.co)[:2], EA, EB) for v in order])
if ra[-1] < ra[0]:
    order = order[::-1]
# the aperture ellipse gets one vertex per cut-loop vertex at the same elliptical angle: a strip of radial quads
NE = len(order)
ar = [ang(*uvh(v.co)[:2], EA, EB) for v in order]
ell = [bm.verts.new(X(AA * math.cos(t), AB * math.sin(t), skin_h(AA * math.cos(t), AB * math.sin(t)) - 0.002))
       for t in ar]
for k in range(NE):
    f = bm.faces.new((order[k], order[(k + 1) % NE], ell[(k + 1) % NE], ell[k])); f[part] = 1
# gullet: rings into the palm
h0 = skin_h(0, 0)
prev = ell
for depth, sc in ((0.008, 0.97), (0.03, 0.78), (0.055, 0.5), (0.075, 0.22)):
    ring = [bm.verts.new(X(AA * sc * math.cos(ar[k]), AB * sc * math.sin(ar[k]), h0 - depth)) for k in range(NE)]
    for k in range(NE):
        f = bm.faces.new((prev[k], prev[(k + 1) % NE], ring[(k + 1) % NE], ring[k])); f[part] = 2
    prev = ring
tip = bm.verts.new(X(0, 0, h0 - 0.085))
for k in range(NE):
    f = bm.faces.new((prev[k], prev[(k + 1) % NE], tip)); f[part] = 2
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
for L in boundary_loops(bm):                 # left-over small skin holes: fan to their centre
    if len(L) > 12: continue
    vs_ = {v for e in L for v in e.verts}; cv = bm.verts.new(sum((v.co for v in vs_), Vector()) / len(vs_))
    for e in L:
        f = bm.faces.new((e.verts[0], e.verts[1], cv)); f[part] = 0
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
nb = sum(1 for e in bm.edges if e.is_boundary)
print('SKIN closed: boundary edges', nb)


def add_closed(build, pid):
    new = build()
    bmesh.ops.triangulate(bm, faces=[f for f in new if len(f.verts) > 3])
    fs = [f for f in bm.faces if f[part] == -1]
    for f in fs: f[part] = pid
    bmesh.ops.recalc_face_normals(bm, faces=fs)


def face(vs):
    out = []
    for v in vs:
        if not out or out[-1] is not v: out.append(v)
    if len(out) > 1 and out[0] is out[-1]: out.pop()
    if len(set(out)) < 3: return None
    f = bm.faces.new(out); f[part] = -1; return f


def tongue():
    c = np.array([0, -0.012, h0 - 0.05]); fs = []
    rings = []
    for a in range(1, 6):
        th = math.pi * a / 6
        rings.append([bm.verts.new(X(c[0] + 0.022 * math.sin(th) * math.cos(2 * math.pi * k / 10),
                                     c[1] + 0.014 * math.sin(th) * math.sin(2 * math.pi * k / 10),
                                     c[2] + 0.011 * math.cos(th))) for k in range(10)])
    top = bm.verts.new(X(c[0], c[1], c[2] + 0.011)); bot = bm.verts.new(X(c[0], c[1], c[2] - 0.011))
    for k in range(10):
        fs.append(face([top, rings[0][k], rings[0][(k + 1) % 10]]))
        fs.append(face([bot, rings[-1][(k + 1) % 10], rings[-1][k]]))
        for a in range(4):
            fs.append(face([rings[a][k], rings[a + 1][k], rings[a + 1][(k + 1) % 10], rings[a][(k + 1) % 10]]))
    return [f for f in fs if f]


FANGS = []
for k in range(5):
    FANGS.append((50 + 20 * k, 0.019, 0.0042, 0.0, 18))          # upper row: phi deg, length, radius, bend, tilt
    FANGS.append((-50 - 20 * k, 0.016, 0.0038, 0.0, 18))         # lower row
FANGS += [(17, 0.032, 0.0058, -1, 6), (163, 0.032, 0.0058, -1, 6), (-36, 0.024, 0.005, 1, 8),
          (-144, 0.024, 0.005, 1, 8)]                            # canines: bend -1 = point down (-V), +1 = up


def fangs():
    fs = []
    for phi, L, rad, vert, tilt in FANGS:
        p = math.radians(phi)
        bu, bv = AA * 0.985 * math.cos(p), AB * 0.985 * math.sin(p)
        base = np.array([bu, bv, skin_h(bu, bv) - 0.005])
        d2 = -np.array([bu / AA ** 2, bv / AB ** 2]); d2 /= np.linalg.norm(d2)
        if vert:
            d2 = 0.3 * d2 + 0.7 * np.array([0, vert]); d2 /= np.linalg.norm(d2)
        t = math.radians(tilt)
        d = np.array([d2[0] * math.cos(t), d2[1] * math.cos(t), math.sin(t)])
        side = np.cross(d, [0, 0, 1.0]); side /= np.linalg.norm(side); up = np.cross(side, d)
        rings = []
        for s, rr in ((-0.004, 1.0), (0.45, 0.62)):
            c = base + d * L * s
            rings.append([bm.verts.new(X(*(c + rad * rr * (side * math.cos(2 * math.pi * k / 6) +
                                                          up * math.sin(2 * math.pi * k / 6))))) for k in range(6)])
        tipv = bm.verts.new(X(*(base + d * L)))
        bc = bm.verts.new(X(*(base - d * 0.004)))
        for k in range(6):
            k1 = (k + 1) % 6
            fs.append(face([rings[0][k], rings[0][k1], rings[1][k1], rings[1][k]]))
            fs.append(face([rings[1][k], rings[1][k1], tipv]))
            fs.append(face([bc, rings[0][k1], rings[0][k]]))
    return [f for f in fs if f]


NU, NW = 18, 4


def lid(s):
    def build():
        cols = []
        for i in range(NU + 1):
            al = -math.pi / 2 + math.pi * i / NU
            u = LA * math.sin(al); c = math.sqrt(max(0.0, 1 - (u / LA) ** 2))
            if i in (0, NU):
                cv = bm.verts.new(X(u, 0, skin_h(u, 0) - 0.004 - LT / 2))
                cols.append([cv] * (2 * (NW + 1) + 1)); continue
            outer, inner = [], []
            for j in range(NW + 1):
                w = 0.07 + 0.93 * j / NW
                v = s * w * LB * c
                q = max(0.0, 1 - (u / LA) ** 2 - (v / LB) ** 2) ** 0.5
                zo = skin_h(u, v) + LH * q - 0.004
                outer.append(X(u, v, zo)); inner.append(X(u, v, zo - LT))
            v0 = s * 0.07 * LB * c
            q0 = max(0.0, 1 - (u / LA) ** 2 - (v0 / LB) ** 2) ** 0.5
            roll = X(u, v0 - s * LT * 0.55, skin_h(u, v0) + LH * q0 - 0.004 - LT / 2)
            ring = [bm.verts.new(p) for p in outer[::-1]] + [bm.verts.new(roll)] + [bm.verts.new(p) for p in inner]
            cols.append(ring)
        fs = []
        m_ = len(cols[0])
        for i in range(NU):
            a, b = cols[i], cols[i + 1]
            for k in range(m_):
                k1 = (k + 1) % m_
                fs.append(face([a[k], b[k], b[k1], a[k1]]))
        return [f for f in fs if f]
    return build


add_closed(tongue, 3)
add_closed(fangs, 4)
add_closed(lid(1), 5)
add_closed(lid(-1), 6)
# closed pieces: outward normals (recalc does that per closed component)
bm.to_mesh(me); bm.free(); me.update()
for p in me.polygons: p.use_smooth = True
pa = np.zeros(len(me.polygons), np.int32); me.attributes['part'].data.foreach_get('value', pa)
for p in me.polygons:
    if pa[p.index] == 4: p.use_smooth = False
print('TRIS', len(me.polygons), 'per part', {int(k): int((pa == k).sum()) for k in np.unique(pa)})
C = O + n * (h0 - HINGE_D)
json.dump({'O': O.tolist(), 'n': n.tolist(), 'U': U.tolist(), 'V': V.tolist(), 'h0': h0, 'hinge': C.tolist(),
           'aperture': [AA, AB], 'lid': [LA, LB, LH, LT], 'hinge_d': HINGE_D, 'skin_coef': coef.tolist()},
          open(os.path.join(HERE, 'work', 'mouth.json'), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'clean_v2.blend'))
