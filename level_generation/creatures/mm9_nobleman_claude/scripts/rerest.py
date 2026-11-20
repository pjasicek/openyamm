"""The rig's rest frames from the corrected true-handed source (mirror_glb.py: S M S on every node; mirror_source.py had applied the partner bone's motion to this bone's rest, which stretched the legs on MM9's asymmetric bind). Mesh, weights, UVs and joint positions stay;
each MM9 bone takes the new source frame turned by the least rotation onto our limb, as fit_hw.py; helpers `_h` follow their bone. Args: <in blend> <new true glb> <fit config> <out blend> <delta json>"""
import bpy, sys, json
import numpy as np
from mathutils import Matrix
IN, GLB, CFG, OUT, DELTA = sys.argv[sys.argv.index('--') + 1:]
cfg = json.load(open(CFG))
bpy.ops.wm.open_mainfile(filepath=IN)
rig = bpy.data.objects['MM9_Rig']
keep = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=GLB)
new = [o for o in bpy.data.objects if o not in keep]
src = next(o for o in new if o.type == 'ARMATURE')
if src.animation_data: src.animation_data.action = None
F = {b.name: np.array(src.matrix_world) @ np.array(b.matrix_local) for b in src.data.bones}
J = {n: m[:3, 3].copy() for n, m in F.items()}
for o in new: bpy.data.objects.remove(o)
def rot_between(a, b):
    a = a / np.linalg.norm(a); b = b / np.linalg.norm(b)
    v = np.cross(a, b); c = float(a @ b); s_ = np.linalg.norm(v)
    if s_ < 1e-9: return np.eye(3)
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + K + K @ K * ((1 - c) / s_ ** 2)
E = {}
for k, v in cfg['estimates'].items():
    E[k] = np.array(v, float)
    if ' R ' in k: E[k.replace(' R ', ' L ')] = np.array(v, float) * [-1, 1, 1]
fixed = {}
for k, v in cfg['fixed'].items():
    for S, f in (('R', [1, 1, 1]), ('L', [-1, 1, 1])): fixed[k.replace('{S}', S)] = np.array(v, float) * f
D = {}
for S in 'RL':
    B = f'Bip01 {S} '
    D[B + 'Clavicle'] = rot_between(J[B + 'UpperArm'] - J[B + 'Clavicle'], E[B + 'UpperArm'] - fixed[B + 'Clavicle'])
    for a, b in (('UpperArm', 'Forearm'), ('Forearm', 'Hand'), ('Thigh', 'Calf'), ('Calf', 'Foot')):
        D[B + a] = rot_between(J[B + b] - J[B + a], E[B + b] - E[B + a])
    D[B + 'Hand'] = rot_between(J[B + 'Finger1'] - J[B + 'Hand'], E['Tip' + S] - E[B + 'Hand'])
    a0 = J[B + 'Toe0'] - J[B + 'Foot']; a1 = E['Toe' + S] - E[B + 'Foot']
    ang = np.arctan2(a1[1], a1[0]) - np.arctan2(a0[1], a0[0]); c, s_ = np.cos(ang), np.sin(ang)
    D[B + 'Foot'] = np.array([[c, -s_, 0], [s_, c, 0], [0, 0, 1]])
    D[B + 'Toe0'] = D[B + 'Foot']; D[B + 'Toe01'] = D[B + 'Foot']
    for c_ in ('Finger1', 'Finger02'): D[B + c_] = D[B + 'Hand']
    D['Ybasesword' if S == 'R' else 'Ybasedagger'] = D[B + 'Hand']
print('REST turn deg', {b: round(float(np.degrees(np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1)))), 1) for b, R in D.items() if 'Toe' not in b and 'Finger' not in b and 'Ybase' not in b})
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects: o.select_set(o is rig)
bpy.ops.object.mode_set(mode='EDIT')
Mw = np.array(rig.matrix_world); Mi = np.linalg.inv(Mw)
n_set = 0
for eb in rig.data.edit_bones:
    base = eb.name[:-2] if eb.name.endswith('_h') else eb.name
    if base not in F: continue
    head = Mw @ np.r_[np.array(eb.head), 1]
    Mn = np.eye(4); Mn[:3, :3] = D.get(base, np.eye(3)) @ F[base][:3, :3]; Mn[:3, 3] = head[:3]
    L = eb.length
    eb.matrix = Matrix((Mi @ Mn).tolist()); eb.length = L
    n_set += 1
bpy.ops.object.mode_set(mode='OBJECT')
json.dump({n: D[n].tolist() for n in D}, open(DELTA, 'w'), indent=0)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('REREST bones', n_set)
