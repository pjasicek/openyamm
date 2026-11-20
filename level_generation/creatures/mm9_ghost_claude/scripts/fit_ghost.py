"""Rig the Ghost's jacket + robe on the ORIGINAL MM9 skeleton: bones translated, rest rotations unchanged.
- Sleeves: a clean planar end, two extruded rings into the lace cuff. Arm stretched along its axis to MM9's shoulder-wrist length, so the hands reach where MM9's do
  (fidget2 holds its floating head). Collar closed by a shallow dish (the head flies away from it).
- Joints: spine and head stay at MM9's; shoulder, elbow, wrist on the arm's slice centres; every robe chain joint on the tube, its column at the chain's mean angle.
- Weights: arms in bands (shoulder blend wide, the MM9 clips lift the arms over the head). Robe: MM9's rigid rings at higher resolution, i.e. hat functions in s along a chain and in theta between chains.
Args: <robe blend with Upper, Robe> <mm9 glb> <out blend> <report json>"""
import bpy, bmesh, sys, json, math
import numpy as np
from mathutils import Vector
A = sys.argv[sys.argv.index('--') + 1:]
IN, MM9, OUT, REP = A
rep = {}
bpy.ops.wm.open_mainfile(filepath=IN)
up = bpy.data.objects['Upper']; robe = bpy.data.objects['Robe']
bpy.context.view_layer.objects.active = up
existing = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=MM9)
new = [o for o in bpy.data.objects if o not in existing]
arm = next(o for o in new if o.type == 'ARMATURE'); arm.name = 'MM9_Rig'
if arm.animation_data:
    arm.animation_data.action = None
for x in list(bpy.data.actions):
    bpy.data.actions.remove(x)
for o in new:
    if o is not arm:
        bpy.data.objects.remove(o)
for pb in arm.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
J = {b.name: np.array(arm.matrix_world @ b.head_local) for b in arm.data.bones}
SIDES = {1: '01', -1: ''}             # +x carries the 01 chain
# ------------------------------------------------------------- arm geometry
bm = bmesh.new(); bm.from_mesh(up.data); bm.verts.ensure_lookup_table()
seen = {}; comps = []
for v in bm.verts:
    if v.index in seen:
        continue
    st = [v]; cur = [v]; seen[v.index] = len(comps)
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in seen:
                seen[y.index] = len(comps); st.append(y); cur.append(y)
    comps.append(cur)
comps.sort(key=len, reverse=True)
print('COMPS', [len(c) for c in comps])
cuffs = {}
for c in comps[1:]:
    p = np.array([v.co[:] for v in c])
    cuffs[int(np.sign(p[:, 0].mean()))] = (0.5 * (p.min(0) + p.max(0)), c)
co = np.array([v.co[:] for v in comps[0]])
P_ = co[co[:, 0] > 0.20]
# arm axis: shoulder centre from the slice just outside the shoulder seam, wrist = cuff centre
c_cuff = cuffs[1][0]
d0 = (c_cuff - np.array([0.17, -0.08, 0.37])); d0 /= np.linalg.norm(d0)
print('CUFF', c_cuff, 'P_', len(P_), P_.min(0), P_.max(0), {k: v[0].tolist() for k, v in cuffs.items()})


def slice_centre(a0, w=0.012):
    q0 = np.array([0.17, -0.08, 0.37])
    al = (P_ - q0) @ d0
    m = np.abs(al - a0) < w
    p = P_[m]
    return 0.5 * (p.min(0) + p.max(0)), int(m.sum())


cs = [slice_centre(a)[0] for a in (0.08, 0.14, 0.20, 0.26, 0.32)]
cs = np.array(cs); u = np.linalg.svd(cs - cs.mean(0))[2][0]
if u @ d0 < 0:
    u = -u
