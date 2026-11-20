"""Weights on the UV master, safe to re-run: no vertex or UV moves. Neck: a smooth run along its axis from the torso ring through Xneckbase, Xneck and Xheadpiv into Xhead, on the loft and the head's stump, so the short throat does not fold.
Args: <in blend> <out blend>"""
import bpy, sys, json, os, bmesh
import numpy as np
A = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=A[0])
head = bpy.data.objects['Head']; arm = head.parent
me = head.data
CO = np.array([v.co[:] for v in me.vertices])
hp = np.zeros(len(CO), np.int32); me.attributes['hpart'].data.foreach_get('value', hp)
neck = hp == 5
tc = np.array([0, -0.153, 0.488]); hc = np.array([0, -0.189, 0.531])
ax = np.array([0, -0.6, 0.8]); ax = ax / np.linalg.norm(ax)
gi = head.vertex_groups
for n in ('Xneckbase', 'Xneck', 'Xheadpiv', 'Xhead', 'Xjaw'):
    if n not in gi:
        gi.new(name=n)
neck = hp == 5
tc = np.array([0, -0.153, 0.488]); hc = np.array([0, -0.189, 0.531])
ax = np.array([0, -0.6, 0.8]); ax = ax / np.linalg.norm(ax)
for n in ('Xneckbase', 'Xneck', 'Xheadpiv', 'Xhead', 'Xjaw'):
    if n not in gi:
        gi.new(name=n)
