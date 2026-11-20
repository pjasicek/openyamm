import bpy, sys
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
for o in bpy.data.objects:
    if o.type == 'MESH' and o.name.endswith('.mesh'):
        print('OBJ', o.name, o.parent.name if o.parent else None, [round(x,3) for x in o.matrix_world.to_translation()], o.matrix_world.to_scale())
        for v in o.data.vertices:
            g = max(v.groups, key=lambda g: g.weight)
            n = o.vertex_groups[g.group].name
            co = o.matrix_world @ v.co
            if abs(co.x) > 6:
                print('FAR', n, [round(c, 2) for c in co]); break