print('AXIS', u, 'd0', d0, 'centres', cs.round(3).tolist())
sho = cs.mean(0) + u * ((np.array([0.175, 0, 0]) - cs.mean(0))[0] / u[0])          # where the axis passes x = 0.175
L_mm9 = np.linalg.norm(J['Zhand01'] - J['Zarmpiv01'])
L_our = float((c_cuff - sho) @ u)
stretch = L_mm9 / L_our
print('SHOULDER', sho, 'L mm9', L_mm9, 'ours', L_our, 'stretch', stretch)
rep.update(stretch=stretch, shoulder=sho.tolist())
# sleeve end: planar cut 3.5 cm before the cuff, two rings into it (both sides)
bm.faces.ensure_lookup_table(); bm.edges.ensure_lookup_table()
for side in (1, -1):
    Ms = np.diag([side, 1, 1])
    uu = Ms @ u; ss = Ms @ sho; cc = Ms @ c_cuff
    verts0 = [v for v in bm.verts if v.co.x * side > 0.2 and seen.get(v.index, 0) == seen.get(comps[0][0].index) ] if False else None
    # the main comp's far sleeve verts
    main = set(v for v in bm.verts if v.is_valid and v.co.x * side > 0.25 and ((np.array(v.co[:]) - ss) @ uu) > 0.1
               and v in set(comps[0]))
    al = [((np.array(v.co[:]) - ss) @ uu) for v in main]
    a_end = float(max(al))
    a_cut = a_end - 0.035
    geom = list(set(f for v in main for f in v.link_faces)) + list(set(e for v in main for e in v.link_edges)) + list(main)
    res = bmesh.ops.bisect_plane(bm, geom=geom, plane_co=Vector((ss + uu * a_cut).tolist()), plane_no=Vector(uu.tolist()), clear_outer=True, dist=1e-5)
    bm.verts.ensure_lookup_table()
    ring = [e for e in bm.edges if e.is_boundary and min(abs((np.array(v.co[:]) - ss) @ uu - a_cut) for v in e.verts) < 1e-4
            and abs(e.verts[0].co.x) > 0.2 and e.verts[0].co.x * side > 0]
    # stray islands past the cut
    print('CUT side', side, 'a_end', a_end, 'a_cut', a_cut, 'ring edges', len(ring))
    rv = list({v for e in ring for v in e.verts})
    pts = np.array([v.co[:] for v in rv]); ctr = pts.mean(0)
    cr = np.linalg.norm(pts - ctr, axis=1).mean()
    a_cuff = float((cc - ss) @ uu)
    for k, (fa, fr) in enumerate(((0.5, 0.97), (1.0, 0.82))):
        ex = bmesh.ops.extrude_edge_only(bm, edges=ring)
        nv = [g for g in ex['geom'] if isinstance(g, bmesh.types.BMVert)]
        ring = [g for g in ex['geom'] if isinstance(g, bmesh.types.BMEdge) and all(v in nv for v in g.verts)]
        tgt = ctr + uu * (a_cuff - a_cut + 0.012) * fa
        for v in nv:
            p = np.array(v.co[:])
            al_ = (p - ctr) @ uu
            rr = p - ctr - uu * al_
            v.co = Vector((tgt + rr * fr).tolist())
    bm.verts.ensure_lookup_table()
    print('RING radius', cr, 'cuff a', a_cuff)
# drop fragments the cut left
bm.verts.ensure_lookup_table(); seen2 = set(); parts = []
for v in bm.verts:
    if v.index in seen2:
        continue
    st = [v]; cur = [v]; seen2.add(v.index)
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in seen2:
                seen2.add(y.index); st.append(y); cur.append(y)
    parts.append(cur)
parts.sort(key=len, reverse=True)
print('PARTS after cut', [len(p) for p in parts[:8]])
bmesh.ops.delete(bm, geom=[v for p in parts[3:] for v in p], context='VERTS')
cuff_faces = set(f for c in parts[1:3] for v in c for f in v.link_faces)
# collar dish
bm.edges.ensure_lookup_table()
top = [e for e in bm.edges if e.is_boundary and min(v.co.z for v in e.verts) > 0.38 and abs(e.verts[0].co.x) < 0.12]
# the largest boundary loop near the neck
loops = []; left = set(top)
while left:
    e = left.pop(); cur = {e}; st = [e]
    while st:
        x = st.pop()
        for v in x.verts:
            for y in v.link_edges:
                if y in left:
                    left.discard(y); cur.add(y); st.append(y)
    loops.append(cur)
