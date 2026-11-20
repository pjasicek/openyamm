"""World head positions of bones at clip@frame. Args: <rig blend> <bones,> <clip@frame ...>"""
import bpy, sys
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
sc = bpy.context.scene
for cf in argv[2:]:
    c, f = cf.split('@')
    arm.animation_data.action = bpy.data.actions[c]
    sc.frame_set(int(f))
    print('POS', cf, {b: [round(x, 3) for x in arm.matrix_world @ arm.pose.bones[b].head] for b in argv[1].split(',')})
