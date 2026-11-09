"""Mouth cavity for the MM9 jaw (the MM9 clips open the mouth: cow up to 15-22 deg, goat 10-24 deg).

The Meshy head is closed. This stage (after reduce + symmetrize, before the UVs) cuts the lip line and builds a real
oral cavity behind it, skinned between the skull and the jaw:

1. Mouth plane: through the lip line read off the bind pose, MOUTH_A (front lip) and MOUTH_B (corner), 'y,z'. MM9's
   jaw labels cannot place it: the HD muzzle is shorter than MM9's and its chin sits above the MM9 jaw pivot.
2. Slit: the muzzle faces in front of the corners are bisected by that plane; the cut edges are split, except at the
   two corners (hinge at the corners).
3. Lips: within LIP_R of the slit, upper-side vertices hand their jaw share to the skull and lower-side vertices their
   skull share to the jaw (smooth ramp), so the lips part cleanly.
4. Cavity: K rings behind the slit loop, each the loop shrunk toward the mouth axis and pushed back along the lips
   by up to CAV_L, the roof raised CAV_H and the floor dropped CAV_F, closed by a cap (the throat). Ring weights: the source lip
   vertex's weights, blending toward an even skull/jaw hinge at the throat. A tongue bulge raises the floor middle.
   At rest the upper and lower halves coincide (closed mouth); the jaw opens them into a wedge.
Attributes for the paint: face int 'cavity' (1), vertex floats 'cav_t' (0 lips .. 1 throat), 'cav_low' (0 roof, 1
floor), 'cav_x' (0 midline .. 1 corner).

Args: <in blend> <out blend> <report json>
Env: MOUTH_A, MOUTH_B, CAV_L (0.12), CAV_H (0.03), CAV_F (0.012), RINGS (6), LIP_R (0.05), JAW_FADE (0.1),
SHRINK (0.45), TONGUE (0.6)
"""
import bpy, bmesh, sys, os, json, math
import numpy as np
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rigcfg

argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, REP = argv[:3]
DEPTH = 1.0
K = int(os.environ.get('RINGS', '6'))
LIP_R = float(os.environ.get('LIP_R', '0.05'))
SHRINK = float(os.environ.get('SHRINK', '0.45'))
TONGUE = float(os.environ.get('TONGUE', '0.6'))
CAV_H = float(os.environ.get('CAV_H', '0.03'))
CAV_F = float(os.environ.get('CAV_F', '0.012'))
bpy.ops.wm.open_mainfile(filepath=IN)
arm = bpy.data.objects['MM9_Rig']
ob = bpy.data.objects['Body']
me = ob.data
gi = {g.name: g.index for g in ob.vertex_groups}
SK = gi[rigcfg.SKULL]
JAWS = [gi[b] for b in rigcfg.JAW_BONES if b in gi]
JMAIN = gi[rigcfg.JAW_BONES[-1]] if rigcfg.JAW_BONES[-1] in gi else JAWS[0]
HEADS = [gi[b] for b in rigcfg.HEAD_BONES if b in gi]
jaw_piv = Vector(arm.data.bones[rigcfg.JAW_BONES[0]].head_local)

bm = bmesh.new()
bm.from_mesh(me)
bm.faces.layers.int.new('cavity')          # layers first: adding one later invalidates the element references
bm.verts.layers.float.new('cav_t'); bm.verts.layers.float.new('cav_low'); bm.verts.layers.float.new('cav_x')
fl = bm.faces.layers.int.get('cavity')
lt = bm.verts.layers.float.get('cav_t'); lw = bm.verts.layers.float.get('cav_low'); lx = bm.verts.layers.float.get('cav_x')
dl = bm.verts.layers.deform.active
pl = bm.verts.layers.int.get('piece')
cl = bm.verts.layers.int.get('chain')
bm.verts.ensure_lookup_table()


def wsum(v, groups):
    d = v[dl]
    return sum(d.get(g, 0.0) for g in groups)


# 0. optional muzzle deepening (the cow's Meshy muzzle is a pointed wedge; cattle have a deep blunt one): vertices
# ramp in from y0 to y1 and scale about the height z0 and the mid plane
if os.environ.get('MUZZLE'):
    y0, y1, z0, zs, xs_ = (float(x) for x in os.environ['MUZZLE'].split(','))
    xmid = sum(v.co.x for v in bm.verts) / len(bm.verts)
    for v in bm.verts:
        if wsum(v, HEADS) < 0.3 or (pl and v[pl] != 0):
            continue
        a = max(0.0, min(1.0, (y0 - v.co.y) / (y0 - y1)))
        a = a * a * (3 - 2 * a)
        v.co.z = z0 + (v.co.z - z0) * (1 + (zs - 1) * a)
        v.co.x = xmid + (v.co.x - xmid) * (1 + (xs_ - 1) * a)
