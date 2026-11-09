"""Rigid-piece fit of the Meshy skeleton to the MM9 SKELETON rig (true handedness, mirror_source.py), from fit_skelwar.py.
Bones do not bend, so every piece is rigid on one joint where it can be, and MM9's joints move onto the places where the pieces meet (translated only, rest
rotations stay, so MM9's local rotations play unchanged):
- arms: shoulder in the humeral head, elbow in the elbow knob, wrist in the carpal knot; legs: hip in the femoral head, knee in the knee knob, ankle in the talus;
- the vertebral column blends over Spine/Spine1/Spine2/Spine3, neck between Neck and Head; ribcage, sternum, vest, strap and back panel share one field Spine2 -> Spine3
  (MM9's torso flexes up to 19 deg there); pelvis, rope and femoral heads' sockets rigid on Spine, the parent of the thighs in MM9;
- hip scraps: here belt -> thigh; finish_skel.py makes them rigid on the thigh;
- five bone fingers of separate phalanges: three bones per finger, two for the thumb (14 per side), MM9's hand has mitten bones only.
The HD pose is not MM9's bind (MM9's arms are nearly level, its legs wider), so each piece is then turned onto the MM9 bone direction about its own joint, chain by chain, keeping
our lengths. The HD-pose position stays in the POINT attribute `fitco` for the Meshy upload.
Writes object 'Body' parented to 'MM9_Rig', report json. Args: <sym blend> <mm9 true glb> <out blend> <report json>"""
import bpy, sys, json
import numpy as np
from mathutils import Vector, Matrix, Quaternion
argv = sys.argv[sys.argv.index('--') + 1:]
IN, MM9, OUT, REP = argv[:4]
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Parts']; body.name = 'Body'; me = body.data; me.name = 'Body'
bpy.ops.import_scene.gltf(filepath=MM9)
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE'); rig.name = 'MM9_Rig'
if rig.animation_data: rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o is not body: bpy.data.objects.remove(o)
bpy.context.view_layer.update()
co = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices])
pid = np.zeros(len(co), np.int32); me.attributes['pid'].data.foreach_get('value', pid)
W = rig.matrix_world; IW = W.inverted()
RJ = lambda n: np.array(W @ rig.data.bones[n].head_local)
rep = {}
bones = rig.data.bones
pts = lambda *ids: co[np.isin(pid, ids)]
cen = lambda *ids: pts(*ids).mean(0)
box = lambda *ids: (pts(*ids).min(0) + pts(*ids).max(0)) / 2


def pca(v):
    c = v.mean(0); u, s, vt = np.linalg.svd(v - c, full_matrices=False); return c, vt[0]


def meet(a, b):
    """mid of the closest vertices of two pieces"""
    A, B = pts(a), pts(b)
    d = ((A[:, None] - B[None]) ** 2).sum(-1); i, j = np.unravel_index(np.argmin(d), d.shape)
    return (A[i] + B[j]) / 2


VERT = [83, 0, 61, 10, 92, 68, 126, 115, 38, 31, 102, 64, 25, 123, 78]
vc = np.array(sorted((cen(p) for p in VERT), key=lambda c: c[2]))
col_y = lambda z: float(np.interp(z, vc[:, 2], vc[:, 1]))
T = {}
for n in ('Bip01 Pelvis', 'Bip01 Spine', 'Bip01 Spine1', 'Bip01 Spine2', 'Bip02 Spine3', 'Bip01 Neck', 'Bip01 Head'):
    p = RJ(n); T[n] = np.array([0.0, col_y(p[2]), p[2]])
# pelvis joint and Spine: the belt centre
sh, el, wr = box(81), box(93), (box(149, 150) * 2 + box(74)) / 3
hp, kn, an = box(3), box(26), box(146)
R = {'UpperArm': sh, 'Forearm': el, 'Hand': wr, 'Thigh': hp, 'Calf': kn, 'Foot': an}
MIR = lambda p: p * [-1, 1, 1]
for k, p in R.items():
    T[f'Bip01 R {k}'] = p; T[f'Bip01 L {k}'] = MIR(p)
