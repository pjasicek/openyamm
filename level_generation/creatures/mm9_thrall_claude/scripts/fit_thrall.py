"""Step A: Meshy body -> symmetric -> MM9 bind pose (true handedness).
Meshy's torso is centred and its left half mirrored (body part only; skirt, ropes, sandals keep their shapes). Limb directions go exactly onto MM9's bones; arm lengths are MM9's,
leg lengths a blend (Meshy's knee is high: MM9's calves are short), the rest is written as moved joints `J2` for the rig (translation only: rest rotations stay MM9's).
Parts: 0 skin, 1 skirt, 3 belt+knot+rope ends, 5 sandals L/R, 6 collar. The old head goes at neck_cut_z. Args: <meshy glb> <mm9 true glb> <config> <out blend>"""
import bpy, bmesh, sys, json
import numpy as np
from mathutils import Vector
MESHY, MM9, CFG, OUT = sys.argv[sys.argv.index('--') + 1:]
cfg = json.load(open(CFG))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=MM9)
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE'); arm.name = 'MM9_Rig'
if arm.animation_data: arm.animation_data.action = None
for pb in arm.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
J = {b.name.replace('Bip01 ', ''): np.array(arm.matrix_world @ b.head_local) for b in arm.data.bones}
dg = bpy.context.evaluated_depsgraph_get()
A = []
for o in bpy.data.objects:
    if o.type == 'MESH' and not o.name.startswith('Icosphere'):
        me = o.evaluated_get(dg).to_mesh(); A += [tuple(o.matrix_world @ v.co) for v in me.vertices]
A = np.array(A)
exist = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=MESHY)
new = [o for o in bpy.data.objects if o not in exist]
body = next(o for o in new if o.type == 'MESH')
Mw = body.matrix_world.copy()
for o in new:
    if o is not body: bpy.data.objects.remove(o)
body.parent = None; body.matrix_world = Mw; body.name = 'Body'
for o in bpy.data.objects:
    if o is not body: bpy.data.objects.remove(o, do_unlink=True)
me = body.data
bpy.context.view_layer.objects.active = body; body.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
me.materials.clear()
yaw = np.radians(cfg['yaw_deg']); c, s_ = np.cos(yaw), np.sin(yaw); Rz = np.array([[c, -s_, 0], [s_, c, 0], [0, 0, 1]])
x0 = cfg['x0']
sc = np.ptp(A[:, 2]) / (0.5 + 0.497)
z0 = A[:, 2].min() + 0.497 * sc      # raw z=-.497 (the foot's bottom, soles a little lower) on MM9's floor
def norm_pts(Q):
    Q = np.asarray(Q, float) @ Rz.T; Q = Q.copy(); Q[..., 0] -= x0
    return Q * sc + np.array([0, 0, z0])
bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
Q = norm_pts(np.array([v.co[:] for v in bm.verts]))
for v, p in zip(bm.verts, Q): v.co = Vector(p)
lay = bm.verts.layers.int.new('part')
seen = set(); comps = []
for v in bm.verts:
    if v in seen: continue
    st = [v]; seen.add(v); cc = [v]
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if y not in seen: seen.add(y); st.append(y); cc.append(y)
    comps.append(cc)
comps.sort(key=len, reverse=True)
kill = []
for i, cc in enumerate(comps):
    q = np.array([v.co[:] for v in cc]); cen = q.mean(0); ext = np.ptp(q, 0)
    if i == 0: pid = 0
    elif i == 1: pid = 1
    elif cen[2] > 0.76: pid = -1          # face shell, eyes: above the collar
    elif cen[2] > 0.6: pid = 6            # collar
    elif cen[2] > -0.3: pid = 3                        # belt, knot, rope ends
    else: pid = 5                                      # sandals
    print('COMP', i, len(cc), np.round(cen, 3).tolist(), np.round(ext, 3).tolist(), 'part', pid)
    if pid < 0: kill += cc
    else:
        for v in cc: v[lay] = pid
