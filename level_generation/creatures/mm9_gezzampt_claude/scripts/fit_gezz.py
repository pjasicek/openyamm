"""Step A: Meshy body -> symmetric (left half mirrored) -> MM9 bind pose in true handedness. Every limb segment goes exactly onto its MM9 bone, lengths included (the estimates in fit_config.json were placed so the
stretch stays small); the hoof follows the Foot joint by yaw only. Head off at the neck (the head-only model replaces it). Writes <out> and <out>.joints.npz. Args: <meshy glb> <mm9 true glb> <config> <out blend>"""
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
print('MM9J', {k: np.round(v, 3).tolist() for k, v in J.items() if k.startswith('R ') or k in ('Pelvis', 'Neck', 'Head')})
exist = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=MESHY)
new = [o for o in bpy.data.objects if o not in exist]
body = next(o for o in new if o.type == 'MESH')
Mw = body.matrix_world.copy(); body.parent = None; body.matrix_world = Mw; body.name = 'Body'
for o in list(bpy.data.objects):
    if o is not body: bpy.data.objects.remove(o, do_unlink=True)
me = body.data
bpy.context.view_layer.objects.active = body; body.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
me.materials.clear()
sc = cfg['sc']; z0 = cfg['floor_z'] + 0.5 * sc
def norm_pts(Q): return np.asarray(Q, float) * sc + np.array([0, 0, z0])
bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
for v in bm.verts: v.co = Vector(norm_pts(np.array(v.co[:])))
# the main shell only: small pieces are the old head's teeth
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
print('COMPS', [len(c) for c in comps])
bmesh.ops.delete(bm, geom=[v for c in comps[1:] for v in c], context='VERTS')
bmesh.ops.bisect_plane(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces), plane_co=(0, 0, 0), plane_no=(1, 0, 0), clear_inner=True, dist=1e-5)
for v in bm.verts:
    if abs(v.co.x) < 1e-4: v.co.x = 0
bmesh.ops.mirror(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces), axis='X', merge_dist=1e-4)
bmesh.ops.reverse_faces(bm, faces=[f for f in bm.faces if f.calc_center_median().x < 0])
bm.to_mesh(me); bm.free()
P = np.array([v.co[:] for v in me.vertices]); n = len(P)
print('MIRRORED verts', n, 'boundary?')
R = cfg['raw']; E = {}
E['pelvis'] = norm_pts(R['pelvis']); E['neck'] = norm_pts(R['neck'])
for s, sx in (('L', 1), ('R', -1)):
    for a, b in (('UpperArm', 'shoulder'), ('Forearm', 'elbow'), ('Hand', 'wrist'), ('Knuckle', 'knuckle'), ('Thigh', 'hip'), ('Calf', 'knee'), ('HorseLink', 'hock'), ('Foot', 'fetlock'), ('Ball', 'ball')):
        q = norm_pts(R[b]); q[0] *= sx; E[f'{s} {a}'] = q
def rot(a, b):
    a = a / np.linalg.norm(a); b = b / np.linalg.norm(b)
    v = np.cross(a, b); c = float(a @ b); sn = np.linalg.norm(v)
    if sn < 1e-9: return np.eye(3)
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + K + K @ K * ((1 - c) / sn ** 2)
J2 = dict(J)
# knee and hock: between MM9's joint and ours, measured on the pelvis-aligned body (MM9's short flat calf would squash our thick leg into a shelf)
LB = cfg.get('leg_blend', 0.6)
for s_ in 'LR':
    off = 0.5 * (J['L Thigh'] + J['R Thigh']) - 0.5 * (E['L Thigh'] + E['R Thigh'])
    for k in ('Calf', 'HorseLink'):
        J2[f'{s_} {k}'] = J[f'{s_} {k}'] * (1 - LB) + (E[f'{s_} {k}'] + off) * LB
    print('KNEE', s_, np.round(J2[f'{s_} Calf'], 3), np.round(J2[f'{s_} HorseLink'], 3))
def seg_map(ea, eb, ja, jb, rg=0.0):
    u = eb - ea; L = np.linalg.norm(u); u = u / L
    k = np.linalg.norm(jb - ja) / L
    Rm = rot(u, jb - ja)
    S = np.eye(3) + (k - 1) * np.outer(u, u) + rg * (k - 1) * (np.eye(3) - np.outer(u, u))
    A_ = Rm @ S
    return A_, ja - A_ @ ea