# 1. plane: through the lip line read off the bind pose (side view): A front lip, B mouth corner, each 'y,z'
Ay, Az = (float(x) for x in os.environ['MOUTH_A'].split(','))
By, Bz = (float(x) for x in os.environ['MOUTH_B'].split(','))
A = Vector((0, Ay, Az)); Bp = Vector((0, By, Bz))
bdir = (Bp - A).normalized()                        # along the lips, from the front to the corners
nrm = Vector((0, -bdir.z, bdir.y))
if nrm.z < 0:
    nrm = -nrm
d0 = -nrm.dot(A)


def f(p):   # signed distance to the mouth plane, + = skull side
    return nrm.dot(p) + d0


tip = A.copy()
y_corner = By
in_front = lambda p: p.y < y_corner
plane_co = A

# 2. bisect the muzzle faces (faces touching the head, crossing the plane, in front of the corners)
faces = [fc for fc in bm.faces if any(in_front(v.co) for v in fc.verts)
         and min(f(v.co) for v in fc.verts) < 0 < max(f(v.co) for v in fc.verts)
         and all(wsum(v, HEADS) > 0.3 for v in fc.verts) and (not pl or all(v[pl] == 0 for v in fc.verts))]
geom = list({e for fc in faces for e in fc.edges}) + faces + list({v for fc in faces for v in fc.verts})
res = bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-6, plane_co=plane_co, plane_no=nrm)
cut = [e for e in res['geom_cut'] if isinstance(e, bmesh.types.BMEdge)]
# the slit: cut edges fully in front of the corner plane (the corner vertices stay joined)
slit = [e for e in cut if all(in_front(v.co) for v in e.verts)]
# keep the connected chain through the muzzle tip
from collections import defaultdict
adj = defaultdict(list)
for e in slit:
    a, b = e.verts
    adj[a].append(e); adj[b].append(e)
start = min({v for e in slit for v in e.verts}, key=lambda v: (v.co - tip).length)
chain, seen, st = set(), {start}, [start]
while st:
    v = st.pop()
    for e in adj[v]:
        chain.add(e)
        o = e.other_vert(v)
        if o not in seen:
            seen.add(o); st.append(o)
slit = list(chain)
ends = [v for v in seen if len(adj[v]) == 1]
slit_keys = {tuple(round(c, 5) for c in v.co) for e in slit for v in e.verts}
bmesh.ops.split_edges(bm, edges=slit)
bm.verts.ensure_lookup_table()
bm.edges.ensure_lookup_table()
# 3. the hole's boundary loop
bnd = [e for e in bm.edges if e.is_boundary and all(tuple(round(c, 5) for c in v.co) in slit_keys for v in e.verts)]
loopv = {v for e in bnd for v in e.verts}
# order the loop
start = next(iter(loopv))
order = [start]
prev = None
while True:
    v = order[-1]
    nxt = [e.other_vert(v) for e in v.link_edges if e.is_boundary and e.other_vert(v) != prev]
    nxt = [w for w in nxt if w in loopv]
    if not nxt or nxt[0] == order[0]:
        break
    prev = v
    order.append(nxt[0])
    if len(order) > len(loopv) + 2:
        break
m = len(order)


def side(v):   # +1 upper (skull face), -1 lower
    fcs = [fc for fc in v.link_faces]
    c = sum((fc.calc_center_median() for fc in fcs), Vector()) / len(fcs)
    return 1 if f(c) > 0 else -1


sides = [side(v) for v in order]
lip_upper = {v for v, s in zip(order, sides) if s > 0}
lip_lower = {v for v, s in zip(order, sides) if s < 0}


def above(v):   # on the plane the sign of f is noise: the lip loop knows its side
    return v in lip_upper or (v not in lip_lower and f(v.co) > 0)


# lips part: re-split skull/jaw shares near the slit
slit_pts = [v.co.copy() for v in order]
for v in bm.verts:
    if pl and v[pl] != 0:
        continue
    dmin = min((v.co - p).length for p in slit_pts)
    if dmin > LIP_R or v.co.y > y_corner + LIP_R:
        continue
    a = 1.0 - dmin / LIP_R
    a = a * a * (3 - 2 * a)
    if v.co.y > y_corner:   # fade out behind the corners
        a *= max(0.0, 1.0 - (v.co.y - y_corner) / LIP_R)
    d = v[dl]
    if above(v):
        mv = sum(d.get(g, 0.0) for g in JAWS) * a
        for g in JAWS:
            if g in d:
                d[g] *= (1 - a)
        d[SK] = d.get(SK, 0.0) + mv
    else:
        mv = sum(w for g, w in d.items() if g not in JAWS) * a
        for g in list(d.keys()):
            if g not in JAWS:
                d[g] *= (1 - a)
        d[JMAIN] = d.get(JMAIN, 0.0) + mv
