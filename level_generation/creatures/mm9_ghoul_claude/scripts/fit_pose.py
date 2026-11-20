"""Step A: place the Meshy body on the MM9 bind pose (true handedness), then symmetrise the upper body.
Every limb segment maps its own estimated joints exactly onto MM9's joints (rotation + stretch along the bone): the Meshy pose was a skewed stride from a
3/4 master, with arms 12 cm short of MM9's. A transient smooth label blends the affine maps, as fit_imp.py. The bald Meshy head is cut at the neck.
Args: <meshy glb> <mm9 true glb> <config> <out blend>"""
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
bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
bm.to_mesh(me); bm.free()
P = np.array([tuple(v.co) for v in me.vertices])
s = np.ptp(A[:, 2]) / np.ptp(P[:, 2]); P *= s
P[:, 2] += A[:, 2].min() - P[:, 2].min()
m = (P[:, 2] > 0.0) & (P[:, 2] < 0.4) & (np.abs(P[:, 0]) < 0.12); ma = (A[:, 2] > 0.0) & (A[:, 2] < 0.4) & (np.abs(A[:, 0]) < 0.12)
P[:, 1] += 0.5 * (A[ma, 1].min() + A[ma, 1].max()) - 0.5 * (P[m, 1].min() + P[m, 1].max())
P[:, 0] -= 0.5 * (P[:, 0].min() + P[:, 0].max()) - 0.5 * (A[:, 0].min() + A[:, 0].max())
n = len(P)
nbr = [[] for _ in range(n)]
for e in me.edges:
    a, b = e.vertices; nbr[a].append(b); nbr[b].append(a)
# components -> part ids (by bbox, stable names)
comp = -np.ones(n, int); c_ = 0
for i in range(n):
    if comp[i] >= 0: continue
    st = [i]; comp[i] = c_
    while st:
        x = st.pop()
        for y in nbr[x]:
            if comp[y] < 0: comp[y] = c_; st.append(y)
    c_ += 1
sizes = np.bincount(comp)
order = np.argsort(-sizes)
upper_c = order[0]; trousers_c = order[1]
PART = np.zeros(n, int)      # 0 upper, 1 trousers, 2 tatter, 3 rope etc
PART[comp == trousers_c] = 1
for c in range(c_):
    if c in (upper_c, trousers_c): continue
    q = P[comp == c]
    if sizes[c] > 400 and q[:, 2].mean() > 0.2 and np.ptp(q[:, 0]) > 0.2: PART[comp == c] = 2     # tatter skirt
    elif q[:, 2].mean() > -0.1: PART[comp == c] = 3                                                                         # belt rope, knot, cords
    elif q[:, 2].mean() > -0.5: PART[comp == c] = 4                                                                         # right shin
    else: PART[comp == c] = 5                                                                                               # right foot
print('PARTS', {int(k): int((PART == k).sum()) for k in np.unique(PART)}, 'comps', c_)
E = {k: np.array(v) for k, v in cfg['estimates'].items()}


def rot(a, b):
    a = a / np.linalg.norm(a); b = b / np.linalg.norm(b)
    v = np.cross(a, b); c = float(a @ b); sn = np.linalg.norm(v)
    if sn < 1e-9: return np.eye(3)
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + K + K @ K * ((1 - c) / sn ** 2)


def seg_map(ea, eb, ja, jb):
    """affine: ea->ja, eb->jb, rotation + axial stretch"""
    u = eb - ea; L = np.linalg.norm(u); u = u / L
    k = np.linalg.norm(jb - ja) / L
    Rm = rot(u, jb - ja)
    S = np.eye(3) + (k - 1) * np.outer(u, u)
    A_ = Rm @ S
    return A_, ja - A_ @ ea


# torso: Kabsch of pelvis/shoulders -> MM9
src = np.array([E['pelvis'], E['L UpperArm'], E['R UpperArm'], E['neck']]); dst = np.array([J['Pelvis'], J['L UpperArm'], J['R UpperArm'], J['Neck']])
sc, dc = src.mean(0), dst.mean(0)
H = (src - sc).T @ (dst - dc); U, _, Vt = np.linalg.svd(H); Rt = Vt.T @ np.diag([1, 1, np.sign(np.linalg.det(Vt.T @ U.T))]) @ U.T
print('torso rot deg', np.degrees(np.arccos((np.trace(Rt) - 1) / 2)))
Tt = (Rt, dc - Rt @ sc)
SEGS = {}
for s_ in 'LR':
    SEGS[f'{s_} UpperArm'] = seg_map(E[f'{s_} UpperArm'], E[f'{s_} Forearm'], J[f'{s_} UpperArm'], J[f'{s_} Forearm'])
    SEGS[f'{s_} Forearm'] = seg_map(E[f'{s_} Forearm'], E[f'{s_} Hand'], J[f'{s_} Forearm'], J[f'{s_} Hand'])
    # hand: keep length, direction to MM9's finger root
    ej = J[f'{s_} Hand'] + (J[f'{s_} Finger1'] - J[f'{s_} Hand']) / np.linalg.norm(J[f'{s_} Finger1'] - J[f'{s_} Hand']) * np.linalg.norm(E[f'{s_} Knuckle'] - E[f'{s_} Hand']) * cfg.get('hand_scale', 1.0)
    SEGS[f'{s_} Hand'] = seg_map(E[f'{s_} Hand'], E[f'{s_} Knuckle'], J[f'{s_} Hand'], ej)
    SEGS[f'{s_} Thigh'] = seg_map(E[f'{s_} Thigh'], E[f'{s_} Calf'], J[f'{s_} Thigh'], J[f'{s_} Calf'])
    SEGS[f'{s_} Calf'] = seg_map(E[f'{s_} Calf'], E[f'{s_} Foot'], J[f'{s_} Calf'], J[f'{s_} Foot'])
    SEGS[f'{s_} Foot'] = seg_map(E[f'{s_} Foot'], E[f'{s_} Toe0'], J[f'{s_} Foot'], J[f'{s_} Toe0'])