bmesh.ops.delete(bm, geom=kill, context='VERTS')
# the body: left half (x > 0) mirrored
def part_geom(pid):
    vs = [v for v in bm.verts if v[lay] == pid]
    es = list({e for v in vs for e in v.link_edges}); fs = list({f for v in vs for f in v.link_faces})
    return vs + es + fs
bmesh.ops.bisect_plane(bm, geom=part_geom(0), plane_co=(0, 0, 0), plane_no=(1, 0, 0), clear_inner=True, dist=1e-5)
for v in bm.verts:
    if v[lay] == 0 and abs(v.co.x) < 1e-4: v.co.x = 0
bmesh.ops.mirror(bm, geom=part_geom(0), axis='X', merge_dist=1e-4)
bmesh.ops.recalc_face_normals(bm, faces=[f for f in bm.faces if f.verts[0][lay] == 0])
bm.to_mesh(me); bm.free()
P = np.array([v.co[:] for v in me.vertices]); n = len(P)
PART = np.zeros(n, int); me.attributes['part'].data.foreach_get('value', PART)
print('PARTS', {int(k): int((PART == k).sum()) for k in np.unique(PART)})
# estimates in the normalised frame
R = cfg['raw']
E = {}
def est(name, q, sx=1):
    v = np.array(q, float); 
    Qe = (v @ Rz.T); Qe = Qe.copy(); Qe[0] -= x0
    Qe = Qe * sc + np.array([0, 0, z0]); Qe[0] = Qe[0] * sx
    E[name] = Qe
est('pelvis', R['pelvis']); E['pelvis'][0] = 0
est('neck', R['neck']); E['neck'][0] = 0
for s, sx in (('L', 1), ('R', -1)):
    for a, b in (('UpperArm', 'shoulder'), ('Forearm', 'elbow'), ('Hand', 'wrist'), ('Knuckle', 'knuckle'), ('Thigh', 'hip'), ('Calf', 'knee'), ('Foot', 'ankle'), ('Toe0', 'ball')):
        est(f'{s} {a}', R[b], sx)
        E[f'{s} {a}'][0] = abs(E[f'{s} {a}'][0]) * sx
print('EST', {k: np.round(v, 3).tolist() for k, v in E.items()})
def rot(a, b):
    a = a / np.linalg.norm(a); b = b / np.linalg.norm(b)
    v = np.cross(a, b); c = float(a @ b); sn = np.linalg.norm(v)
    if sn < 1e-9: return np.eye(3)
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + K + K @ K * ((1 - c) / sn ** 2)
# moved joints: MM9's directions, blended leg lengths
J2 = dict(J)
LB = cfg['leg_len_blend']
for s in 'LR':
    pa = J[f'{s} Thigh']
    for a, b, key in ((f'{s} Thigh', f'{s} Calf', 'Thigh'), (f'{s} Calf', f'{s} Foot', 'Calf'), (f'{s} Foot', f'{s} Toe0', 'Foot')):
        d = J[b] - J[a]; L_mm9 = np.linalg.norm(d); L_our = np.linalg.norm(E[b] - E[a]); L = L_mm9 * LB[key] + L_our * (1 - LB[key])
        print('LEN', s, key, round(L_mm9, 3), round(L_our, 3), '->', round(L, 3))
        J2[b] = J2[a] + d / L_mm9 * L
def seg_map(ea, eb, ja, jb, rg=0.0):
    u = eb - ea; L = np.linalg.norm(u); u = u / L
    k = np.linalg.norm(jb - ja) / L
    Rm = rot(u, jb - ja)
    S = np.eye(3) + (k - 1) * np.outer(u, u) + rg * (k - 1) * (np.eye(3) - np.outer(u, u))     # stretched limbs thicken a share of it
    A_ = Rm @ S
    return A_, ja - A_ @ ea