# lower jaw: everything below the lip plane in front of the corners follows the jaw, fading out behind them
JAW_FADE = float(os.environ.get('JAW_FADE', '0.1'))
for v in bm.verts:
    if above(v):
        continue
    a = min(1.0, max(0.0, (y_corner + JAW_FADE - v.co.y) / JAW_FADE))
    a = a * a * (3 - 2 * a)
    a *= min(1.0, -f(v.co) / LIP_R * 2 + 0.6) if v.co.y > y_corner else 1.0
    if v.co.z > Bz + 0.06 or a <= 0:          # never the skull above the corners
        continue
    d = v[dl]
    mv = sum(w for g, w in d.items() if g != JMAIN) * a
    for g in list(d.keys()):
        if g != JMAIN:
            d[g] *= (1 - a)
    d[JMAIN] = d.get(JMAIN, 0.0) + mv
# 4. the cavity
c0 = sum((v.co for v in order), Vector()) / m
L = float(os.environ.get('CAV_L', '0.12'))
mid_plane_x = sum(v.co.x for v in order) / m
xs = [abs(v.co.x - mid_plane_x) for v in order]
xmax = max(xs) or 1.0
rings = [order]
for v, s in zip(order, sides):
    v[lt] = 0.0; v[lw] = 0.0 if s > 0 else 1.0; v[lx] = abs(v.co.x - mid_plane_x) / xmax
hinge = {SK: 0.5, JMAIN: 0.5}
for k in range(1, K + 1):
    t = k / K
    ring = []
    cen = c0 + bdir * (DEPTH * L * t)
    r = 1.0 - (1.0 - SHRINK) * t
    for v, s, xr in zip(order, sides, xs):
        p = cen + (v.co - c0) * r
        p.x = mid_plane_x + (v.co.x - mid_plane_x) * r
        # cavity height: the roof rises into the skull and the floor drops into the jaw behind the lips (a real
        # volume even when closed); the floor's middle keeps a tongue (TONGUE share of the drop)
        prof = math.sin(0.5 * math.pi * min(1.0, t / 0.35))
        if s > 0:
            p += nrm * (CAV_H * prof)
        else:
            mid = max(0.0, 1.0 - xr / xmax / 0.75)
            p -= nrm * (CAV_F * prof * (1.0 - TONGUE * mid))
        nv = bm.verts.new(p)
        src_w = dict(v[dl])
        b = t * t * (3 - 2 * t)
        w = {}
        for g, wt in src_w.items():
            w[g] = w.get(g, 0.0) + wt * (1 - b)
        for g, wt in hinge.items():
            w[g] = w.get(g, 0.0) + wt * b
        for g, wt in w.items():
            if wt > 1e-4:
                nv[dl][g] = wt
        if pl:
            nv[pl] = 0
        if cl:
            nv[cl] = -1
        nv[lt] = t; nv[lw] = 0.0 if s > 0 else 1.0; nv[lx] = xr / xmax
        ring.append(nv)
    rings.append(ring)
newf = []
for k in range(K):
    A, B = rings[k], rings[k + 1]
    for i in range(m):
        j = (i + 1) % m
        try:
            fc = bm.faces.new((A[i], A[j], B[j], B[i]))
        except ValueError:
            continue
        newf.append(fc)
# throat cap: strip-triangulated across the last ring (upper half to lower half)
last = rings[-1]
up = [i for i in range(m) if sides[i] > 0]
lo = [i for i in range(m) if sides[i] < 0]
cap = bmesh.ops.contextual_create(bm, geom=[bm.edges.get((last[i], last[(i + 1) % m])) for i in range(m)])
newf += [g for g in cap['faces']]
for fc in newf:
    fc[fl] = 1
    fc.smooth = True
# winding: one closed skin (body + pocket) -> consistent outward normals per connected part
body_faces = [fc for fc in bm.faces if not pl or all(v[pl] == 0 for v in fc.verts)]
bmesh.ops.recalc_face_normals(bm, faces=body_faces)
bmesh.ops.triangulate(bm, faces=[fc for fc in bm.faces if len(fc.verts) > 3], quad_method='BEAUTY', ngon_method='BEAUTY')
bm.normal_update()
# normalise weights of every touched vertex, limit 4
for v in bm.verts:
    d = v[dl]
    items = sorted(d.items(), key=lambda x: -x[1])[:4]
    tot = sum(w for _, w in items)
    d.clear()
    for g, w in items:
        if w / tot > 0.01:
            d[g] = w / tot
bm.to_mesh(me)
bm.free()
rep = {'plane_normal': list(nrm), 'tip': list(tip), 'y_corner': y_corner,
       'slit_edges': len(slit), 'loop_verts': m, 'upper': len(lip_upper), 'lower': len(lip_lower), 'ends': len(ends),
       'cavity_faces': sum(1 for p in me.polygons if me.attributes['cavity'].data[p.index].value == 1),
       'faces': len(me.polygons)}
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1, default=float)
print('MOUTH', json.dumps(rep, default=float))
