"""Print objects, polycounts and bounds in a blend. Args: <blend>"""
import bpy, sys
import numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--') + 1])
for o in bpy.data.objects:
    if o.type == 'MESH':
        q = np.array([tuple(o.matrix_world @ v.co) for v in o.data.vertices])
        print('OBJ', o.name, len(o.data.polygons), q.min(0).round(3).tolist(), q.max(0).round(3).tolist(), [m.name for m in o.data.materials][:3], list(o.data.attributes.keys())[:8])
    else:
        print('OBJ', o.name, o.type)
