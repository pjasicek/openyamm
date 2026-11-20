"""The Green Man's staff (mm9_greenman, 2026-11-04): MM9's staff is a 48-triangle stick skinned to Bone01 (a child of
the scene root that the clips key in the R hand; staff_follow.py re-keys it from our hand). A smooth gnarled tube is
built along MM9's own staff centreline (bind pose; slices along its long axis -> centre + radius, Catmull-Rom through
them), RADIAL_SEG sides, with a low-frequency bend noise and a few knots, and joined to 'Body' as head-set faces
(face attribute head = 1, hand = 0) weighted 100 % to Bone01. HeadUV: a vertical strip in the head set's free right
column (u 0.82..0.98, v 0.02..0.58; the head islands fill the lower-left 0.8 square, the hands' squares sit at
(0.8, 0.6) and (0.8, 0.8)) wrapping the circumference once and the length REPEAT times (the bark swatch tiles).
Args: <in blend> <mm9 glb> <out blend> [radius scale 1.0]"""
import bpy, bmesh, sys, math
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
IN, MM9, OUT = a[:3]
RSCALE = float(a[3]) if len(a) > 3 else 1.0
RADIAL_SEG, RINGS, REPEAT = 10, 40, 1.0
U0, U1, V0, V1 = 0.82, 0.98, 0.02, 0.58
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; rig = body.parent
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=MM9)
new = [o for o in bpy.data.objects if o not in before]
arm9 = next(o for o in new if o.type == 'ARMATURE')
if arm9.animation_data:
    arm9.animation_data.action = None
for pb in arm9.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
st = next(o for o in new if o.type == 'MESH' and o.name.startswith('staff'))
dg = bpy.context.evaluated_depsgraph_get()
m = st.evaluated_get(dg).to_mesh()
P = np.array([tuple(st.matrix_world @ v.co) for v in m.vertices])
for o in new:
    bpy.data.objects.remove(o, do_unlink=True)
c = P.mean(0); U = np.linalg.svd(P - c)[2]; ax = U[0]
if ax[2] < 0:
    ax = -ax
t = (P - c) @ ax; t0, t1 = t.min(), t.max(); L = t1 - t0
NS = 4
cents, rads = [], []
for k in range(NS):
    s0 = t0 + L * k / NS; s1 = t0 + L * (k + 1) / NS
    q = P[(t >= s0 - 1e-6) & (t <= s1 + 1e-6)]
    if len(q) < 3:
        continue
    cc = q.mean(0); perp = q - cc - np.outer((q - cc) @ ax, ax)
    cents.append(c + ax * ((s0 + s1) / 2 - 0) + (cc - c - ax * ((cc - c) @ ax)))
    rads.append(np.median(np.linalg.norm(perp, axis=1)))
cents = [c + ax * t0] + cents + [c + ax * t1]
rads = [rads[0]] + rads + [rads[-1]]
cents = np.array(cents); rads = np.array(rads)
r0 = float(np.nanmedian(rads)) * RSCALE
def cr(pts, u):
    n = len(pts) - 1; x = u * n; i = min(int(x), n - 1); f = x - i
    p0, p1, p2, p3 = pts[max(i - 1, 0)], pts[i], pts[i + 1], pts[min(i + 2, n)]
    return 0.5 * ((2 * p1) + (-p0 + p2) * f + (2 * p0 - 5 * p1 + 4 * p2 - p3) * f * f + (-p0 + 3 * p1 - 3 * p2 + p3) * f ** 3)