# the strap of skin Meshy left from the ear to the jaw: smoothed away (vertices move a little, UVs stay)
bm0 = bmesh.new(); bm0.from_mesh(me); bm0.verts.ensure_lookup_table()
hl0 = bm0.verts.layers.int.get('hpart')
zone0 = [v for v in bm0.verts if v[hl0] == 0 and abs(v.co.x) > 0.04 and -0.272 < v.co.y < -0.15 and 0.455 < v.co.z < 0.585]
zone0 += [v for v in bm0.verts if v[hl0] == 0 and v not in zone0 and -0.30 < v.co.y < -0.18 and 0.44 < v.co.z < 0.482 and v.normal.z < 0.2]     # the notch between chin and throat
for _ in range(10):
    bmesh.ops.smooth_vert(bm0, verts=zone0, factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
zone1 = [v for v in bm0.verts if v[hl0] in (0, 5) and -0.30 < v.co.y < -0.16 and 0.43 < v.co.z < 0.50 and abs(v.co.x) < 0.07 and v.normal.z < 0.35]      # the crease from jaw to throat
for _ in range(6):
    bmesh.ops.smooth_vert(bm0, verts=zone1, factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
print('STRAP vertices', len(zone0), len(zone1))
bm0.to_mesh(me); bm0.free(); me.update()
CO = np.array([v.co[:] for v in me.vertices])
# jaw: one hinge at the TMJ. The lips part sharply at the centre, the cheeks take the stretch over a wide band toward the corners and behind them (hinge at the mouth corners, no shards)
def ss0(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


TMJ = np.array([0, -0.237, 0.545])
yz = CO[:, 1:3] - TMJ[1:3]
MOUTH = np.array([-0.345, 0.513]) - TMJ[1:3]
a0 = np.arctan2(MOUTH[1], MOUTH[0])
phi = np.degrees((np.arctan2(yz[:, 1], yz[:, 0]) - a0 + np.pi) % (2 * np.pi) - np.pi)
chin = np.degrees((np.arctan2(0.45 - TMJ[2], -0.33 - TMJ[1]) - a0 + np.pi) % (2 * np.pi) - np.pi)
phi = phi * np.sign(chin)
rr = np.linalg.norm(yz, axis=1)
lat = ss0(0.012, 0.04, np.abs(CO[:, 0]))
lo = -3 - 12 * lat; hi = 8 + 30 * lat      # a band of 48 deg on the cheek: at 34 deg of opening it stretches about 1.7 x, not 3 x
wj = np.clip((phi - lo) / (hi - lo), 0, 1)
wj = wj * ss0(0.02, 0.08, rr) * (1 - ss0(70, 105, phi))
gi = head.vertex_groups
for i in np.where(hp == 0)[0]:
    v = me.vertices[int(i)]
    for g in list(v.groups):
        gi[g.group].remove([int(i)])
    w = float(wj[i])
    if w < 1:
        gi['Xhead'].add([int(i)], 1 - w, 'REPLACE')
    if w > 0:
        gi['Xjaw'].add([int(i)], w, 'REPLACE')
s = (CO - tc) @ ax
L = float((CO[neck] - tc) @ ax @ np.ones(1) if False else ((CO[neck] - tc) @ ax).max())
# only shell vertices: the loft and the stump behind the jaw
yfront = -0.262
yfr = yfront + 0.3 * (CO[:, 2] - 0.47)
# how much of the neck run a vertex takes: all on the loft, fading to none up the skull and toward the jaw line, so no edge jumps from the neck's bones to the head's
g_run = np.where(hp == 5, 1.0, (1 - ss0(L + 0.015, L + 0.085, s)) * ss0(0.0, 0.035, CO[:, 1] - yfr))
stops = [(0.0, 'Xneckbase'), (0.34, 'Xneck'), (0.68, 'Xheadpiv'), (1.0, 'Xhead')]
count = 0
for i in np.where(((hp == 5) | (hp == 0)) & (g_run > 1e-3))[0]:
    v = me.vertices[int(i)]
    old = {gi[g.group].name: g.weight for g in v.groups}
    t = float(np.clip(s[i] / (L + 0.075), 0, 1))
    w = {}
    for (a, na), (b, nb) in zip(stops, stops[1:]):
        if a <= t <= b:
            f = (t - a) / (b - a); f = f * f * (3 - 2 * f)
            w[na] = 1 - f; w[nb] = f
    k = float(g_run[i])
    final = {n: x * k for n, x in w.items()}
    for n, x in old.items():
        final[n] = final.get(n, 0) + x * (1 - k)
    for g in list(v.groups):
        gi[g.group].remove([int(i)])
    for n, x in sorted(final.items(), key=lambda t_: -t_[1])[:4]:
        if x > 1e-4:
            gi[n].add([int(i)], x, 'REPLACE')
    count += 1
print('NECK vertices', count, 'L', L)
# the torso's neck ring rides with the neck's last row: Xneckbase on the cut, fading into the chest
body = bpy.data.objects['Body']; mb = body.data
BC = np.array([v.co[:] for v in mb.vertices])
bg = body.vertex_groups
if 'Xneckbase' not in bg:
    bg.new(name='Xneckbase')
P_, N_ = np.array([0, -0.13, 0.505]), np.array([0, -0.6, 0.8])
dd = -((BC - P_) @ N_)


def ss(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


n = 0
for i in np.where((dd < 0.075) & (np.abs(BC[:, 0]) < 0.19))[0]:
    k = float(1 - ss(0.0, 0.075, dd[i]))
    if k <= 0:
        continue
    v = mb.vertices[int(i)]
    old = {bg[g.group].name: g.weight for g in v.groups}
    for g in list(v.groups):
        bg[g.group].remove([int(i)])
    new = {nm: w * (1 - k) for nm, w in old.items() if nm != 'Xneckbase'}
    new['Xneckbase'] = old.get('Xneckbase', 0) * (1 - k) + k
    for nm, w in new.items():
        if w > 1e-4:
            bg[nm].add([int(i)], w, 'REPLACE')
    n += 1
print('RING vertices', n)
# ------------------------------------------------------------- mouth bag: Meshy's mouth is a hole into the hollow head. A dark inner shell (faces inward, open at the lips), upper half on Xhead, lower on Xjaw, mapped onto a dark patch reserved in the head atlas (compose: bag_rect)
rect = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bag_rect.json')))
SZ = 1024
print('BAG rect', rect)
C = np.array([0, -0.292, 0.513]); RX, RY, RZ = 0.056, 0.072, 0.060
NR, NA = 7, 14
verts = []; uvs = []; faces = []
for r in range(NR + 1):
    # r = 0 at the lips' ring, r = NR at the throat pole
    ph = np.radians(68 + (180 - 68) * r / NR)        # angle from the front pole
    for a_ in range(NA):
        th = 2 * np.pi * a_ / NA
        p = C + np.array([RX * np.sin(ph) * np.cos(th), -RY * np.cos(ph), RZ * np.sin(ph) * np.sin(th)])
        verts.append(p); uvs.append((r / NR, 0.5 + 0.45 * np.cos(th) * 0.02))
for r in range(NR):
    for a_ in range(NA):
        a1 = (a_ + 1) % NA
        faces.append((r * NA + a_, r * NA + a1, (r + 1) * NA + a1, (r + 1) * NA + a_))
# the bag stays inside the head in every clip: each vertex pulled in short of the first shell surface seen from the bag's centre, and skinned as the nearest shell vertex
from mathutils import Vector as V_
from mathutils.bvhtree import BVHTree as BT_
me.calc_loop_triangles()
sh_t = [t.vertices[:] for t in me.loop_triangles if hp[list(t.vertices)].max() <= 5 and set(hp[list(t.vertices)].tolist()) <= {0, 5}]
sh_co = [V_(tuple(v.co)) for v in me.vertices]
bvh_s = BT_.FromPolygons(sh_co, sh_t)
cv = V_(C.tolist())
bagw = []
for k_, p in enumerate(verts):
    d_ = V_((p - C).tolist()); r_ = d_.length; d_.normalize()
    hit = bvh_s.ray_cast(cv, d_, 1.0)
    if hit[0] is not None and hit[3] * 0.9 < r_:
        verts[k_] = C + np.array(d_[:]) * (hit[3] * 0.9)
    near = bvh_s.find_nearest(V_(verts[k_].tolist()))
    tri = sh_t[near[2]]
    vi_ = min(tri, key=lambda i_: (sh_co[i_] - near[0]).length)
    bagw.append({gi[g.group].name: g.weight for g in me.vertices[vi_].groups})
bm = bmesh.new()
bm.from_mesh(me)
vs = [bm.verts.new(tuple(float(x) for x in p)) for p in verts]
fs = []
for f in faces:
    ff = bm.faces.new([vs[i] for i in f]); fs.append(ff)
bm.faces.ensure_lookup_table(); bm.verts.ensure_lookup_table(); bm.verts.index_update()
uvl = bm.loops.layers.uv.active
hl = bm.verts.layers.int.get('hpart')
for v in vs:
    v[hl] = 6
# normals inward: facing the bag's centre
for ff in fs:
    if ff.normal.dot(bmesh.types.BMVert.co.__get__(ff.verts[0]) - __import__('mathutils').Vector(C.tolist())) > 0 if False else (np.array(ff.normal[:]) @ (np.array(ff.calc_center_median()[:]) - C)) > 0:
        ff.normal_flip()
for ff in fs:
    for l in ff.loops:
        i = vs.index(l.vert)
        r = i // NA
        l[uvl].uv = ((rect[0] + 2 + (rect[2] - 4) * r / NR) / SZ, 1 - (rect[1] + rect[2] / 2) / SZ)
bm.faces.ensure_lookup_table()
tri = bmesh.ops.triangulate(bm, faces=fs)
newidx = [v.index for v in vs]
bm.to_mesh(me); bm.free(); me.update()
gi = head.vertex_groups
for i, w_ in zip(newidx, bagw):
    for n_, x_ in w_.items():
        gi[n_].add([i], x_, 'REPLACE')
print('BAG verts', len(verts))
# the stitch strip's triangles came out of the unwrap with degenerate UVs (all at 0,0 or a line): tangents are undefined there and the stretched strip shades in stripes. They take a real small triangle on the neck's flat colour
hp2 = np.zeros(len(me.vertices), np.int32); me.attributes['hpart'].data.foreach_get('value', hp2)
uvd = me.uv_layers.active.data
best, area = None, 0.0
for p in me.polygons:
    h_ = hp2[list(p.vertices)]
    if (h_ == 5).all() and (np.mean([CO[v] for v in p.vertices], axis=0) - tc) @ ax > 0.55 * L:
        q = [uvd[l].uv for l in p.loop_indices]
        a_ = abs((q[1][0] - q[0][0]) * (q[2][1] - q[0][1]) - (q[1][1] - q[0][1]) * (q[2][0] - q[0][0])) / 2
        if a_ > area and len(q) == 3:
            best, area = [tuple(x) for x in q], a_
fixed = 0
for p in me.polygons:
    h_ = hp2[list(p.vertices)]
    if h_.max() == 5 and h_.min() == 0:
        for l, q in zip(p.loop_indices, best):
            uvd[l].uv = q
        fixed += 1
print('RING stitch faces with real UVs', fixed, 'donor area', area)
# hair spikes: reshaped in place (topology and weights as assembled): roots narrow and deep in the cap, widest a fifth of the way out
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spikes as SP, lattice as L
from mathutils import Vector
from mathutils.bvhtree import BVHTree
hv_ = [Vector(tuple(head.matrix_world @ v.co)) for v in me.vertices if True]
me.calc_loop_triangles()
bvh_h = BVHTree.FromPolygons(hv_, [t.vertices[:] for t in me.loop_triangles])
lines = SP.spike_lines(np.load(os.path.join(os.path.dirname(A[0]), 'mm9_parts.npz')))
hair = bpy.data.objects['Hair']
RINGN, STN = 5, 7
CEN = np.array([0, -0.22, 0.62])
vi = 0
for s_ in lines:
    pts = s_['points'][::-1]
    root = pts[0]
    hit = np.array(bvh_h.find_nearest(Vector(root.tolist()))[0][:])
    deep = hit + (CEN - hit) * 0.24
    pts = np.vstack([deep, pts[1:]]) if len(pts) > 2 else np.vstack([deep, pts])
    C_, tq = L.resample_arc(pts, STN)
    tang = np.gradient(C_, axis=0); tang /= np.linalg.norm(tang, axis=1, keepdims=True)
    out = C_ - CEN
    for i in range(STN):
        t = i / (STN - 1)
        w_ = 0.027 * (1 - t ** 1.7) * (0.3 + 0.7 * ss0(0.12, 0.5, t)) + 0.0004
        th_ = 0.42 * w_ + 0.0004
        a_ = np.cross(tang[i], out[i]); a_ /= np.maximum(np.linalg.norm(a_), 1e-6)
        b_ = np.cross(a_, tang[i])
        for k in range(RINGN):
            an = 2 * np.pi * k / RINGN
            hair.data.vertices[vi].co = (C_[i] + a_ * w_ * np.cos(an) + b_ * th_ * np.sin(an)).tolist()
            vi += 1
hair.data.update()
print('HAIR vertices', vi, len(hair.data.vertices))
# hair swatch: tips at the image top
ha = bpy.data.objects['Hair'].data
uv_ = ha.uv_layers.active.data
for l in uv_:
    l.uv = (l.uv[0], 1 - l.uv[1])
# the loft's last row onto the torso's own neck ring, tucked just under it, and the rows between straight: last, because nothing below may move them
hp = np.zeros(len(me.vertices), np.int32); me.attributes['hpart'].data.foreach_get('value', hp)
n5 = np.where(hp == 5)[0]
if len(n5) == 168:
    CO = np.array([v.co[:] for v in me.vertices])
    g5 = CO[n5].reshape(6, 28, 3)
    _bm = bmesh.new(); _bm.from_mesh(bpy.data.objects['Body'].data)
    RC = np.array([v.co[:] for v in _bm.verts if v.is_boundary and v.co.z > 0.40 and abs(v.co.y + 0.1) < 0.14 and abs(v.co.x) < 0.12]); _bm.free()
    RC = RC[np.argsort(np.arctan2(RC[:, 0], RC[:, 1] + 0.15))]
    A_, B_ = RC, np.roll(RC, -1, axis=0)
    moved = []
    for j in range(28):
        p_ = g5[5, j].copy()
        t_ = np.clip(((p_ - A_) * (B_ - A_)).sum(1) / np.maximum(((B_ - A_) ** 2).sum(1), 1e-9), 0, 1)
        q_ = A_ + (B_ - A_) * t_[:, None]
        q_ = q_[np.argmin(np.linalg.norm(q_ - p_, axis=1))]
        moved.append(float(np.linalg.norm(q_ - p_)))
        g5[5, j] = q_ - ax * 0.004
    for r in range(1, 6):
        for i_, c_ in zip(n5[r * 28:(r + 1) * 28], g5[0] * (1 - r / 5) + g5[5] * (r / 5)):
            me.vertices[int(i_)].co = c_.tolist()
    me.update()
    print('LOFT snapped, moved max', round(max(moved), 4))
bpy.ops.wm.save_as_mainfile(filepath=A[1])
