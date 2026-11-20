"""Step A (colloidal warrior, from mm9_giant_claude/fit_giant.py): Meshy body -> symmetric (figure's RIGHT half, the master's seen side, mirrored) -> MM9 bind pose in true handedness. MM9's joints, centred on x = 0 (the bind's bones sit 4.5 mm off, the mesh does not). Scale to MM9's height.
Arms: each segment rigidly onto its MM9 bone (blended by diffusion). Legs: a smooth shear of the thigh, the lower leg and foot translated only: the sole stays flat. Writes <out> and <out>.joints.npz. Args: <meshy glb> <mm9 true glb> <out blend>"""
import bpy, bmesh, sys, json, os
import numpy as np
from mathutils import Vector
MESHY, MM9, OUT = sys.argv[sys.argv.index('--') + 1:]
SC, FLOOR, OY = float(os.environ.get('SC', 2.0)), -1.016, float(os.environ.get('OY', 0.0))
E = {'UpperArm': (0.53, 0.03, 0.53), 'Forearm': (0.72, 0.03, 0.17), 'Hand': (0.88, 0.0, -0.03), 'Tip': (0.97, -0.03, -0.38)}   # after WIDEN
LEG = np.array([float(x) for x in os.environ.get('LEG', '0,0,0').split(',')]); Z0, Z1 = -0.25, -0.65
RG = float(os.environ.get('RG', 0.3))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=MM9)
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE'); arm.name = 'MM9_Rig'
if arm.animation_data: arm.animation_data.action = None
for pb in arm.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
J = {b.name.replace('Bip01 ', ''): np.array(arm.matrix_world @ b.head_local) for b in arm.data.bones}
for k in list(J):
    if k.startswith('R '):       # exact mirror of the left
        J[k] = J['L ' + k[2:]] * [-1, 1, 1]
for k in ('Pelvis', 'Spine', 'Spine1', 'Spine2', 'Spine3', 'Neck', 'Head'): J[k][0] = 0.0
print('MM9J', {k: np.round(v, 3).tolist() for k, v in J.items() if k[:2] == 'L ' or k in ('Pelvis', 'Head')})
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
bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
off = np.array((0.0, OY, 0.0))
zmin = min(v.co.z for v in bm.verts) * SC
for v in bm.verts: v.co = Vector(np.array(v.co[:]) * SC + off + np.array((0, 0, FLOOR - zmin)))
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
comps.sort(key=len, reverse=True); print('COMPS', [len(c) for c in comps])
bmesh.ops.delete(bm, geom=[v for c in comps[1:] for v in c], context='VERTS')
bmesh.ops.bisect_plane(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces), plane_co=(0, 0, 0), plane_no=(-1, 0, 0), clear_inner=True, dist=1e-5)
for v in bm.verts:
    if abs(v.co.x) < 1e-4: v.co.x = 0
