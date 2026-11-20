"""Knee flex (thigh-calf angle) and ankle height per frame of one clip, for several GLBs (Blender evaluation).
Usage: blender -b -P knee_curve.py -- <clip> <label=glb,...>"""
import os, sys, bpy
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]; clip = a[0]
for item in a[1].split(','):
    label, glb = item.split('=')
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, glb))
    rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE'); act = bpy.data.actions[clip]
    rig.animation_data.action = act; sc = bpy.context.scene; f0, f1 = (int(x) for x in act.frame_range)
    for side in 'LR':
        row = []
        for f in range(f0, f1 + 1):
            sc.frame_set(f); pb = rig.pose.bones
            t, c = pb[f'B_{side}_Thigh'], pb[f'B_{side}_Calf']
            v1 = (t.tail - t.head).normalized(); v2 = (c.tail - c.head).normalized()
            import math
            row.append(f'{math.degrees(v1.angle(v2)):.0f}')
        print(f'KNEE {label} {side} ' + ' '.join(row))
