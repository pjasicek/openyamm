"""Rest joint positions of chosen bones. Args: -- <blend> <bone> [...]"""
import bpy, sys, os
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
rig = bpy.data.objects['Rig']
for b in a[1:]:
    print('REST', b, tuple(round(x, 3) for x in rig.matrix_world @ rig.data.bones[b].head_local))