nk = T['Bip01 Neck']
for s, sg in (('R', -1), ('L', 1)):
    T[f'Bip02 {s} Clavicle'] = np.array([sg * 0.045, nk[1], nk[2]])
rep['joints'] = {k: np.round(v, 4).tolist() for k, v in T.items()}
rep['moved_cm'] = {k: round(float(np.linalg.norm(v - RJ(k))) * 100, 1) for k, v in T.items()}
print('MOVED', rep['moved_cm'])
# fingers: joint at each meeting point; the tip is the far end of the last piece
CHAINS = dict(Thumb=[[33], [90]], Index=[[29], [77], [130, 7]], Middle=[[104], [107], [45]], Ring=[[135], [15], [59]], Pinky=[[136], [67], [111]])
palm = pts(74, 149, 150)
chains = {}
for name, ch in CHAINS.items():
    first = pts(*ch[0])
    d = ((first[:, None] - palm[None]) ** 2).sum(-1); i, j = np.unravel_index(np.argmin(d), d.shape)
    jp = [first[i] * 0.7 + palm[j] * 0.3]
    for a, b in zip(ch[:-1], ch[1:]):
        A, B = pts(*a), pts(*b)
        d = ((A[:, None] - B[None]) ** 2).sum(-1); i, j = np.unravel_index(np.argmin(d), d.shape)
        jp.append((A[i] + B[j]) / 2)
    last = pts(*ch[-1]); jp.append(last[np.argmax(np.linalg.norm(last - jp[-1], axis=1))])
    chains[name] = jp
    print('FINGER', name, np.round(jp, 3).tolist())
rep['fingers'] = {k: [np.round(p, 4).tolist() for p in v] for k, v in chains.items()}


def rotmin(a, b):
    a = a / np.linalg.norm(a); b = b / np.linalg.norm(b)
    return np.array(Vector(a).rotation_difference(Vector(b)).to_matrix())


def slerp_i(R_, t):
    q = Matrix(R_.tolist()).to_quaternion(); ax, an_ = q.to_axis_angle()
    return np.array(Quaternion(ax, an_ * t).to_matrix())


SM = np.diag([-1.0, 1, 1])
follow = {'Bip02 R Finger0': 'Bip01 R Hand', 'Bip02 L Finger0': 'Bip01 L Hand', 'Bip02 R Finger1': 'Bip01 R Hand', 'Bip02 L Finger1': 'Bip01 L Hand',
          'Bip02 R Finger01': 'Bip01 R Hand', 'Bip02 L Finger01': 'Bip01 L Hand', 'Bip02 R Finger11': 'Bip01 R Hand', 'Bip02 L Finger11': 'Bip01 L Hand',
          'Bone01': 'Bip01 R Hand'}
for b_ in bones.keys():
    if 'Toe' in b_: follow[b_] = 'Bip01 R Foot' if ' R ' in b_ else 'Bip01 L Foot'
JF = dict(T)
for k, v in follow.items():
    JF[k] = RJ(k) + (T[v] - RJ(v))
JF['Scene Root'] = RJ('Scene Root')
FNAMES = list(chains)
for name, jp in chains.items():
    for i in range(len(jp) - 1):
        JF[f'Bip01 R {name}{i + 1}'] = jp[i]; JF[f'Bip01 L {name}{i + 1}'] = MIR(jp[i])
CR = {}
up = rotmin(T['Bip01 Neck'] - T['Bip01 Spine'], RJ('Bip01 Neck') - RJ('Bip01 Spine'))
ang = lambda R_: round(float(np.degrees(np.arccos(np.clip((np.trace(R_) - 1) / 2, -1, 1)))), 1)
print('torso turn', ang(up))
for n, R_ in (('Bip01 Spine1', slerp_i(up, 0.5)), ('Bip01 Spine2', up), ('Bip02 Spine3', up), ('Bip01 Neck', up), ('Bip02 R Clavicle', up), ('Bip02 L Clavicle', up)):
    CR[n] = R_
