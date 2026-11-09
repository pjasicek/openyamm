"""Print world head/tail of chosen bones at a clip frame. Args: blend clip frame bone [bone ...]."""
import bpy, sys, os
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(P, a[0]))
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
rig.animation_data.action = bpy.data.actions[a[1]]; bpy.context.scene.frame_set(int(a[2]))
for n in a[3:]:
    b = rig.pose.bones[n]; h = rig.matrix_world @ b.head; t = rig.matrix_world @ b.tail
    print('BONE', n, tuple(round(x, 3) for x in h), tuple(round(x, 3) for x in t))
