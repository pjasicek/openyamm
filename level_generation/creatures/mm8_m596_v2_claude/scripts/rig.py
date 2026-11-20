"""Rig the prepared crystal body: the installed walker's bone hierarchy and names plus clavicles (Left/RightShoulder, review 2: the raised arm twisted the shoulder) (sockets RightHand/LeftHand,
upper body Waist, look Neck/Head) on joints fitted to this mesh (work/joints_v1.json), automatic (heat) weights,
then rules: each side's limbs only on its own side, claws wholly on the hand, crown/beak wholly on the head, at
most 4 influences, normalised. Usage: blender -b -P rig.py -- <mesh.blend> <joints.json> <out.blend>"""
import json, os, sys, bpy
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]; src, jfile, dst = a
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
J = {k: Vector(v) for k, v in json.load(open(os.path.join(P, jfile))).items()}
PARENT = {'Hips': 'Root', 'Waist': 'Hips', 'Chest': 'Waist', 'Neck': 'Chest', 'Head': 'Neck'}
for s in ('Left', 'Right'):
    PARENT.update({s + 'Shoulder': 'Chest', s + 'Arm': s + 'Shoulder', s + 'ForeArm': s + 'Arm', s + 'Hand': s + 'ForeArm',
                   s + 'Thigh': 'Hips', s + 'Shin': s + 'Thigh', s + 'Foot': s + 'Shin'})
ORDER = ['Root', 'Hips', 'Waist', 'Chest', 'Neck', 'Head'] + [s + p for s in ('Left', 'Right') for p in
         ('Shoulder', 'Arm', 'ForeArm', 'Hand', 'Thigh', 'Shin', 'Foot')]
TAIL = {'Root': J['Root'] + Vector((0, 0, .15)), 'Hips': J['Waist'], 'Waist': J['Chest'], 'Chest': J['Neck'],
        'Neck': J['Head'], 'Head': J['Head'] + Vector((0, -.06, .2))}
for s, g in (('Left', 1), ('Right', -1)):
    TAIL.update({s + 'Shoulder': J[s + 'Arm'], s + 'Arm': J[s + 'ForeArm'], s + 'ForeArm': J[s + 'Hand'], s + 'Hand': J[s + 'Hand'] + Vector((g * .04, -.03, -.2)),
                 s + 'Thigh': J[s + 'Shin'], s + 'Shin': J[s + 'Foot'], s + 'Foot': J[s + 'Foot'] + Vector((0, -.16, -.16))})
bpy.ops.wm.open_mainfile(filepath=os.path.join(P, src))
body = bpy.data.objects['CrystalWalker']
hg = body.vertex_groups.get('HeadRigid')     # round 3: the authored head, crown and eyes move rigidly with Head
HEAD_RIGID = set()
if hg is not None:
    HEAD_RIGID = {v.index for v in body.data.vertices if any(g.group == hg.index for g in v.groups)}
    body.vertex_groups.remove(hg)
arm = bpy.data.armatures.new('CrystalRig'); rig = bpy.data.objects.new('CrystalRig', arm)
bpy.context.scene.collection.objects.link(rig); bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
for n in ORDER:
    b = arm.edit_bones.new(n); b.head = J[n]; b.tail = TAIL[n]
    if n in PARENT:
        b.parent = arm.edit_bones[PARENT[n]]
    b.use_connect = False
# roll: local Z toward -Y (forward) where possible, so bone frames are tidy
for b in arm.edit_bones:
    b.align_roll(Vector((0, -1, 0)) if abs((b.tail - b.head).normalized().y) < .9 else Vector((0, 0, 1)))
arm.edit_bones['Root'].use_deform = False
bpy.ops.object.mode_set(mode='OBJECT')
for o in bpy.context.view_layer.objects:
    o.select_set(o in (body, rig))
bpy.context.view_layer.objects.active = rig
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
vg = {g.index: g.name for g in body.vertex_groups}
empty = [v.index for v in body.data.vertices if not v.groups]
print('AUTO weights: vertices without weight', len(empty))
# rule pass
import numpy as np
co = np.array([v.co[:] for v in body.data.vertices])
def side_of(name):
    return 1 if name.startswith('Left') else -1 if name.startswith('Right') else 0
W = [dict() for _ in body.data.vertices]
for v in body.data.vertices:
    for g in v.groups:
        if g.weight > 1e-4:
            W[v.index][vg[g.group]] = g.weight
hand_z = J['LeftHand'].z; head_z = J['Head'].z
for i, w in enumerate(W):
    x, y, z = co[i]
    # side rule: limb weights only on the vertex's own side (beyond 4 cm of the centre line)
    if abs(x) > .04:
        for n in list(w):
            if side_of(n) and side_of(n) != (1 if x > 0 else -1):
                del w[n]
    # claws and palm below the wrist: hand only
    s = 'Left' if x > 0 else 'Right'
    if abs(x) > .40 and .40 < z < J[s + 'Hand'].z - .03:
        W[i] = {s + 'Hand': 1.0}; continue
    if i in HEAD_RIGID:
        W[i] = {'Head': 1.0}; continue
    # head mass: above the head joint and ahead of the neck
    if z > head_z + .02 and abs(x) < .2 and not HEAD_RIGID:
        W[i] = {'Head': 1.0}; continue
    if z < .40:   # legs and feet: no arm or hand weight
        w = {n: x_ for n, x_ in w.items() if not n.endswith(('Arm', 'Hand'))}; W[i] = w
    if not w:
        # nearest bone head as a fallback
        n = min(J, key=lambda k: (Vector(co[i]) - J[k]).length if k != 'Root' else 9)
        W[i] = {n: 1.0}
# smooth the rule boundaries once by averaging with mesh neighbours, then cap to 4 influences
nbr = [[] for _ in W]
for e in body.data.edges:
    a_, b_ = e.vertices; nbr[a_].append(b_); nbr[b_].append(a_)
for _ in range(2):
    new = []
    for i, w in enumerate(W):
        acc = dict(w)
        for j in nbr[i]:
            for n, x in W[j].items():
                acc[n] = acc.get(n, 0) + x * .5
        tot = sum(acc.values()); new.append({n: x / tot for n, x in acc.items()})
    # keep the hard rules hard
    for i in range(len(W)):
        x, y, z = co[i]; s = 'Left' if x > 0 else 'Right'
        if abs(x) > .40 and .40 < z < J[s + 'Hand'].z - .06:
            new[i] = {s + 'Hand': 1.0}
        if i in HEAD_RIGID or (z > head_z + .05 and abs(x) < .2 and not HEAD_RIGID):
            new[i] = {'Head': 1.0}
        if abs(x) > .04:
            new[i] = {n: x_ for n, x_ in new[i].items() if not side_of(n) or side_of(n) == (1 if x > 0 else -1)}
        if z < .40:
            new[i] = {n: x_ for n, x_ in new[i].items() if not n.endswith(('Arm', 'Hand'))} or new[i]
    W = new
for g in list(body.vertex_groups):
    body.vertex_groups.remove(g)
groups = {n: body.vertex_groups.new(name=n) for n in ORDER if n != 'Root'}
for i, w in enumerate(W):
    top = sorted(w.items(), key=lambda t: -t[1])[:4]; tot = sum(x for _, x in top)
    for n, x in top:
        if x / tot > .02:
            groups[n].add([i], x / tot, 'REPLACE')
print('RIG bones', len(arm.bones), 'max influences 4')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(P, dst))
