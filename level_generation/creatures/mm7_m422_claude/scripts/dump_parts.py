"""Dump every part of work/st_v1_parts.blend (vertices, triangles) to work/st_v1_parts.npz for numpy analysis.
Args: none"""
import bpy, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'st_v1_parts.blend'))
out = {}
for o in bpy.data.objects:
    if o.type != 'MESH':
        continue
    me = o.data
    co = np.array([o.matrix_world @ v.co for v in me.vertices])
    me.calc_loop_triangles()
    tri = np.array([t.vertices[:] for t in me.loop_triangles])
    out[o.name + '_co'] = co; out[o.name + '_tri'] = tri
np.savez(os.path.join(common.WORK, 'st_v1_parts.npz'), **out)
print('DUMP parts', len(out) // 2)
