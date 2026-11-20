"""Leg shape onto MM9's knee/ankle line (mm9_greenman pass 2, orchestrator: "walk hop 8 cm every step"). fit_rig.py put
our knee 4.8 cm behind and our ankle 9.6 cm in front of MM9's (our Meshy legs are straight, MM9's bind leg has the knee
forward and the ankle back). The joints keep MM9's rest ROTATIONS, so with the knee bent in MM9's walk the ankle's forward
offset swung down and drove the toes 10 cm through the floor. Here each leg's mesh is moved in depth (Blender y) by a field
of height: 0 at the hip, DK at the knee, DA at the ankle and below (piecewise linear), times the vertex's weight on that
side's Thigh/Calf/Foot/Toe0 (kilt leaves on the pelvis stay); then the Calf, Foot and Toe0 joints move by the same amounts
(onto MM9's knee and ankle depth). Positions only; UVs, weights and paint unchanged. Args: <in blend> <out blend>"""
import bpy, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
body = bpy.data.objects['Body']; arm = body.parent; me = body.data
MM9 = {'Calf': -0.0726, 'Foot': 0.0309}
J = {b.name: (arm.matrix_world @ b.head_local) for b in arm.data.bones}
gname = {g.index: g.name for g in body.vertex_groups}
rep = {}
for s in 'LR':
    hipz = J[f'Bip01 {s} Thigh'].z; kz = J[f'Bip01 {s} Calf'].z; az = J[f'Bip01 {s} Foot'].z
    DK = MM9['Calf'] - J[f'Bip01 {s} Calf'].y; DA = MM9['Foot'] - J[f'Bip01 {s} Foot'].y
    zs = [az, kz, hipz]; ds = [DA, DK, 0.0]
    legs = {f'Bip01 {s} {b}' for b in ('Thigh', 'Calf', 'Foot', 'Toe0')}
    n = 0
    for v in me.vertices:
        w = sum(g.weight for g in v.groups if gname.get(g.group) in legs)
        if w <= 0: continue
        co = body.matrix_world @ v.co
        d = float(np.interp(co.z, zs, ds))
        co.y += d * w
        v.co = body.matrix_world.inverted() @ co; n += 1
    rep[s] = {'DK_cm': round(DK * 100, 1), 'DA_cm': round(DA * 100, 1), 'verts': n}
    # joints
    bpy.context.view_layer.objects.active = arm
    for o in bpy.data.objects: o.select_set(o is arm)
    bpy.ops.object.mode_set(mode='EDIT')
    Mi = arm.matrix_world.inverted().to_3x3()
    from mathutils import Vector
    for bn, d in ((f'Bip01 {s} Calf', DK), (f'Bip01 {s} Foot', DA), (f'Bip01 {s} Toe0', DA)):
        eb = arm.data.edit_bones[bn]; dv = Mi @ Vector((0, d, 0)); eb.head += dv; eb.tail += dv
    bpy.ops.object.mode_set(mode='OBJECT')
me.update()
print('LEGALIGN', rep)
bpy.ops.wm.save_as_mainfile(filepath=a[1])