for s_ in 'RL':
    for a_, b_ in (('UpperArm', 'Forearm'), ('Forearm', 'Hand'), ('Thigh', 'Calf'), ('Calf', 'Foot')):
        A, B = f'Bip01 {s_} {a_}', f'Bip01 {s_} {b_}'
        CR[A] = rotmin(T[B] - T[A], RJ(B) - RJ(A))
# the foot: flat in both poses; turned about the vertical onto MM9's toe direction
tg = (RJ('Bip01 R Toe02') + RJ('Bip01 R Toe42')) / 2 if 'Bip01 R Toe02' in bones else None
tg9 = np.mean([RJ(b_) for b_ in bones.keys() if 'Toe' in b_ and ' R ' in b_], 0) - RJ('Bip01 R Foot')
to = cen(19, 98, 48, 43, 55, 62, 125, 128, 133, 101, 73, 138) - T['Bip01 R Foot']
a9, ao = tg9[:2] / np.linalg.norm(tg9[:2]), to[:2] / np.linalg.norm(to[:2])
yaw = np.arctan2(ao[0] * a9[1] - ao[1] * a9[0], ao @ a9)
print('foot yaw deg', round(np.degrees(yaw), 1))
Ry = np.array(Matrix.Rotation(yaw, 3, 'Z')); CR['Bip01 R Foot'] = Ry; CR['Bip01 L Foot'] = SM @ Ry @ SM
# the hand: knuckle line (little finger -> index) along MM9's dagger handle, fingers across it toward the MM9 finger bone
dag = np.load(bpy.path.abspath('//dagger_rest.npz'))
handle = -dag['axis'] / np.linalg.norm(dag['axis'])                     # pommel -> tip at MM9's bind, right hand
F9 = RJ('Bip02 R Finger1') - RJ('Bip01 R Hand'); F9 -= handle * (F9 @ handle); F9 /= np.linalg.norm(F9)
kn_ = chains['Index'][0] - chains['Pinky'][0]; kn_ /= np.linalg.norm(kn_)
fo = chains['Middle'][1] - chains['Middle'][0] + chains['Ring'][1] - chains['Ring'][0]; fo -= kn_ * (fo @ kn_); fo /= np.linalg.norm(fo)
Ro = np.array([kn_, fo, np.cross(kn_, fo)]).T; Rt = np.array([handle, F9, np.cross(handle, F9)]).T
CR['Bip01 R Hand'] = Rt @ Ro.T; CR['Bip01 L Hand'] = SM @ CR['Bip01 R Hand'] @ SM
rep['rest_turn_deg'] = {k: ang(v) for k, v in CR.items()}
print('TURNS', rep['rest_turn_deg'])
for s_ in 'RL':
    for name in FNAMES:
        for i in (1, 2, 3):
            CR[f'Bip01 {s_} {name}{i}'] = CR[f'Bip01 {s_} Hand']
    for n in ('Finger0', 'Finger01', 'Finger1', 'Finger11'):
        CR[f'Bip02 {s_} {n}'] = CR[f'Bip01 {s_} Hand']
    for b_ in bones.keys():
        if 'Toe' in b_ and f' {s_} ' in b_: CR[b_] = CR[f'Bip01 {s_} Foot']
CR['Bone01'] = CR['Bip01 R Hand']
I3 = np.eye(3); JR = {}; FPAR = {}
for s_ in 'RL':
    for name, jp in chains.items():
        FPAR[f'Bip01 {s_} {name}1'] = f'Bip01 {s_} Hand'
        for i in range(2, len(jp)): FPAR[f'Bip01 {s_} {name}{i}'] = f'Bip01 {s_} {name}{i - 1}'


