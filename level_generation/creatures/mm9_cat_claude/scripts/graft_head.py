"""Replace the cat's head (Smart Topology v2: lumpy, no eyeballs, whisker debris) with the head-only Smart Topology
(references_head/). Dense stage, before weights: the two closed shells are united by the voxel remesher, so there is no
seam, loft or second material.

Args: <sym blend> <head glb> <out blend> <report json>   env: SCALE (x MM9 ear spacing), CUT (position along the neck
A -> C line, 0..1), STUB (head neck stub kept, fraction of the head length behind the ears), VOX, SEAM (relax band),
PITCH (extra degrees)
1. Head: the main shell, ear shells and eye pieces; turned by the yaw and roll that make it mirror-symmetric, mirrored.
2. Placed by landmarks against the MM9 head (posed = bind for neck and head): scale from the ear-tip spacing, pitch from
   nose -> ear midpoint, position so both midpoints coincide.
3. Body cut by a plane across the neck, its ring and the stub capped, both voxelised together; eyes stay separate
   pieces. A band around the junction is relaxed. 'chain' is carried over from the nearest old vertex."""
import bpy, bmesh, sys, os, json, math
import numpy as np
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree

argv = sys.argv[sys.argv.index('--') + 1:]
IN, HEADGLB, OUT, REP = argv
SCALE = float(os.environ.get('SCALE', '1.0'))
CUT = float(os.environ.get('CUT', '0.5'))
STUB = float(os.environ.get('STUB', '0.75'))
VOX = float(os.environ.get('VOX', '0.0013'))
SEAM = float(os.environ.get('SEAM', '0.016'))
PITCH = float(os.environ.get('PITCH', '0'))
rep = {}
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']
rig = bpy.data.objects['MM9_Rig']
me = body.data
co_b = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices])
chain = np.array([d.value for d in me.attributes['chain'].data])
J = {b.name: np.array(tuple(rig.pose.bones[b.name].head)) for b in rig.data.bones}
mm9 = next(o for o in bpy.data.objects if o.type == 'MESH' and o.name != 'Body')
lab = np.array([mm9.vertex_groups[max(v.groups, key=lambda g: g.weight).group].name for v in mm9.data.vertices])
dg = bpy.context.evaluated_depsgraph_get()
em = mm9.evaluated_get(dg).to_mesh()
A = np.array([tuple(mm9.matrix_world @ v.co) for v in em.vertices])
mm9.evaluated_get(dg).to_mesh_clear()
ear_r = A[lab == 'Xear01'].mean(0); ear_l = A[lab == 'Xear'].mean(0)
hv = A[lab == 'Xhead']
nose_m = hv[hv[:, 1].argmin()]
nose_m = np.array([0.0, nose_m[1], hv[hv[:, 1] < hv[:, 1].min() + 0.003, 2].mean()])
ear_m = (ear_l + ear_r) / 2
rep['mm9'] = {'nose': nose_m.round(4).tolist(), 'ear_mid': ear_m.round(4).tolist(), 'ear_spacing': float(np.linalg.norm(ear_l - ear_r))}

# ---------------- head model
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=HEADGLB)
hobj = next(o for o in bpy.data.objects if o not in before and o.type == 'MESH')
bm = bmesh.new(); bm.from_mesh(hobj.data); bm.transform(hobj.matrix_world)
for o in [o for o in bpy.data.objects if o not in before]:
    bpy.data.objects.remove(o)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
bm.verts.ensure_lookup_table()


def comps(b):
    b.verts.ensure_lookup_table()
    seen, out = set(), []
    for v in b.verts:
        if v.index in seen:
            continue
        c, st = [], [v]; seen.add(v.index)
        while st:
            x = st.pop(); c.append(x)
            for e in x.link_edges:
                y = e.other_vert(x)
                if y.index not in seen:
                    seen.add(y.index); st.append(y)
        out.append(c)
    out.sort(key=len, reverse=True)
    return out


cs = comps(bm)
P = np.array([tuple(v.co) for v in bm.verts])
rep['head_comps'] = [(len(c), np.round(P[[v.index for v in c]].min(0), 3).tolist(), np.round(P[[v.index for v in c]].max(0), 3).tolist()) for c in cs[:12]]
main = P[[v.index for v in cs[0]]]
rng = np.random.default_rng(0)
Hs = main[rng.choice(len(main), 2500, replace=False)]
c0 = Hs.mean(0)


def kd(X):
    k = KDTree(len(X))
    for i, p in enumerate(X):
        k.insert(Vector(p), i)
    k.balance()
    return k


