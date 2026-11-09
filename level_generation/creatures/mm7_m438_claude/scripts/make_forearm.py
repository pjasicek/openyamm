"""The zombie's held prop: his own severed RIGHT forearm (native m438sa*/a*: held in the LEFT fist by the wrist, the
bloody elbow end forward as the club head, the limp hand behind the fist). Built from our mesh, so it matches the
body: the LEFT forearm and hand of the step1 skin (piece 0, beyond 3 cm below the left elbow along the arm, within
13 cm of the elbow -> fingertip line), mirrored to a right forearm; the elbow cut is capped (the cap is the wound,
coloured at the texture step). The grip zone (+-7 cm around the grip centre) is squeezed radially to the solved
fist's handle radius (GRIP_R, default R_HANDLE 0.030 m), blended out over 4 cm.
Prop space (read by prop_frame.py, export_runtime.py, the gates): origin at the grip centre, GRIP_BACK (4 cm) up the
forearm from the severed wrist; +Y along the forearm toward the elbow cut (the club head); +X toward the severed
thumb side; +Z = X x Y (the back of the severed hand).
Writes work/props.blend ('ForearmMesh', face attribute 'cap') and work/forearm.json. Args: -- <rest blend with Body>"""
import bpy, bmesh, sys, os, json, math
import numpy as np
from mathutils import Vector, Matrix
blend = sys.argv[sys.argv.index('--') + 1]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = lambda *p: os.path.join(HERE, *p)
GRIP_R = float(os.environ.get('GRIP_R', os.environ.get('R_HANDLE', '0.030')))
GRIP_BACK = 0.04
J = {k: np.array(v) for k, v in json.load(open(R('work', 'joints_final.json')))['joints'].items()}
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
body = bpy.data.objects['Body']; me = body.data
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
co = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices])
el, wr = J['L_Forearm'], J['L_Hand']
d = (wr - el) / np.linalg.norm(wr - el)
tip = co[(pv == 0) & (co[:, 0] > 0.2)]; tip = tip[np.argmax((tip - el) @ d)]        # farthest skin point down the arm
ax = (tip - el) / np.linalg.norm(tip - el)
t = (co - el) @ d
rad = np.linalg.norm((co - el) - np.outer((co - el) @ ax, ax), axis=1)
sel = (pv == 0) & (co[:, 0] > 0) & (t > -0.04) & (rad < 0.13)   # past the elbow: the planar cut below removes the ragged selection edge
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
for dl in list(bm.verts.layers.deform.values()):              # the body's arm weights must not ride along: the prop is
    bm.verts.layers.deform.remove(dl)                           # skinned 100 % to its own bone later
bmesh.ops.delete(bm, geom=[f for f in bm.faces if not all(sel[v.index] for v in f.verts)], context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
# keep the largest connected piece (stray thigh-skin islands, if any)
comp, seen = [], set()
for v in bm.verts:
    if v in seen:
        continue
    st, c = [v], []
    while st:
        x = st.pop()
        if x in seen:
            continue
        seen.add(x); c.append(x); st.extend(e.other_vert(x) for e in x.link_edges)
    comp.append(c)
big = max(comp, key=len)
bmesh.ops.delete(bm, geom=[v for c in comp if c is not big for v in c], context='VERTS')
# mirror to the right arm: x -> -x, faces reversed
for v in bm.verts:
    v.co.x = -v.co.x
bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
# cap the elbow cut (the only boundary loop) - user review 2026-10-20: the flat fan read as a faceted red block. Now a
# ragged rounded wound: three inner rings shrinking toward the loop centre and bulging out along the arm (radial and
# axial jitter), a centre vertex, and the two broken bones (bone_stub.two_bones, as on the body's stump) out of it.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bone_stub
mwr = wr * np.array([-1, 1, 1]); mel = el * np.array([-1, 1, 1])
nax = (mel - mwr) / np.linalg.norm(mel - mwr)
# a clean planar cut 4.5 cm below the elbow (the face selection left a zigzag boundary that the rings bridged with long
# slivers up the arm)
bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=Vector(mel - nax * 0.045),
                       plane_no=Vector(nax), clear_outer=True)
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])   # the bisect leaves n-gons
bl = [e for e in bm.edges if e.is_boundary]
adj = {}
for e in bl:
    a_, b_ = e.verts; adj.setdefault(a_, []).append(b_); adj.setdefault(b_, []).append(a_)
loops, seen = [], set()
for st in adj:
    if st in seen:
        continue
    lp = [st]; seen.add(st); prev = None
    while True:
        nxt = [x for x in adj[lp[-1]] if x is not prev and (x not in seen or x is lp[0])]
        if not nxt or nxt[0] is lp[0]:
            break
        prev = lp[-1]; lp.append(nxt[0]); seen.add(nxt[0])
    loops.append(lp)
# the cut is the loop farthest along the arm; any other small opening of the extracted skin is filled flat (skin)
cutpos = [float(np.mean([np.array(v.co) @ nax for v in lp])) for lp in loops]
loop = loops[int(np.argmax(cutpos))]
others = [lp for i, lp in enumerate(loops) if i != int(np.argmax(cutpos))]
for lp in others:
    es = [e for e in bl if e.verts[0] in set(lp) and e.verts[1] in set(lp)]
    r_ = bmesh.ops.holes_fill(bm, edges=es, sides=0); bmesh.ops.triangulate(bm, faces=list(r_['faces']))