src = np.array([E['pelvis'], E['L UpperArm'], E['R UpperArm'], E['neck']]); dst = np.array([0.5 * (J2['L Thigh'] + J2['R Thigh']), J['L UpperArm'], J['R UpperArm'], J['Neck']])
sc_, dc = src.mean(0), dst.mean(0)
H = (src - sc_).T @ (dst - dc); U, _, Vt = np.linalg.svd(H); Rt = Vt.T @ np.diag([1, 1, np.sign(np.linalg.det(Vt.T @ U.T))]) @ U.T
print('torso rot deg', np.degrees(np.arccos((np.trace(Rt) - 1) / 2)))
Tt = (Rt, dc - Rt @ sc_)
SEGS = {}; ends = {}
for s_ in 'LR':
    RG = cfg.get('arm_radial', 0.6)
    SEGS[f'{s_} UpperArm'] = seg_map(E[f'{s_} UpperArm'], E[f'{s_} Forearm'], J[f'{s_} UpperArm'], J[f'{s_} Forearm'], RG)
    SEGS[f'{s_} Forearm'] = seg_map(E[f'{s_} Forearm'], E[f'{s_} Hand'], J[f'{s_} Forearm'], J[f'{s_} Hand'], RG)
    ej = J[f'{s_} Hand'] + (J[f'{s_} Finger1'] - J[f'{s_} Hand']) / np.linalg.norm(J[f'{s_} Finger1'] - J[f'{s_} Hand']) * np.linalg.norm(E[f'{s_} Knuckle'] - E[f'{s_} Hand'])
    SEGS[f'{s_} Hand'] = seg_map(E[f'{s_} Hand'], E[f'{s_} Knuckle'], J[f'{s_} Hand'], ej)
    SEGS[f'{s_} Thigh'] = seg_map(E[f'{s_} Thigh'], E[f'{s_} Calf'], J2[f'{s_} Thigh'], J2[f'{s_} Calf'])
    SEGS[f'{s_} Calf'] = seg_map(E[f'{s_} Calf'], E[f'{s_} Foot'], J2[f'{s_} Calf'], J2[f'{s_} Foot'])
    # foot: yaw only, or the sole pitches against MM9's in every clip (Mummy). The toe joint goes to the ball of OUR foot, rest rotations stay
    ea, eb = E[f'{s_} Foot'], E[f'{s_} Toe0']; d0 = J[f'{s_} Toe0'] - J[f'{s_} Foot']
    ang = np.arctan2(d0[1], d0[0]) - np.arctan2((eb - ea)[1], (eb - ea)[0]); ca, sa = np.cos(ang), np.sin(ang)
    Ry = np.array([[ca, -sa, 0], [sa, ca, 0], [0, 0, 1]])
    SEGS[f'{s_} Foot'] = (Ry, J2[f'{s_} Foot'] - Ry @ ea)
    J2[f'{s_} Toe0'] = J2[f'{s_} Foot'] + Ry @ (eb - ea)
    ends.update({f'{s_} UpperArm': (f'{s_} UpperArm', f'{s_} Forearm'), f'{s_} Forearm': (f'{s_} Forearm', f'{s_} Hand'), f'{s_} Hand': (f'{s_} Hand', f'{s_} Knuckle'),
                 f'{s_} Thigh': (f'{s_} Thigh', f'{s_} Calf'), f'{s_} Calf': (f'{s_} Calf', f'{s_} Foot'), f'{s_} Foot': (f'{s_} Foot', f'{s_} Toe0')})
names = list(SEGS)
nbr = [[] for _ in range(n)]
for e in me.edges:
    a, b = e.vertices; nbr[a].append(b); nbr[b].append(a)
def seg_d(Q, a, b):
    ab = b - a
    t = (Q - a) @ ab / (ab @ ab)
    tc = np.clip(t, 0, 1)
    return np.linalg.norm(Q - a - np.outer(tc, ab), axis=1), t