def asym(yaw, roll):
    Ry = np.array(Matrix.Rotation(math.radians(yaw), 3, 'Z'))
    Rr = np.array(Matrix.Rotation(math.radians(roll), 3, 'Y'))
    X = (Hs - c0) @ (Rr @ Ry).T
    k = kd(X)
    cx = 0.0
    for _ in range(3):
        M = X.copy(); M[:, 0] = 2 * cx - M[:, 0]
        idx = np.array([k.find(Vector(m))[1] for m in M])
        cx = float(((X[idx, 0] + X[:, 0]) / 2).mean())
    M = X.copy(); M[:, 0] = 2 * cx - M[:, 0]
    return float(np.mean([k.find(Vector(m))[2] for m in M])), cx


cand = [(asym(y, r)[0], y, r) for y in np.arange(-12, 12.1, 2.0) for r in np.arange(-8, 8.1, 2.0)]
_, y0, r0 = min(cand)
cand = [(asym(y, r)[0], y, r) for y in np.arange(y0 - 2, y0 + 2.1, 0.5) for r in np.arange(r0 - 2, r0 + 2.1, 0.5)]
dbest, yb, rb = min(cand)
cx = asym(yb, rb)[1]
Rsym = Matrix.Rotation(math.radians(rb), 3, 'Y') @ Matrix.Rotation(math.radians(yb), 3, 'Z')
for v in bm.verts:
    q = Rsym @ (v.co - Vector(c0))
    q.x -= cx
    v.co = q
rep['head_sym'] = {'yaw': yb, 'roll': rb, 'mirror_dist': dbest}
# neck stub cap, then the mirror (right half kept)
boundary_loops = 0
for _ in range(10):
    nm = [v for v in bm.verts if not v.is_manifold]
    if not nm:
        break
    bmesh.ops.delete(bm, geom=nm, context='VERTS')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')


def fan_fill(b):
    used, n = set(), 0
    for e0 in [e for e in b.edges if len(e.link_faces) == 1]:
        if e0 in used:
            continue
        loop, e, v = [], e0, e0.verts[0]
        while e not in used:
            used.add(e); loop.append(v)
            v = e.other_vert(v)
            nxt = [x for x in v.link_edges if len(x.link_faces) == 1 and x not in used]
            if not nxt:
                break
            e = nxt[0]
        if len(loop) < 3:
            continue
        cen = b.verts.new(sum((x.co for x in loop), Vector()) / len(loop))
        for k in range(len(loop)):
            try:
                b.faces.new((loop[k], loop[(k + 1) % len(loop)], cen))
            except ValueError:
                pass
        n += 1
    bmesh.ops.recalc_face_normals(b, faces=b.faces)
    return n


rep['head_filled'] = fan_fill(bm)
# drop the small shells: keep main, ears (touch the skull), eyes (recognised by position in front of the skull)
cs = comps(bm)
keep = []
eyes = []
for c in cs:
    p = np.array([tuple(v.co) for v in c])
    if len(c) > 400:
        keep.append(c)
    elif len(c) > 120 and np.ptp(p[:, 2]) < 0.12 and np.ptp(p[:, 1]) < 0.15:
        eyes.append(c)
drop = [v for c in cs if c not in keep and c not in eyes for v in c]
rep['head_keep'] = [len(c) for c in keep]; rep['head_eyes'] = [len(c) for c in eyes]; rep['head_dropped'] = len(drop)
bmesh.ops.delete(bm, geom=drop, context='VERTS')
eye_set = set(v for c in eyes for v in c)
bm.verts.ensure_lookup_table()
# landmarks in the symmetric head frame
Pm = np.array([tuple(v.co) for c in keep for v in c])
nose_h = Pm[Pm[:, 1].argmin()]
top = Pm[Pm[:, 0] > 0.1]; ear_h = top[top[:, 2].argmax()]
ear_mid_h = np.array([0.0, ear_h[1], ear_h[2]])
nose_h = np.array([0.0, nose_h[1], nose_h[2]])
s = SCALE * rep['mm9']['ear_spacing'] / (2 * abs(ear_h[0]))
a_h = math.atan2(ear_mid_h[2] - nose_h[2], ear_mid_h[1] - nose_h[1])
a_m = math.atan2(ear_m[2] - nose_m[2], ear_m[1] - nose_m[1])
pitch = a_m - a_h + math.radians(PITCH)
Rp = Matrix.Rotation(pitch, 3, 'X')
mid_h = (nose_h + ear_mid_h) / 2
mid_m = (nose_m + ear_m) / 2
rep['place'] = {'scale': s, 'pitch_deg': math.degrees(pitch), 'ear_h': ear_h.round(3).tolist(), 'nose_h': nose_h.round(3).tolist()}
L_h = float(np.linalg.norm(ear_mid_h - nose_h))
for v in bm.verts:
    v.co = Vector(mid_m) + (Rp @ (v.co - Vector(mid_h))) * s