rng = np.random.default_rng(7)
knots = [(rng.uniform(0.15, 0.85), rng.uniform(0, 2 * math.pi), rng.uniform(0.25, 0.45)) for _ in range(4)]
# the grip (MM9's Bone01 sits at u ~0.54 of the staff): no knots there and the wood worn 10 % thinner, so the fist closes on it
knots = [k if not (0.40 < k[0] < 0.68) else (k[0] - 0.3 if k[0] < 0.54 else k[0] + 0.25, k[1], k[2]) for k in knots]
bm = bmesh.new()
rings = []
up = np.array([0, 0, 1.0])
for i in range(RINGS + 1):
    u = i / RINGS
    p = cr(cents, u); dp = cr(cents, min(u + 0.01, 1)) - cr(cents, max(u - 0.01, 0)); dp /= np.linalg.norm(dp)
    e1 = np.cross(dp, [1.0, 0, 0]); e1 /= np.linalg.norm(e1); e2 = np.cross(dp, e1)
    # taper: thicker at the top, a rounded butt at the foot, a knob at the top
    taper = 0.85 + 0.25 * u
    if u > 0.93:
        taper *= 1.0 + 1.2 * ((u - 0.93) / 0.07) ** 0.5 * (1 - ((u - 0.93) / 0.07) ** 3) * 0.35
    end = min(1.0, math.sin(min(u, 1 - u) / 0.012 * math.pi / 2)) if min(u, 1 - u) < 0.012 else 1.0
    ring = []
    for j in range(RADIAL_SEG):
        th = 2 * math.pi * j / RADIAL_SEG
        r = r0 * taper * (1 + 0.08 * math.sin(3 * th + 11 * u) + 0.05 * math.sin(7 * u * 2 * math.pi + th))
        for ku, kth, kh in knots:
            dth = math.atan2(math.sin(th - kth), math.cos(th - kth))
            r += r0 * kh * math.exp(-((u - ku) / 0.015) ** 2 - (dth / 0.5) ** 2)
        r *= 1 - 0.1 * math.exp(-((u - 0.54) / 0.06) ** 2)
        r *= max(end, 0.35)
        ring.append(bm.verts.new((p + r * (math.cos(th) * e1 + math.sin(th) * e2)).tolist()))
    rings.append(ring)
bm.verts.ensure_lookup_table()
uvl = bm.loops.layers.uv.new('HeadUV'); uvb = bm.loops.layers.uv.new('UVMap')
for i in range(RINGS):
    for j in range(RADIAL_SEG):
        j2 = (j + 1) % RADIAL_SEG
        f = bm.faces.new((rings[i][j], rings[i][j2], rings[i + 1][j2], rings[i + 1][j]))
        for lp, (ii, jj) in zip(f.loops, ((i, j), (i, j + 1), (i + 1, j + 1), (i + 1, j))):
            lp[uvl].uv = (U0 + (U1 - U0) * jj / RADIAL_SEG, V0 + (V1 - V0) * ((ii / RINGS * REPEAT) % 1.0000001))
            lp[uvb].uv = (0.0, 0.0)
for ring, flip in ((rings[0], True), (rings[-1], False)):
    cen = bm.verts.new(tuple(np.mean([np.array(v.co) for v in ring], 0)))
    for j in range(RADIAL_SEG):
        vs = (ring[j], ring[(j + 1) % RADIAL_SEG], cen)
        f = bm.faces.new(vs[::-1] if flip else vs)
        for lp in f.loops:
            lp[uvl].uv = (U0 + 0.02, V0 + 0.01); lp[uvb].uv = (0.0, 0.0)
bmesh.ops.triangulate(bm, faces=list(bm.faces))
bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
sm = bpy.data.meshes.new('staff'); bm.to_mesh(sm); bm.free()
so = bpy.data.objects.new('Staff', sm); bpy.context.scene.collection.objects.link(so)
nf = len(sm.polygons)
for nm in ('head', 'hand'):
    at = sm.attributes.new(nm, 'INT', 'FACE'); at.data.foreach_set('value', [1 if nm == 'head' else 0] * nf)
for l in body.data.uv_layers:
    if l.name not in sm.uv_layers:
        sm.uv_layers.new(name=l.name)
vg = so.vertex_groups.new(name='Bone01'); vg.add(list(range(len(sm.vertices))), 1.0, 'REPLACE')
for p in sm.polygons:
    p.use_smooth = True
so.matrix_world = body.matrix_world.copy()
for o in bpy.data.objects:
    o.select_set(o in (so, body))
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
print('STAFF', {'length_m': round(float(L), 3), 'radius_cm': round(r0 * 100, 2), 'tris': nf, 'axis': np.round(ax, 3).tolist(),
                'bottom': np.round(cents[0], 3).tolist(), 'top': np.round(cents[-1], 3).tolist()})
bpy.ops.wm.save_as_mainfile(filepath=OUT)