def rest_of(n):
    if n in JR: return JR[n]
    par = FPAR.get(n) or (bones[n].parent.name if bones[n].parent else None)
    if par is None or n == 'Bip01 Pelvis':
        JR[n] = RJ(n) if n in bones else JF[n]
        if n == 'Bip01 Pelvis': JR[n] = T[n].copy()
    else:
        JR[n] = rest_of(par) + CR.get(par, I3) @ (JF[n] - JF[par])
    return JR[n]


for n in list(bones.keys()) + list(FPAR): rest_of(n)
rep['rest_joints'] = {k: np.round(v, 4).tolist() for k, v in JR.items()}
for s_ in 'R':
    print('REST', s_, {k: np.round(JR[f'Bip01 {s_} {k}'], 3).tolist() for k in ('UpperArm', 'Hand', 'Calf', 'Foot')}, 'MM9', np.round(RJ(f'Bip01 {s_} Hand'), 3), np.round(RJ(f'Bip01 {s_} Foot'), 3))
TIPS = {}
for name, jp in chains.items():
    k = len(jp) - 1
    TIPS[f'Bip01 R {name}{k}'] = JR[f'Bip01 R {name}{k}'] + CR['Bip01 R Hand'] @ (jp[-1] - jp[-2])
    TIPS[f'Bip01 L {name}{k}'] = JR[f'Bip01 L {name}{k}'] + CR['Bip01 L Hand'] @ (MIR(jp[-1]) - MIR(jp[-2]))
bpy.ops.object.select_all(action='DESELECT'); rig.select_set(True); bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
ebs = rig.data.edit_bones
for n in bones.keys():
    if n in JR:
        eb = ebs[n]; d = Vector(IW @ Vector(JR[n])) - eb.head
        eb.head += d; eb.tail += d
for s_ in 'RL':
    for name, jp in chains.items():
        par = ebs[f'Bip01 {s_} Hand']; nb = len(jp) - 1
        for i in range(1, nb + 1):
            n = f'Bip01 {s_} {name}{i}'; eb = ebs.new(n)
            eb.head = IW @ Vector(JR[n])
            eb.tail = IW @ Vector(JR[f'Bip01 {s_} {name}{i + 1}'] if i < nb else TIPS[n])
            eb.parent = par; eb.use_connect = False; par = eb
bpy.ops.object.mode_set(mode='OBJECT')
bpy.context.view_layer.update()
# --- weights
for g in list(body.vertex_groups): body.vertex_groups.remove(g)
n = len(co); WT = {}


def add(bone, ids, w=1.0):
    WT.setdefault(bone, np.zeros(n))[ids] += w


def ramp(z, joints, soft):
    zs = np.array([j[1] for j in joints]); out = np.zeros((len(z), len(joints))); out[:, 0] = 1
    for i in range(1, len(joints)):
        t = np.clip((z - zs[i] + soft) / (2 * soft), 0, 1); t = t * t * (3 - 2 * t)
        out[:, i] = t; out[:, :i] *= (1 - t)[:, None]
    return out


def mir(ids):
    return list(ids) + [i + 1000 for i in ids]


def rigid(ids, b):
    """right piece and its mirror on the matching bones"""
    add(f'Bip01 R {b}', np.where(np.isin(pid, ids))[0]); add(f'Bip01 L {b}', np.where(np.isin(pid, [i + 1000 for i in ids]))[0])


rigid([81, 44, 93], 'UpperArm'); rigid([76, 6, 41, 54], 'Forearm')
rigid([74, 149, 150], 'Hand')
for name, ch in CHAINS.items():
    for i, c in enumerate(ch): rigid(c, f'{name}{i + 1}')