# stub: everything further than STUB x (nose -> ear) x s behind the ears along the head's down-back axis goes
Plan = Rp @ Vector((0, 0.35, -0.94))
bmesh.ops.symmetrize(bm, input=bm.verts[:] + bm.edges[:] + bm.faces[:], direction='-X', dist=1e-5)
hmesh = bpy.data.meshes.new('HeadShell'); bm.to_mesh(hmesh)
# ---------------- separate eyes from the shell after the mirror
b2 = bmesh.new(); b2.from_mesh(hmesh)
cs2 = comps(b2)
eye_part, skin_part = [], []
for c in cs2:
    (eye_part if len(c) < 400 else skin_part).append(c)
rep['after_mirror'] = {'skin': [len(c) for c in skin_part], 'eyes': [len(c) for c in eye_part]}
# clean eyeballs: the Meshy eye shells are irregular; a sphere fitted to each (centre of its bounds, half the mean extent)
eset = set(v.index for c in eye_part for v in c)
b_eye = bmesh.new()
rep['eyes'] = []
for c in eye_part:
    p_ = np.array([tuple(v.co) for v in c])
    cen = (p_.max(0) + p_.min(0)) / 2
    r_ = float(np.ptp(p_, axis=0).mean() / 2) * float(os.environ.get('EYE_R', '1.0'))
    bmesh.ops.create_uvsphere(b_eye, u_segments=16, v_segments=12, radius=r_, matrix=Matrix.Translation(Vector(cen)))
    rep['eyes'].append({'centre': np.round(cen, 4).tolist(), 'radius': round(r_, 4)})
m_eye = bpy.data.meshes.new('Eyes'); b_eye.to_mesh(m_eye); b_eye.free()
bmesh.ops.delete(b2, geom=[v for v in b2.verts if v.index in eset], context='VERTS')
rep['head_open_after'] = sum(1 for e in b2.edges if len(e.link_faces) == 1)
fan_fill(b2)
# ---------------- body: head out
N0, N1 = J['XneckA'], J['XneckC']
U = (N1 - N0) / np.linalg.norm(N1 - N0)
C = N0 + CUT * (N1 - N0)
rep['cut_at'] = C.round(4).tolist()
bb = bmesh.new(); bb.from_mesh(me); bb.transform(body.matrix_world); bb.verts.ensure_lookup_table()
# the neck morphs onto the head stub's section over TAPER behind the cut, so the union has no step
TAPER = float(os.environ.get('TAPER', '0.045'))
Xa = np.array([1.0, 0, 0])
Va = np.cross(U, Xa); Va /= np.linalg.norm(Va)
Pb = np.array([tuple(v.co) for v in bb.verts])
db = (Pb - C) @ U
rad = np.linalg.norm((Pb - C) - db[:, None] * U, axis=1)
ring_b = Pb[(np.abs(db) < 0.004) & (rad < 0.09)]
Ph = np.array([tuple(v.co) for v in b2.verts])
ring_h = Ph[np.abs((Ph - C) @ U) < 0.004]
assert len(ring_h) > 10, 'the head stub does not reach the cut plane'
cb, ch = ring_b.mean(0), ring_h.mean(0)
cb = (ring_b.max(0) + ring_b.min(0)) / 2; ch = (ring_h.max(0) + ring_h.min(0)) / 2
ext = lambda R, c, A_: float(np.abs((R - c) @ A_).max())
fx, fy = ext(ring_h, ch, Xa) / ext(ring_b, cb, Xa), ext(ring_h, ch, Va) / ext(ring_b, cb, Va)
rep['neck'] = {'ring_body': [ext(ring_b, cb, Xa), ext(ring_b, cb, Va)], 'ring_head': [ext(ring_h, ch, Xa), ext(ring_h, ch, Va)],
               'centre_shift': np.round(ch - cb, 4).tolist()}
for v, p_, d_, r_ in zip(bb.verts, Pb, db, rad):
    if -TAPER < d_ <= 0.002 and r_ < 0.09:
        t = min(1.0, 1 + d_ / TAPER)
        t = t * t * (3 - 2 * t)
        q = p_ - cb
        sx, sy = q @ Xa, q @ Va
        v.co = Vector(tuple(p_ + t * ((ch - cb) + Xa * sx * (fx - 1) + Va * sy * (fy - 1))))