print('CAPLOOPS', len(loops), 'cut loop verts', len(loop), 'other openings filled', [len(lp) for lp in others])
L0 = np.array([tuple(v.co) for v in loop]); c = L0.mean(0)
rng = np.random.default_rng(4380)
for v in loop:                                                  # a torn rim, not a clean saw cut: +-5 mm along the arm
    d_ = np.array(v.co) - c
    v.co = Vector(c + d_ * (1 + rng.uniform(-0.03, 0.06)) + nax * rng.uniform(-0.005, 0.005))
rings = [loop]
for s_, h_ in ((0.74, 0.005), (0.48, 0.010), (0.22, 0.013)):
    ring = []
    for v in loop:
        p_ = c + (np.array(v.co) - c) * s_ * (1 + rng.uniform(-0.1, 0.1)) + nax * (h_ + rng.uniform(-0.003, 0.003))
        ring.append(bm.verts.new(p_))
    rings.append(ring)
cen = bm.verts.new(c + nax * 0.014)
capf = []
n_ = len(loop)
for r0, r1 in zip(rings[:-1], rings[1:]):
    for k in range(n_):
        k1 = (k + 1) % n_
        capf.append(bm.faces.new((r0[k], r0[k1], r1[k1]))); capf.append(bm.faces.new((r0[k], r1[k1], r1[k])))
for k in range(n_):
    capf.append(bm.faces.new((rings[-1][k], rings[-1][(k + 1) % n_], cen)))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
FJ0 = json.load(open(R('work', 'finger_joints.json')))['L']
across0 = np.array(FJ0['B_L_Finger02_tip']) * np.array([-1, 1, 1]) - mwr     # thumb side: radius and ulna side by side
bonef = []
for V, F in bone_stub.two_bones(c + nax * 0.006, nax, across0, seed=4381):
    vs = [bm.verts.new(p_) for p_ in V]
    for f in F:
        bonef.append(bm.faces.new([vs[i] for i in f]))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])        # every shell closed: outward
# frame: severed wrist = mirrored left wrist; +Y toward the elbow; +X toward the severed thumb
Y = (mel - mwr) / np.linalg.norm(mel - mwr)
P = np.array([tuple(v.co) for v in bm.verts])
hand = P[((P - mwr) @ Y) < -0.02]
thumb_side = hand[np.argmax(np.linalg.norm((hand - mwr) - np.outer((hand - mwr) @ Y, Y), axis=1))]
FJ = json.load(open(R('work', 'finger_joints.json')))['L']
th = np.array(FJ['B_L_Finger02_tip']) * np.array([-1, 1, 1])
X = th - mwr; X = X - Y * (X @ Y); X /= np.linalg.norm(X)
Z = np.cross(X, Y)
O = mwr + Y * GRIP_BACK
Mw = np.column_stack([X, Y, Z])
for v in bm.verts:
    v.co = Vector(Mw.T @ (np.array(v.co) - O))
# squeeze the grip zone to the handle radius
P = np.array([tuple(v.co) for v in bm.verts])
ring = P[np.abs(P[:, 1]) < 0.01]
r0 = float(np.median(np.linalg.norm(ring[:, [0, 2]], axis=1)))
k = min(1.0, GRIP_R / r0)
for v in bm.verts:
    y = abs(v.co.y)
    w = 1.0 if y < 0.07 else max(0.0, 1 - (y - 0.07) / 0.04)
    s = 1 - (1 - k) * w
    v.co.x *= s; v.co.z *= s
bm.faces.ensure_lookup_table()
capset, boneset = set(capf), set(bonef)
capflags = [f in capset for f in bm.faces]; boneflags = [f in boneset for f in bm.faces]
pm = bpy.data.meshes.new('ForearmMesh'); bm.to_mesh(pm)
ncap = int(sum(capflags))
cap = pm.attributes.new('cap', 'BOOLEAN', 'FACE'); cap.data.foreach_set('value', capflags)
bp = pm.attributes.new('bonepart', 'BOOLEAN', 'FACE'); bp.data.foreach_set('value', boneflags)
bm.free()
for p in pm.polygons:
    p.use_smooth = True
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
ob = bpy.data.objects.new('ForearmMesh', pm); bpy.context.scene.collection.objects.link(ob)
P = np.array([tuple(v.co) for v in pm.vertices])
info = {'grip_radius_m': GRIP_R, 'grip_ring_radius_before_m': r0, 'squeeze': k, 'grip_back_m': GRIP_BACK,
        'y_min_m': float(P[:, 1].min()), 'y_max_m': float(P[:, 1].max()), 'tris': sum(len(p.vertices) - 2 for p in pm.polygons),
        'cap_tris': ncap, 'bone_tris': int(sum(boneflags))}
json.dump(info, open(R('work', 'forearm.json'), 'w'), indent=1)
print('PROP forearm', json.dumps(info))
bpy.ops.wm.save_as_mainfile(filepath=R('work', 'props.blend'))