bmesh.ops.mirror(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces), axis='X', merge_dist=1e-4)
bmesh.ops.reverse_faces(bm, faces=[f for f in bm.faces if f.calc_center_median().x > 0])
bd = [e for e in bm.edges if e.is_boundary]; print('BOUNDARY', len(bd))
if bd: bmesh.ops.holes_fill(bm, edges=bd, sides=60)
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
bm.to_mesh(me); bm.free()
P = np.array([v.co[:] for v in me.vertices]); n = len(P); print('MIRRORED', n)
# MM9's figure is wider than the master: widen the trunk (x * f(z), full between WZ1 and WZ2, fading to 1 at the legs and the head);
# beyond |x| = XA (the arms) the shift is constant, so arms move out without stretching.
WID = float(os.environ.get('WIDEN', 1.15)); XA = 0.62
def _ss(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
fz = 1 + (WID - 1) * _ss(P[:, 2], -0.75, -0.35) * (1 - _ss(P[:, 2], 0.55, 0.85))
ax = np.abs(P[:, 0])
P[:, 0] = np.sign(P[:, 0]) * np.where(ax < XA, ax * fz, ax + XA * (fz - 1))
print('WIDENED', WID)
nbr = [[] for _ in range(n)]
for e in me.edges:
    a, b = e.vertices; nbr[a].append(b); nbr[b].append(a)
def rot(a, b):
    a = a / np.linalg.norm(a); b = b / np.linalg.norm(b)
    v = np.cross(a, b); c = float(a @ b); sn = np.linalg.norm(v)
    if sn < 1e-9: return np.eye(3)
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + K + K @ K * ((1 - c) / sn ** 2)
def seg_map(ea, eb, ja, jb, rg=0.6):
    u = eb - ea; L = np.linalg.norm(u); u = u / L
    k = np.linalg.norm(jb - ja) / L
    S = np.eye(3) + (k - 1) * np.outer(u, u) + rg * (k - 1) * (np.eye(3) - np.outer(u, u))
    A_ = rot(u, jb - ja) @ S
    return A_, ja - A_ @ ea
def seg_d(Q, a, b):
    ab = b - a; t = (Q - a) @ ab / (ab @ ab); tc = np.clip(t, 0, 1)
    return np.linalg.norm(Q - a - np.outer(tc, ab), axis=1), t
Ea = {k: np.array(v) for k, v in E.items()}
SEGS = []
for s, sg in ((() if os.environ.get('PREVIEW') else (('L', 1), ('R', -1)))):
    M = np.array([sg, 1, 1])
    e = {k: v * M for k, v in Ea.items()}
    jT = J[f'{s} Finger1'] + (J[f'{s} Finger1'] - J[f'{s} Hand']) * 0.55     # the fingertip on MM9's Finger1 line
    SEGS.append((s, e['UpperArm'], e['Forearm']) + seg_map(e['UpperArm'], e['Forearm'], J[f'{s} UpperArm'], J[f'{s} Forearm'], RG))
    SEGS.append((s, e['Forearm'], e['Hand']) + seg_map(e['Forearm'], e['Hand'], J[f'{s} Forearm'], J[f'{s} Hand'], RG))
    SEGS.append((s, e['Hand'], e['Tip']) + seg_map(e['Hand'], e['Tip'], J[f'{s} Hand'], jT, 0.0))
D = np.ones((n, max(len(SEGS), 1))) * 1e3
for i, (s, a, b, A_, t_) in enumerate(SEGS):
    d, t = seg_d(P, a, b)
    ok = (np.sign(P[:, 0]) == (1 if s == 'L' else -1)) & (d < 0.17)
    if i % 3 == 0: ok &= (t > 0.08)        # the shoulder stays with the torso
    D[:, i] = np.where(ok, d, 1e3)
best = D.argmin(1); free = D.min(1) < 1e2
lab = np.zeros((n, len(SEGS) + 1)); lab[np.arange(n), np.where(free, best + 1, 0)] = 1
for _ in range(30):
    avg = np.array([lab[nb].mean(0) if nb else lab[i] for i, nb in enumerate(nbr)])
    lab = 0.5 * lab + 0.5 * avg
Q = lab[:, :1] * P
for i, (s, a, b, A_, t_) in enumerate(SEGS):
    Q = Q + lab[:, i + 1:i + 2] * (P @ A_.T + t_)
# legs
t = np.clip((Z0 - P[:, 2]) / (Z0 - Z1), 0, 1); f = t * t * (3 - 2 * t)
leg = (lab[:, 0] > 0.995) & (P[:, 2] < 0.1)
Q[leg, 0] += f[leg] * LEG[0] * np.sign(P[leg, 0]); Q[leg, 1] += f[leg] * LEG[1]
print('floor', Q[:, 2].min(), 'bbox', Q.min(0).round(3), Q.max(0).round(3))
for v, p in zip(me.vertices, Q): v.co = Vector(p)
me.update()
for p in me.polygons: p.use_smooth = True
np.savez(OUT + '.joints.npz', **J)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('FITTED', n)