src = np.array([E['pelvis'], E['L UpperArm'], E['R UpperArm'], E['neck']]); dst = np.array([0.5 * (J['L Thigh'] + J['R Thigh']), J['L UpperArm'], J['R UpperArm'], J['Neck']])
sc_, dc = src.mean(0), dst.mean(0)
H = (src - sc_).T @ (dst - dc); U, _, Vt = np.linalg.svd(H); Rt = Vt.T @ np.diag([1, 1, np.sign(np.linalg.det(Vt.T @ U.T))]) @ U.T
print('torso rot deg', np.degrees(np.arccos((np.trace(Rt) - 1) / 2)), 'residuals', np.round((src - sc_) @ Rt.T + dc - dst, 3).tolist())
Tt = (Rt, dc - Rt @ sc_)
SEGS = {}; ends = {}
RG = cfg.get('arm_radial', 0.6)
for s_ in 'LR':
    for a, b in (('UpperArm', 'Forearm'), ('Forearm', 'Hand')):
        SEGS[f'{s_} {a}'] = seg_map(E[f'{s_} {a}'], E[f'{s_} {b}'], J[f'{s_} {a}'], J[f'{s_} {b}'], RG); ends[f'{s_} {a}'] = (f'{s_} {a}', f'{s_} {b}')
    SEGS[f'{s_} Hand'] = seg_map(E[f'{s_} Hand'], E[f'{s_} Knuckle'], J[f'{s_} Hand'], J[f'{s_} Finger0']); ends[f'{s_} Hand'] = (f'{s_} Hand', f'{s_} Knuckle')
    for a, b in (('Thigh', 'Calf'), ('Calf', 'HorseLink'), ('HorseLink', 'Foot')):
        SEGS[f'{s_} {a}'] = seg_map(E[f'{s_} {a}'], E[f'{s_} {b}'], J2[f'{s_} {a}'], J2[f'{s_} {b}']); ends[f'{s_} {a}'] = (f'{s_} {a}', f'{s_} {b}')
        print('LEN', s_, a, round(np.linalg.norm(E[f'{s_} {b}'] - E[f'{s_} {a}']), 3), '->', round(np.linalg.norm(J2[f'{s_} {b}'] - J2[f'{s_} {a}']), 3), 'mm9', round(np.linalg.norm(J[f'{s_} {b}'] - J[f'{s_} {a}']), 3))
    # hoof: the fetlock on the Foot joint, no pitch; height stretched so the sole stays on MM9's floor
    ea = E[f'{s_} Foot']; h_our = ea[2] - cfg['floor_z']; h_mm9 = J[f'{s_} Foot'][2] - cfg['floor_z']
    print('HOOF', s_, round(h_our, 3), '->', round(h_mm9, 3))
    Sz = np.diag([1.0, 1.0, h_mm9 / h_our])
    SEGS[f'{s_} Foot'] = (Sz, J[f'{s_} Foot'] - Sz @ ea); ends[f'{s_} Foot'] = (f'{s_} Foot', f'{s_} Ball')
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
    if 'Thigh' in b: ok &= (d < 0.27) & (t > -0.25)
    if 'Hand' in b: d = np.where(t < 0, d + 0.02, d)
    D[:, i] = np.where(ok, d, 1e3)
best = D.argmin(1); dbest = D.min(1)
lab = np.zeros((n, len(names) + 1))
rad = {'UpperArm': 0.2, 'Forearm': 0.16, 'Hand': 0.25, 'Thigh': 0.27, 'Calf': 0.2, 'HorseLink': 0.2, 'Foot': 0.5}
free = np.array([dbest[i] < rad[names[best[i]].split()[1]] for i in range(n)])
for s_ in 'LR':
    b = f'{s_} UpperArm'; o = E[b]; u = E[f'{s_} Forearm'] - o; u = u / np.linalg.norm(u)
    i = names.index(b); free &= ~((best == i) & ((P - o) @ u < -0.01))
    b = f'{s_} Thigh'; o = E[b]; u = E[f'{s_} Calf'] - o; u = u / np.linalg.norm(u)
    i = names.index(b); free &= ~((best == i) & ((P - o) @ u < 0.0))
lab[np.arange(n), np.where(free, best + 1, 0)] = 1
for _ in range(cfg.get('blend_iters', 8)):
    avg = np.array([lab[nb].mean(0) if nb else lab[i] for i, nb in enumerate(nbr)])
    lab = 0.5 * lab + 0.5 * avg
Q = lab[:, :1] * (P @ Tt[0].T + Tt[1])
for i, b in enumerate(names):
    A_, t_ = SEGS[b]
    Q = Q + lab[:, i + 1:i + 2] * (P @ A_.T + t_)
print('floor', Q[:, 2].min(), 'bbox', Q.min(0), Q.max(0))
for v, p in zip(me.vertices, Q): v.co = Vector(p)
me.update()
for p in me.polygons: p.use_smooth = True
print('FINAL verts', len(me.vertices))
np.savez(OUT + '.joints.npz', **J2)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
