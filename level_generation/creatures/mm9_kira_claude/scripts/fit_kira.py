# Kira: from mm9_njam_claude/scripts/fit_nj.py. Every joint the config does not place (Finger12, the socket nodes Lhand1/Rhand1, the braid
# chain Yp*, the fringe Ybang*) follows its parent: its MM9 offset turned by the parent's rest turn (Njam's left them at MM9's positions).
"""Rest pose of the MM9 skeleton on the cleaned body, the mesh is not moved. MM9's own rest is a walking stance (right leg 15 cm forward) and its arms differ from Meshy's by 10-18 deg, so a transient skin
would bend the hips and shoulders. Instead each limb bone keeps MM9's frame rotated by the least rotation onto our limb (`cloned source frames`, humanoid playbook G3). The clips copy MM9's local rotations, so the bones
take MM9's world rotations exactly, the bind matrices come from this rest, and our mesh follows. Feet turn by yaw only, so soles stay level where MM9's are. Spine, neck and head are translated.
Args: <clean blend> <config json> <out blend> <report json>"""
import bpy, sys, json
import numpy as np
from mathutils import Vector, Matrix
SRC, CFG, OUT, REP = sys.argv[sys.argv.index('--') + 1:]
cfg = json.load(open(CFG)); rep = {}
bpy.ops.wm.open_mainfile(filepath=SRC)
arm = bpy.data.objects['MM9_Rig']
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o.name != 'Body': bpy.data.objects.remove(o)
J = {b.name: np.array(tuple(arm.matrix_world @ b.head_local)) for b in arm.data.bones}
children = {}
for b in arm.data.bones: children[b.name] = [c.name for c in b.children]


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
newJ = {k: np.array(v, float) for k, v in cfg['centre'].items()}
for k, v in cfg['fixed'].items():
    for S, f in (('R', [1, 1, 1]), ('L', [-1, 1, 1])):
        newJ[k.replace('{S}', S)] = np.array(v, float) * f
D = {}
for S in 'RL':
    B = f'Bip01 {S} '
    D[B + 'Clavicle'] = rot_between(J[B + 'UpperArm'] - J[B + 'Clavicle'], E[B + 'UpperArm'] - newJ[B + 'Clavicle'])
    for a, b in (('UpperArm', 'Forearm'), ('Forearm', 'Hand'), ('Thigh', 'Calf'), ('Calf', 'Foot')):
        D[B + a] = rot_between(J[B + b] - J[B + a], E[B + b] - E[B + a]); newJ[B + a] = E[B + a].copy()
    newJ[B + 'Hand'] = E[B + 'Hand'].copy(); newJ[B + 'Foot'] = E[B + 'Foot'].copy()
    D[B + 'Hand'] = rot_between(J[B + 'Finger1'] - J[B + 'Hand'], E['Tip' + S] - E[B + 'Hand'])
    a0 = J[B + 'Toe0'] - J[B + 'Foot']; a1 = E['Toe' + S] - E[B + 'Foot']
    ang = np.arctan2(a1[1], a1[0]) - np.arctan2(a0[1], a0[0]); c, s_ = np.cos(ang), np.sin(ang)
    D[B + 'Foot'] = np.array([[c, -s_, 0], [s_, c, 0], [0, 0, 1]])
    newJ[B + 'Toe0'] = E['Toe' + S].copy()
    D[B + 'Toe0'] = D[B + 'Foot']
    for c_ in ('Finger0', 'Finger01', 'Finger1', 'Finger11', 'Finger12'):
        D[B + c_] = D[B + 'Hand']
        newJ[B + c_] = newJ[B + 'Hand'] + D[B + 'Hand'] @ (J[B + c_] - J[B + 'Hand']) * 0.9
rep['rest_turn_deg'] = {b: round(float(np.degrees(np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1)))), 1) for b, R in D.items()}
parent = {b.name: (b.parent.name if b.parent else None) for b in arm.data.bones}
def place(n):
    if n in newJ: return
    p = parent[n]
    if p is None: newJ[n] = J[n].copy(); return
    place(p)
    D.setdefault(n, D.get(p, np.eye(3)))
    newJ[n] = newJ[p] + D.get(p, np.eye(3)) @ (J[n] - J[p])
for n in J: place(n)
rep['joint_moves_cm'] = {n: round(float(np.linalg.norm(newJ[n] - J[n]) * 100), 1) for n in J}
bpy.context.view_layer.objects.active = arm
for o in bpy.data.objects: o.select_set(o is arm)
bpy.ops.object.mode_set(mode='EDIT')
Mw = np.array(arm.matrix_world); Mi = np.linalg.inv(Mw)
for eb in arm.data.edit_bones:
    n = eb.name
    Mb = Mw @ np.array(eb.matrix)
    R = D.get(n, np.eye(3)) @ Mb[:3, :3]
    Mn = np.eye(4); Mn[:3, :3] = R; Mn[:3, 3] = newJ[n]
    Ml = Mi @ Mn
    L = eb.length
    eb.matrix = Matrix(Ml.tolist())
    eb.length = L
bpy.ops.object.mode_set(mode='OBJECT')
bpy.context.view_layer.update()
chk = max(float(np.linalg.norm(np.array(tuple(arm.matrix_world @ arm.data.bones[n].head_local)) - newJ[n])) for n in newJ)
rep['joint_error_mm'] = round(chk * 1000, 3)
json.dump({n: newJ[n].tolist() for n in J}, open(OUT + '.joints.json', 'w'), indent=0)
json.dump({n: D[n].tolist() for n in D}, open(OUT + '.delta.json', 'w'), indent=0)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1)
print('FIT ' + json.dumps({k: v for k, v in rep.items() if k != 'joint_moves_cm'})[:900])
