"""List the objects of a blend (name, type, vertex count, bounds). Args: <blend>"""
import bpy, sys
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
for o in bpy.data.objects:
    n = len(o.data.vertices) if o.type == 'MESH' else 0
    print('OBJ', o.name, o.type, n, [round(x, 2) for x in o.dimensions], 'hide_render', o.hide_render)
