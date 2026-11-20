"""Hand length (hand joint -> farthest vertex weighted mostly to the hand/finger bones) and figure height, rest pose.
Args: <glb or blend>"""
import bpy, sys
argv = sys.argv[sys.argv.index('--') + 1:]
f = argv[0]
if f.endswith('.blend'):
    bpy.ops.wm.open_mainfile(filepath=f)
else:
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=f)
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
zs = []
for o in bpy.data.objects:
    if o.type != 'MESH':
        continue
    zs += [(o.matrix_world @ v.co).z for v in o.data.vertices]
for S in 'LR':
    hj = arm.matrix_world @ arm.data.bones[f'Bip01 {S} Hand'].head_local
    fa = arm.matrix_world @ arm.data.bones[f'Bip01 {S} Forearm'].head_local
    best = 0
    for o in bpy.data.objects:
        if o.type != 'MESH':
            continue
        names = {g.index: g.name for g in o.vertex_groups}
        for v in o.data.vertices:
            w = sum(g.weight for g in v.groups if f' {S} ' in names.get(g.group, '') and ('Hand' in names[g.group] or 'Finger' in names[g.group] or 'Thumb' in names[g.group] or 'Index' in names[g.group] or 'Middle' in names[g.group] or 'Ring' in names[g.group] or 'Pinky' in names[g.group]))
            if w > 0.5:
                best = max(best, ((o.matrix_world @ v.co) - hj).length)
    print('HANDLEN', S, round(best, 4), 'forearm', round((hj - fa).length, 4), 'height', round(max(zs) - min(zs), 4))