# the stub ends just behind the plane (its flat end would stick out of the neck as a ledge)
bmesh.ops.delete(b2, geom=[v for v in b2.verts if (np.array(tuple(v.co)) - C) @ U < -0.004], context='VERTS')
rep['stub_cut_loops'] = fan_fill(b2)
bad = [v for v in bb.verts if (np.array(tuple(v.co)) - C) @ U > 0]
bmesh.ops.delete(bb, geom=bad, context='VERTS')
cs3 = comps(bb)
big = set(cs3[0])
bmesh.ops.delete(bb, geom=[v for v in bb.verts if v not in big], context='VERTS')
rep['body_cut_loops'] = fan_fill(bb)
# ---------------- union: join both, voxel
bb.from_mesh(bpy.data.meshes.new('e')) if False else None
b2.to_mesh(hmesh); b2.free()
tmp = bpy.data.meshes.new('Union'); bb.to_mesh(tmp); bb.free()
u = bpy.data.objects.new('Union', tmp); bpy.context.scene.collection.objects.link(u)
h = bpy.data.objects.new('HeadShell', hmesh); bpy.context.scene.collection.objects.link(h)
for o in bpy.data.objects:
    o.select_set(o in (u, h))
bpy.context.view_layer.objects.active = u
bpy.ops.object.join()
u.data.remesh_voxel_size = VOX
u.data.remesh_voxel_adaptivity = 0.0
bpy.ops.object.voxel_remesh()
b4 = bmesh.new(); b4.from_mesh(u.data)
cs4 = comps(b4)
rep['union_shells'] = [len(c) for c in cs4[:6]]
big = set(cs4[0])
bmesh.ops.delete(b4, geom=[v for v in b4.verts if v not in big], context='VERTS')
b4.to_mesh(u.data); b4.free()
# relax the junction band
mesh = u.data
co = np.array([tuple(v.co) for v in mesh.vertices])
E = np.array([tuple(e.vertices) for e in mesh.edges])
deg = np.maximum(np.bincount(E.ravel(), minlength=len(co)), 1)
d = (co - C) @ U
axis_r = np.linalg.norm((co - C) - d[:, None] * U, axis=1)
w = np.clip(1 - np.abs(d) / SEAM, 0, 1) * (axis_r < 0.08)
P2 = co.copy()
for _ in range(30):
    acc = np.zeros_like(P2)
    np.add.at(acc, E[:, 0], P2[E[:, 1]]); np.add.at(acc, E[:, 1], P2[E[:, 0]])
    P2 = P2 + 0.5 * w[:, None] * (acc / deg[:, None] - P2)
P2[np.abs(co[:, 0]) < 1e-7, 0] = 0
mesh.foreach_set('position', P2.ravel()) if False else None
for v, p in zip(mesh.vertices, P2):
    v.co = Vector(tuple(p))
sm = u.modifiers.new('s', 'SMOOTH'); sm.factor = 0.5; sm.iterations = 1
bpy.context.view_layer.objects.active = u
bpy.ops.object.modifier_apply(modifier='s')
# attributes
k = KDTree(len(co_b))
for i, p in enumerate(co_b):
    k.insert(p, i)
k.balance()
nearest = np.array([k.find(v.co)[1] for v in mesh.vertices])
new_chain = chain[nearest].astype(np.int32)
co_now = np.array([tuple(v.co) for v in mesh.vertices])
new_chain[((co_now - C) @ U > -0.07) & (co_now[:, 1] < -0.02)] = -1   # head and neck are core
mesh.attributes.new('piece', 'INT', 'POINT'); mesh.attributes.new('chain', 'INT', 'POINT')
mesh.attributes['piece'].data.foreach_set('value', np.zeros(len(new_chain), np.int32))
mesh.attributes['chain'].data.foreach_set('value', new_chain)
e = bpy.data.objects.new('Eyes', m_eye); bpy.context.scene.collection.objects.link(e)
m_eye.attributes.new('piece', 'INT', 'POINT'); m_eye.attributes.new('chain', 'INT', 'POINT')
m_eye.attributes['piece'].data.foreach_set('value', np.full(len(m_eye.vertices), 2, np.int32))
m_eye.attributes['chain'].data.foreach_set('value', np.full(len(m_eye.vertices), -1, np.int32))
for o in bpy.data.objects:
    o.select_set(o in (u, e))
bpy.context.view_layer.objects.active = u
bpy.ops.object.join()
mw = body.matrix_world.copy()
bpy.data.objects.remove(body)
u.name = 'Body'; u.data.name = 'Body'
for p in u.data.polygons:
    p.use_smooth = True
rep['verts'] = len(u.data.vertices); rep['faces'] = len(u.data.polygons)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1, default=str)
print('GRAFT ' + json.dumps(rep, default=str)[:1500])
