"""Dry-run body: the MM9 meshes joined as 'Body' (their MM9 weights) in the source blend. Args: <src blend> <out>"""
import bpy, sys
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
ms = [o for o in bpy.data.objects if o.type == 'MESH']
for o in bpy.data.objects:
    o.select_set(o in ms)
bpy.context.view_layer.objects.active = ms[0]
bpy.ops.object.join()
ms[0].name = 'Body'
bpy.ops.wm.save_as_mainfile(filepath=argv[1])