names = list(SEGS)
ends = {f'{s_} UpperArm': (f'{s_} UpperArm', f'{s_} Forearm') for s_ in 'LR'}
ends.update({f'{s_} Forearm': (f'{s_} Forearm', f'{s_} Hand') for s_ in 'LR'})
ends.update({f'{s_} Hand': (f'{s_} Hand', f'{s_} Knuckle') for s_ in 'LR'})
ends.update({f'{s_} Thigh': (f'{s_} Thigh', f'{s_} Calf') for s_ in 'LR'})
ends.update({f'{s_} Calf': (f'{s_} Calf', f'{s_} Foot') for s_ in 'LR'})
ends.update({f'{s_} Foot': (f'{s_} Foot', f'{s_} Toe0') for s_ in 'LR'})


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
        ok &= PART != 0
        ok &= (PART == 1) | (PART == 4) | (PART == 5)
        if 'Thigh' in b: ok &= (P[:, 2] < 0.13) | (d < 0.06)
    else:
        ok &= PART == 0
    if 'Hand' in b:
        d = np.where(t < 0, d + 0.02, d)     # the forearm owns what lies before the wrist
    D[:, i] = np.where(ok, d, 1e3)
best = D.argmin(1); dbest = D.min(1)
lab = np.zeros((n, len(names) + 1))
rad = {'UpperArm': 0.10, 'Forearm': 0.08, 'Hand': 0.14, 'Thigh': 0.16, 'Calf': 0.14, 'Foot': 0.2}
free = np.array([dbest[i] < rad[names[best[i]].split()[1]] for i in range(n)])
# past the shoulder joint plane the torso owns the vertex
for s_ in 'LR':
    b = f'{s_} UpperArm'; o = E[b]; u = E[f'{s_} Forearm'] - o; u = u / np.linalg.norm(u)
    i = names.index(b)
    free &= ~((best == i) & ((P - o) @ u < -0.01))
lab[np.arange(n), np.where(free, best + 1, 0)] = 1
for _ in range(cfg.get('blend_iters', 8)):
    avg = np.array([lab[nb].mean(0) if nb else lab[i] for i, nb in enumerate(nbr)])
    lab = 0.5 * lab + 0.5 * avg
# the base: torso rigid above the waist, the pelvis parts identity (with its small offset)
tw = np.clip((P[:, 2] - 0.2) / 0.2, 0, 1); tw = tw * tw * (3 - 2 * tw)
Pel = J['Pelvis'] - E['pelvis']
base = (P @ Tt[0].T + Tt[1]) * tw[:, None] + (P + Pel) * (1 - tw[:, None])
Q = lab[:, :1] * base
for i, b in enumerate(names):
    A_, t_ = SEGS[b]
    Q = Q + lab[:, i + 1:i + 2] * (P @ A_.T + t_)
# loose shin and foot: rigid with their segment
for part, b in ((4, 'R Calf'), (5, 'R Foot')):
    pass
P = Q
print('floor', P[:, 2].min(), 'bbox', P.min(0), P.max(0))
for v, p in zip(me.vertices, P): v.co = Vector(p)
pa = me.attributes.new('part', 'INT', 'POINT'); pa.data.foreach_set('value', PART.tolist())
me.update()
# upper body: head cut at the neck, left half mirrored over the right (MM9's upper body is symmetric; Meshy's 3/4 master is not)
bm = bmesh.new(); bm.from_mesh(me)
lay = bm.verts.layers.int['part']


def upper(bm):
    vs = [v for v in bm.verts if v[lay] == 0]
    es = list({e for v in vs for e in v.link_edges}); fs = list({f for v in vs for f in v.link_faces})
    return vs + es + fs


cut = float(__import__('os').environ.get('NECKCUT', cfg['neck_cut_z']))
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v[lay] == 3 and v.co.z > 0.6], context='VERTS')      # Meshy's own eyes and teeth
bmesh.ops.bisect_plane(bm, geom=upper(bm), plane_co=(0, 0, cut), plane_no=(0, 0, 1), clear_outer=True)
bmesh.ops.bisect_plane(bm, geom=upper(bm), plane_co=(0, 0, 0), plane_no=(1, 0, 0), clear_inner=True, dist=1e-5)
g = upper(bm)
for v in bm.verts:
    if v[lay] == 0 and abs(v.co.x) < 1e-4: v.co.x = 0
ret = bmesh.ops.mirror(bm, geom=g, axis='X', merge_dist=1e-4)
bmesh.ops.recalc_face_normals(bm, faces=[f for f in bm.faces if f.verts[0][lay] == 0])
bm.to_mesh(me); bm.free()
print('SYM verts', len(me.vertices), 'tris', sum(len(p.vertices) - 2 for p in me.polygons))
np.savez(OUT + '.joints.npz', **{k: v for k, v in J.items()})
bpy.ops.wm.save_as_mainfile(filepath=OUT)