loops.sort(key=len, reverse=True)
print('NECK loops', [len(l) for l in loops])
lv = list({v for e in loops[0] for v in e.verts})
cen = np.array([v.co[:] for v in lv]).mean(0)
ex = bmesh.ops.extrude_edge_only(bm, edges=list(loops[0]))
nv = [g for g in ex['geom'] if isinstance(g, bmesh.types.BMVert)]
for v in nv:
    v.co = Vector((cen + (np.array(v.co[:]) - cen) * 0.55 + np.array([0, 0, -0.014])).tolist())
ne = [g for g in ex['geom'] if isinstance(g, bmesh.types.BMEdge) and all(v in nv for v in g.verts)]
res = bmesh.ops.edgeloop_fill(bm, edges=ne)
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
# pin holes the ornaments left, and the chest's slits (lapels and bosses are paint here, not folds): a see-through shell shows them
left = set(e for e in bm.edges if e.is_boundary and not any(f in cuff_faces for f in e.link_faces))
small = 0
while left:
    e = left.pop(); cur = {e}; st = [e]
    while st:
        x = st.pop()
        for v in x.verts:
            for y in v.link_edges:
                if y in left:
                    left.discard(y); cur.add(y); st.append(y)
    if len(cur) <= 14:
        bmesh.ops.holes_fill(bm, edges=list(cur), sides=0); small += 1