D = np.ones((n, len(names))) * 1e3
for i, b in enumerate(names):
    d, t = seg_d(P, E[ends[b][0]], E[ends[b][1]])
    side = 1 if b[0] == 'L' else -1
    ok = (np.sign(P[:, 0]) == side)
    if 'Thigh' in b or 'Calf' in b or 'Foot' in b:
        ok &= (PART == 0) | (PART == 5)
        if 'Thigh' in b: ok &= (d < 0.17) & (t > -0.25)
    else:
        ok &= PART == 0
    if 'Hand' in b:
        d = np.where(t < 0, d + 0.02, d)
    D[:, i] = np.where(ok, d, 1e3)
best = D.argmin(1); dbest = D.min(1)
lab = np.zeros((n, len(names) + 1))
rad = {'UpperArm': 0.11, 'Forearm': 0.09, 'Hand': 0.16, 'Thigh': 0.17, 'Calf': 0.15, 'Foot': 0.24}
free = np.array([dbest[i] < rad[names[best[i]].split()[1]] for i in range(n)])
for s_ in 'LR':
    b = f'{s_} UpperArm'; o = E[b]; u = E[f'{s_} Forearm'] - o; u = u / np.linalg.norm(u)
    i = names.index(b)
    free &= ~((best == i) & ((P - o) @ u < -0.01))
    b = f'{s_} Thigh'; o = E[b]; u = E[f'{s_} Calf'] - o; u = u / np.linalg.norm(u)
    i = names.index(b)
    free &= ~((best == i) & ((P - o) @ u < 0.0))
lab[np.arange(n), np.where(free, best + 1, 0)] = 1
for _ in range(cfg.get('blend_iters', 8)):
    avg = np.array([lab[nb].mean(0) if nb else lab[i] for i, nb in enumerate(nbr)])
    lab = 0.5 * lab + 0.5 * avg
tw = np.clip((P[:, 2] - 0.2) / 0.22, 0, 1); tw = tw * tw * (3 - 2 * tw)
Pel = 0.5 * (J2['L Thigh'] + J2['R Thigh']) - E['pelvis']
base = (P @ Tt[0].T + Tt[1]) * tw[:, None] + (P + Pel) * (1 - tw[:, None])
Q = lab[:, :1] * base
for i, b in enumerate(names):
    A_, t_ = SEGS[b]
    Q = Q + lab[:, i + 1:i + 2] * (P @ A_.T + t_)
print('floor', Q[:, 2].min(), 'bbox', Q.min(0), Q.max(0), 'MM9', A.min(0), A.max(0))
for v, p in zip(me.vertices, Q): v.co = Vector(p)
me.update()
# old head off at the neck
bm = bmesh.new(); bm.from_mesh(me); lay = bm.verts.layers.int['part']
cut = float(cfg['neck_cut_z'])
vs = [v for v in bm.verts if v[lay] == 0]; es = list({e for v in vs for e in v.link_edges}); fs = list({f for v in vs for f in v.link_faces})
bmesh.ops.bisect_plane(bm, geom=vs + es + fs, plane_co=(0, 0, cut), plane_no=(0, 0, 1), clear_outer=True)
bm.to_mesh(me); bm.free()
for zz in (0.60, 0.64, 0.68, 0.70):
    m = (np.abs(Q[:, 2] - zz) < 0.012) & (PART == 0) & (np.abs(Q[:, 0]) < 0.11)
    print('NECK z', zz, 'c', np.round(0.5 * (Q[m].min(0) + Q[m].max(0)), 3), 'ext', np.round(np.ptp(Q[m], 0), 3))
print('FINAL verts', len(me.vertices))
np.savez(OUT + '.joints.npz', **J2)
for p in me.polygons: p.use_smooth = True
bpy.ops.wm.save_as_mainfile(filepath=OUT)
