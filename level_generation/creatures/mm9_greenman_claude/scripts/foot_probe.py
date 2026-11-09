"""Foot footprints relative to the Foot joint: MM9's mesh (all pieces but the staff, bind pose) and our Body (blend, bind).
Vertices whose dominant group is the side's Foot or Toe0. Prints x/y/z extents (Blender: -y forward, z up) per side and the
joints. Args: <blend> <mm9 glb>"""
import bpy, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
def footprint(objs, arm, side):
    J = arm.matrix_world @ arm.data.bones[f'Bip01 {side} Foot'].head_local
    T = arm.matrix_world @ arm.data.bones[f'Bip01 {side} Toe0'].head_local
    pts = []
    for o in objs:
        names = {g.index: g.name for g in o.vertex_groups}
        for v in o.data.vertices:
            if not v.groups: continue
            g = max(v.groups, key=lambda g: g.weight)
            if names.get(g.group) in (f'Bip01 {side} Foot', f'Bip01 {side} Toe0'):
                pts.append(tuple(o.matrix_world @ v.co))
    p = np.array(pts) - np.array(J)
    return np.array(J), np.array(T) - np.array(J), p
bpy.ops.wm.open_mainfile(filepath=a[0])
body = bpy.data.objects['Body']; arm = body.parent
for s in 'LR':
    J, T, p = footprint([body], arm, s)
    print('OURS', s, 'ankle', J.round(3), 'toe joint rel', T.round(3), 'n', len(p), 'min', p.min(0).round(3), 'max', p.max(0).round(3))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a[1])
arm = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE')
if arm.animation_data: arm.animation_data.action = None
for pb in arm.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
objs = [o for o in bpy.context.scene.objects if o.type == 'MESH' and not o.name.startswith('staff')]
for s in 'LR':
    J, T, p = footprint(objs, arm, s)
    print('MM9 ', s, 'ankle', J.round(3), 'toe joint rel', T.round(3), 'n', len(p), 'min', p.min(0).round(3), 'max', p.max(0).round(3))
