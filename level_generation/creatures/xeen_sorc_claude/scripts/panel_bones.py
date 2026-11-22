"""Cloth panel bones (sorceress G6: with the panels skinned to an even pelvis/thigh mixture the forward thigh came 16 cm
through the front panel in Walking and 20 cm in Running, the backward thigh 13 cm through the back panel).
Adds B_PanelFront and B_PanelBack (children of B_Pelvis, heads at the top centre of each panel, pointing down) and bakes
their rotation into every action: about the pelvis's lateral axis, the front panel swings forward with the more flexed
thigh (KF x the larger forward flexion of the two thighs relative to the pelvis, from their rest direction), the back
panel backward with the more extended thigh (KB x the larger extension). The panel vertices are weighted to these
bones by weights_fix.py (pelvis at the girdle, ramping onto the panel bone below it).
Env KF (default 1.05), KB (default 1.0). Args: -- <in blend> <out blend>"""
import bpy, sys, os, math
import numpy as np
from mathutils import Vector, Quaternion
src, out = sys.argv[sys.argv.index('--') + 1:]
KF = float(os.environ.get('KF', '1.05')); KB = float(os.environ.get('KB', '1.0'))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
co = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices])
TOP = {}
for name, piece in (('B_PanelFront', 4), ('B_PanelBack', 6)):
    c = co[pv == piece]; zt = c[:, 2].max()
    top = c[c[:, 2] > zt - 0.03]
    TOP[name] = (Vector((float(top[:, 0].mean()), float(top[:, 1].mean()), float(zt))), float(zt - c[:, 2].min()))
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones
for name, (head, length) in TOP.items():
    b = eb.get(name) or eb.new(name)
    b.head = head; b.tail = head + Vector((0, 0, -length)); b.roll = 0.0
    b.parent = eb['B_Pelvis']; b.use_deform = True
bpy.ops.object.mode_set(mode='OBJECT')
for name in TOP:
    if name not in body.vertex_groups:
        body.vertex_groups.new(name=name)
X = Vector((1, 0, 0))
pel = rig.data.bones['B_Pelvis']
AXP = (pel.matrix_local.inverted().to_3x3() @ X).normalized()            # lateral axis in the pelvis frame
LOC = {n: (rig.data.bones[n].matrix_local.inverted().to_3x3() @ X).normalized() for n in TOP}
V0 = {}
for s in 'LR':
    h, k = rig.data.bones[f'B_{s}_Thigh'].head_local, rig.data.bones[f'B_{s}_Calf'].head_local
    V0[s] = pel.matrix_local.inverted().to_3x3() @ (k - h)


def flex(s):
    pm = rig.pose.bones['B_Pelvis'].matrix
    h, k = rig.pose.bones[f'B_{s}_Thigh'].head, rig.pose.bones[f'B_{s}_Calf'].head
    v = pm.inverted().to_3x3() @ (k - h); v0 = V0[s]
    v = v - AXP * v.dot(AXP); v0p = v0 - AXP * v0.dot(AXP)
    sgn = math.atan2(AXP.dot(v0p.cross(v)), v0p.dot(v))
    return -sgn                                                          # + = knee forward (toward -Y at rest)


report = {}
for act in [a for a in bpy.data.actions if a.use_fake_user]:
    rig.animation_data.action = act
    if len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range); mx = [0.0, 0.0]
    for f in range(f0, f1 + 1):
        bpy.context.scene.frame_set(f)
        fl = [flex('L'), flex('R')]
        tf = max(0.0, *fl) * KF; tb = max(0.0, -fl[0], -fl[1]) * KB
        for name, ang in (('B_PanelFront', -tf), ('B_PanelBack', tb)):
            p = rig.pose.bones[name]; p.rotation_mode = 'QUATERNION'
            p.rotation_quaternion = Quaternion(LOC[name], ang)
            p.keyframe_insert('rotation_quaternion', frame=f)
        mx = [max(mx[0], tf), max(mx[1], tb)]
    report[act.name] = [round(math.degrees(x)) for x in mx]
    rig.animation_data.action = None
print('PANELBONES max front/back swing deg', report)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