print('PIN HOLES filled', small)
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
ch = [v for v in bm.verts if abs(v.co.x) < 0.17 and 0.15 < v.co.z < 0.44 and not v.is_boundary and not any(f in cuff_faces for f in v.link_faces)]
for _ in range(8):
    bmesh.ops.smooth_vert(bm, verts=ch, factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
# the extruded sleeve rings and the arm around them point away from the arm axis (recalc guesses per island)
flipped = 0
for f in bm.faces:
    c = np.array(f.calc_center_median()[:])
    side = 1 if c[0] > 0 else -1
    if abs(c[0]) < 0.28:
        continue
    Ms = np.diag([side, 1, 1]); uu = Ms @ u; ss_ = Ms @ sho
    al = (c - ss_) @ uu
    if al < 0.1 or f in cuff_faces:
        continue
    rad = c - ss_ - uu * al
    if np.array(f.normal[:]) @ rad < 0:
        f.normal_flip(); flipped += 1
print('FLIPPED arm faces', flipped)
# stretch the arms along their axis, from the shoulder out
for v in bm.verts:
    side = 1 if v.co.x > 0 else -1
    p = np.array(v.co[:]); Ms = np.diag([side, 1, 1]); uu = Ms @ u; ss = Ms @ sho
    al = (p - ss) @ uu
    if al > 0 and abs(p[0]) > 0.15:
        v.co = Vector((p + uu * al * (stretch - 1)).tolist())
bm.to_mesh(up.data); bm.free()
up.data.update()
print('UPPER', len(up.data.vertices), len(up.data.polygons))
# ------------------------------------------------------------- joints
newJ = dict(J)
elbow_frac = float(np.linalg.norm(J['Zarm01'] - J['Zarmpiv01']) / L_mm9)
wr = sho + u * L_mm9
for side, tag in SIDES.items():
    Ms = np.diag([side, 1, 1])
    newJ['Zarmpiv' + tag] = Ms @ sho
    newJ['Zarm' + tag] = Ms @ (sho + u * L_mm9 * elbow_frac)
    newJ['Zhand' + tag] = Ms @ wr
    newJ['Zarmbase' + tag] = Ms @ (J['Xspine2'] * 0.35 + 0.65 * sho)
    for k, n in enumerate(('Zfingbase', 'ZfingA', 'ZfingB', 'ZfingC')):
        nm = n + tag
        newJ[nm] = newJ['Zhand' + tag] + (J[nm] - J['Zhand' + tag])
# robe columns
rm = robe.data
rv = np.array([v.co[:] for v in rm.vertices])
n_t = int(round(sum(1 for z in rv if abs(z[2] - rv[0, 2]) < 1e-5)))
Nt = 40; Ns = len(rv) // Nt
grid = rv.reshape(Ns, Nt, 3)
CH = {'f': ['Yfront', 'YfA', 'YfB', 'YfC', 'YfD'], 'fl': ['Yfrontleft', 'YflA', 'YflB', 'YflC'], 'l': ['Yleft', 'YlA', 'YlB', 'YlC', 'YlD'],
      'bl': ['YblA', 'YblB', 'YblC'], 'b': ['Yback', 'YbA', 'YbB', 'YbC', 'YbD'], 'br': ['YbrA', 'YbrB', 'YbrC'],
      'r': ['Yrit', 'YrA', 'YrB', 'YrC', 'YrD'], 'fr': ['Yfrontrit', 'YfrA', 'YfrB', 'YfrC']}
ORDER = ['f', 'fl', 'l', 'bl', 'b', 'br', 'r', 'fr']
col = {}; rows = {}
for c in ORDER:
    ks = []; ss_ = []
    for n in CH[c]:
        d = np.linalg.norm(grid - J[n], axis=2)
        i, k = np.unravel_index(d.argmin(), d.shape)
        ks.append(k); ss_.append(i)
    ang = np.array(ks) * 2 * np.pi / Nt
    mean = np.angle(np.exp(1j * ang).mean())
    col[c] = float((mean % (2 * np.pi)) / (2 * np.pi) * Nt)
    rows[c] = ss_
print('COLUMNS', {c: round(v, 2) for c, v in col.items()}, rows)
for c in ORDER:
    ks = col[c]; rr = list(rows[c])
    # strictly increasing along the chain; the tip on the last ring
    rr[-1] = Ns - 1
    for i in range(len(rr) - 2, -1, -1):
        rr[i] = min(rr[i], rr[i + 1] - 1)
    for i in range(1, len(rr)):
        rr[i] = max(rr[i], rr[i - 1] + 1)
    rows[c] = rr
    k0 = int(ks) % Nt; k1 = (k0 + 1) % Nt; f = ks - int(ks)
    for n, r in zip(CH[c], rr):
        newJ[n] = grid[r, k0] * (1 - f) + grid[r, k1] * f
newJ['Ydress'] = J['Ydress']
rep['rows'] = rows; rep['columns'] = col
# move the bones (rest rotations unchanged)
bpy.context.view_layer.objects.active = arm
for o in bpy.data.objects:
    o.select_set(o == arm)
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.data.edit_bones
inv = np.array(arm.matrix_world.inverted())
for b in eb:
    tail_off = b.tail - b.head
    p = Vector((inv[:3, :3] @ newJ[b.name] + inv[:3, 3]).tolist())
    b.use_connect = False
for b in eb:
    tail_off = b.tail - b.head
    p = Vector((inv[:3, :3] @ newJ[b.name] + inv[:3, 3]).tolist())
    b.head = p; b.tail = p + tail_off
bpy.ops.object.mode_set(mode='OBJECT')
# ------------------------------------------------------------- weights
names = [b.name for b in arm.data.bones]


def ss(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def add(W, i, n, w):
    if w > 1e-4:
        W[i][n] = W[i].get(n, 0) + float(w)


# upper
mw = up.matrix_world
UP = np.array([tuple(mw @ v.co) for v in up.data.vertices])
WU = [{} for _ in UP]
sp = [(n, newJ[n][2]) for n in ('XCENTER', 'Xspine', 'Xspine1', 'Xspine2')]
for i, p in enumerate(UP):
    side = 1 if p[0] > 0 else -1
    tag = SIDES[side]
    Ms = np.diag([side, 1, 1]); uu = Ms @ u; s0 = Ms @ sho
    al = (p - s0) @ uu
    # torso share along the arm axis
    arm_t = ss(-0.075, 0.035, al) if abs(p[0]) > 0.09 else 0.0
    z = p[2]
    tw = []
    if z <= sp[1][1]:
        f = ss(sp[0][1], sp[1][1], z); tw = [('XCENTER', 1 - f), ('Xspine', f)]
    elif z <= sp[2][1]:
        f = ss(sp[1][1], sp[2][1], z); tw = [('Xspine', 1 - f), ('Xspine1', f)]
    elif z <= sp[3][1] + 0.0:
        f = ss(sp[2][1], sp[3][1], z); tw = [('Xspine1', 1 - f), ('Xspine2', f)]
    else:
        tw = [('Xspine2', 1.0)]
    for n, w in tw:
        add(WU, i, n, w * (1 - arm_t))
    if arm_t > 0:
        base = 1 - ss(-0.01, 0.09, al)
        add(WU, i, 'Zarmbase' + tag, arm_t * base)
        rest = arm_t * (1 - base)
        e = L_mm9 * elbow_frac
        f = ss(e - 0.045, e + 0.045, al)
        w = ss(L_mm9 - 0.03, L_mm9 + 0.0, al)
        add(WU, i, 'Zarmpiv' + tag, rest * (1 - f))
        add(WU, i, 'Zarm' + tag, rest * f * (1 - w))
        add(WU, i, 'Zhand' + tag, rest * f * w)
# robe: hats
WR = [{} for _ in rv]
cols = [(col[c], c) for c in ORDER]
cols.sort()
Ncols = len(cols)
for i in range(Ns):
    for k in range(Nt):
        idx = i * Nt + k
        q = None
        for a in range(Ncols):
            c0, n0 = cols[a]; c1, n1 = cols[(a + 1) % Ncols]
            c1w = c1 + (Nt if c1 < c0 else 0)
            kk = k + (Nt if k < c0 else 0)
            if c0 <= kk <= c1w:
                q = (n0, n1, (kk - c0) / (c1w - c0)); break
        n0, n1, f = q
        for c, cw in ((n0, 1 - f), (n1, f)):
            rr = rows[c]; bs = CH[c]
            if i <= 3:                       # belt rings ride the hips
                b = ss(0, 3, i)
                add(WR, idx, 'XCENTER', cw * (1 - b)); add(WR, idx, 'Ydress', cw * b * 0.999)
                continue
            if i < rr[0]:
                f2 = (i - 3) / max(rr[0] - 3, 1)
                add(WR, idx, 'Ydress', cw * (1 - f2)); add(WR, idx, bs[0], cw * f2)
                continue
            for a in range(len(rr) - 1):
                if rr[a] <= i <= rr[a + 1]:
                    f2 = (i - rr[a]) / (rr[a + 1] - rr[a])
                    add(WR, idx, bs[a], cw * (1 - f2)); add(WR, idx, bs[a + 1], cw * f2)
                    break


def apply(obj, W):
    obj.vertex_groups.clear()
    for n in names:
        obj.vertex_groups.new(name=n)
    for i, w in enumerate(W):
        top = sorted(w.items(), key=lambda kv: -kv[1])[:4]
        t = sum(x for _, x in top) or 1.0
        for n, x in top:
            obj.vertex_groups[n].add([i], x / t, 'REPLACE')


apply(up, WU); apply(robe, WR)
# one Body: part attribute 0 upper, 1 robe
for name, obj, val in (('up', up, 0), ('robe', robe, 1)):
    a = obj.data.attributes.new('part', 'INT', 'FACE'); a.data.foreach_set('value', [val] * len(obj.data.polygons))
for o in bpy.data.objects:
    o.select_set(o in (up, robe))
bpy.context.view_layer.objects.active = up
bpy.ops.object.join()
body = up; body.name = 'Body'; body.data.name = 'Body'
for p in body.data.polygons:
    p.use_smooth = True
body.parent = arm
mod = body.modifiers.new('Armature', 'ARMATURE'); mod.object = arm
bpy.ops.wm.save_as_mainfile(filepath=OUT)
rep['joints'] = {k: np.round(v, 4).tolist() for k, v in newJ.items()}
json.dump(rep, open(REP, "w"), indent=1, default=float)
print('FIT', len(body.data.vertices), len(body.data.polygons))
