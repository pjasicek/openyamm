"""Forearm twist: add <Side>ForeArmTwist1/2 deform bones (children of the forearm) and split forearm skin weights
along the forearm (mode 'setup'), or bake per-frame twist into them for every action (mode 'bake').

Bake: the hand's twist relative to the forearm (about the forearm axis, rest-relative) is distributed as
45% to Twist1 (mid-forearm) and 85% to Twist2 (near the wrist); the hand keeps its orientation.
"""
import bpy, sys, os, math
import numpy as np
from mathutils import Quaternion, Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

mode = sys.argv[sys.argv.index('--') + 1]
rig = bpy.data.objects['Peasant_Rig']; mesh = bpy.data.objects['Peasant']
SIDES = ('Left', 'Right')
SHARE = {1: 0.45, 2: 0.85}

if mode == 'setup':
    rig.animation_data.action = None
    for b in rig.pose.bones:
        b.matrix_basis.identity()
    bpy.context.view_layer.objects.active = rig
    for o in bpy.data.objects:
        o.select_set(o == rig)
    bpy.ops.object.mode_set(mode='EDIT')
    eb = rig.data.edit_bones
    for side in SIDES:
        fa = eb[f'mixamorig:{side}ForeArm']
        for k, (t0, t1) in ((1, (0.35, 0.6)), (2, (0.7, 0.95))):
            name = f'{side}ForeArmTwist{k}'
            b = eb.get(name) or eb.new(name)
            b.head = fa.head.lerp(fa.tail, t0); b.tail = fa.head.lerp(fa.tail, t1)
            b.roll = fa.roll; b.parent = fa; b.use_connect = False
    bpy.ops.object.mode_set(mode='OBJECT')
    groups = {g.name: g for g in mesh.vertex_groups}
    for side in SIDES:
        bone = rig.data.bones[f'mixamorig:{side}ForeArm']
        head = rig.matrix_world @ bone.head_local; tail = rig.matrix_world @ bone.tail_local
        axis = tail - head; L = axis.length; axis.normalize()
        fa_g = groups[f'mixamorig:{side}ForeArm']
        t_g = {k: groups.get(f'{side}ForeArmTwist{k}') or mesh.vertex_groups.new(name=f'{side}ForeArmTwist{k}')
               for k in (1, 2)}
        moved = 0
        for v in mesh.data.vertices:
            w = next((g.weight for g in v.groups if g.group == fa_g.index), 0.0)
            if w <= 0:
                continue
            t = (mesh.matrix_world @ v.co - head).dot(axis) / L
            # tents along the forearm: elbow end stays on ForeArm, middle -> Twist1, wrist end -> Twist2
            w1 = max(0.0, 1.0 - abs(t - 0.5) / 0.3)
            w2 = max(0.0, 1.0 - abs(t - 0.9) / 0.3) if t < 0.9 else 1.0
            w0 = max(0.0, 1.0 - t / 0.35)
            s = w0 + w1 + w2
            if s <= 0:
                continue
            fa_g.add([v.index], w * w0 / s, 'REPLACE')
            for k, wk in ((1, w1), (2, w2)):
                if wk > 0:
                    t_g[k].add([v.index], w * wk / s, 'REPLACE')
            moved += 1
        print('TWIST weights', side, moved)
    bpy.context.view_layer.objects.active = mesh
    for o in bpy.data.objects:
        o.select_set(o == mesh)
    bpy.ops.object.vertex_group_limit_total(group_select_mode='ALL', limit=4)
    bpy.ops.object.vertex_group_normalize_all(lock_active=False)
    bpy.ops.wm.save_mainfile()

elif mode == 'bake':
    for action in bpy.data.actions:
        rig.animation_data.action = action
        f0, f1 = int(action.frame_range[0]), int(action.frame_range[1])
        maxtw = 0.0
        for f in range(f0, f1 + 1):
            bpy.context.scene.frame_set(f)
            for side in SIDES:
                fa = rig.pose.bones[f'mixamorig:{side}ForeArm']; h = rig.pose.bones[f'mixamorig:{side}Hand']
                rel = fa.matrix.to_quaternion().inverted() @ h.matrix.to_quaternion()
                rest = fa.bone.matrix_local.to_quaternion().inverted() @ h.bone.matrix_local.to_quaternion()
                _, tw = (rest.inverted() @ rel).to_swing_twist('Y')
                maxtw = max(maxtw, abs(math.degrees(tw)))
                for k, share in SHARE.items():
                    tb = rig.pose.bones[f'{side}ForeArmTwist{k}']
                    tb.rotation_mode = 'QUATERNION'
                    tb.rotation_quaternion = Quaternion((0, 1, 0), tw * share)
                    tb.keyframe_insert('rotation_quaternion', frame=f)
        print('TWIST baked', action.name, 'max wrist twist deg', round(maxtw, 1))
    bpy.ops.wm.save_mainfile()