rigid([3, 65], 'Thigh'); rigid([26, 143, 30, 108, 11], 'Calf')
FOOT = [146, 87, 22, 105, 62, 125, 138, 55, 73, 43, 101, 48, 133, 79, 129, 98, 19, 128]
rigid(FOOT, 'Foot')
add('Bip01 Spine', np.where(np.isin(pid, [36, 13, 83, 0]))[0])
# column and neck
ids = np.where(np.isin(pid, [61, 10, 92, 68, 126, 115, 38, 31, 102, 25]))[0]
js = [('Bip01 Spine', 0), ('Bip01 Spine1', T['Bip01 Spine1'][2]), ('Bip01 Spine2', T['Bip01 Spine2'][2]), ('Bip02 Spine3', T['Bip02 Spine3'][2]), ('Bip01 Neck', T['Bip01 Neck'][2])]
r = ramp(co[ids, 2], js, 0.05)
for i, j in enumerate(js): add(j[0], ids, 0); WT[j[0]][ids] += r[:, i]
ids = np.where(np.isin(pid, [123, 78]))[0]
js = [('Bip01 Neck', 0), ('Bip01 Head', T['Bip01 Head'][2])]
r = ramp(co[ids, 2], js, 0.03)
for i, j in enumerate(js): add(j[0], ids, 0); WT[j[0]][ids] += r[:, i]
# ribcage, vest and strap: one field
TORSO = mir([57, 100, 82, 50, 2, 47]) + [18, 97, 64, 14, 95, 124, 300, 301]
ids = np.where(np.isin(pid, TORSO))[0]
js = [('Bip01 Spine2', 0), ('Bip02 Spine3', T['Bip02 Spine3'][2] - 0.02)]
r = ramp(co[ids, 2], js, 0.09)
for i, j in enumerate(js): add(j[0], ids, 0); WT[j[0]][ids] += r[:, i]
add('Bip01 Head', np.where(pid >= 2000)[0])
# hip scraps: belt -> thigh
SCR = [52, 142, 134, 109, 144, 127]
for s_, ids_ in (('R', SCR), ('L', [i + 1000 for i in SCR])):
    ids = np.where(np.isin(pid, ids_))[0]
    hip = T[f'Bip01 {s_} Thigh']; ax = T[f'Bip01 {s_} Calf'] - hip; ax /= np.linalg.norm(ax)
    t = np.clip(((co[ids] - hip) @ ax + 0.03) / 0.16, 0, 1); t = t * t * (3 - 2 * t)
    add('Bip01 Spine', ids, 0); WT['Bip01 Spine'][ids] += 1 - t
    add(f'Bip01 {s_} Thigh', ids, 0); WT[f'Bip01 {s_} Thigh'][ids] += t
tot = sum(WT.values())
bad = (tot < .99) | (tot > 1.01)
assert not bad.any(), (tot.min(), tot.max(), np.unique(pid[bad]))
for b, w in WT.items():
    g = body.vertex_groups.new(name=b)
    nz = np.where(w > 1e-3)[0]
    for lvl in np.unique(np.round(w[nz], 3)):
        g.add(nz[np.round(w[nz], 3) == lvl].tolist(), float(lvl), 'REPLACE')
a_ = me.attributes.new('fitco', 'FLOAT_VECTOR', 'POINT'); a_.data.foreach_set('vector', co.ravel())
new = np.zeros_like(co)
for b, w in WT.items():
    nz = np.where(w > 0)[0]
    new[nz] += w[nz, None] * (JR[b] + (co[nz] - JF[b]) @ CR.get(b, I3).T)
bm_w = np.linalg.inv(np.array(body.matrix_world))
hom = np.c_[new, np.ones(len(new))] @ bm_w.T
me.vertices.foreach_set('co', hom[:, :3].ravel()); me.update()
print('REST bounds', new.min(0), new.max(0), 'height', new[:, 2].max() - new[:, 2].min())
body.parent = rig
m = body.modifiers.get('Armature') or body.modifiers.new('Armature', 'ARMATURE'); m.object = rig
rep['weights_bones'] = sorted(WT)
json.dump(rep, open(REP, 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('FIT done', len(me.polygons))
