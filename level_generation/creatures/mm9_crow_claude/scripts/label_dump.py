"""Print MM9 vertex positions of the given bones (dominant label). Args: <rig source blend> bone ..."""
import bpy, sys
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
for o in bpy.data.objects:
    if o.type != 'MESH':
        continue
    for v in o.data.vertices:
        g = max(v.groups, key=lambda g: g.weight)
        n = o.vertex_groups[g.group].name
        if n in argv[1:]:
            print('LBL', n, tuple(round(x, 3) for x in (o.matrix_world @ v.co)))
