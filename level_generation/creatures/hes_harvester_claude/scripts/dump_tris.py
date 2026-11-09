"""Dump work/harvester_tex.blend's triangles for the texture compose: per triangle the UVs, 3D corners (rest pose,
metres), face normal, part and polygon index. Writes work/harvester_tris.npz (after hes_turrets_claude)."""
import os
import sys

import bpy
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
name = 'harvester'
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', f'{name}_tex.blend'))
me = bpy.data.objects[name].data
me.calc_loop_triangles()
uv = me.uv_layers.active.data
part = np.zeros(len(me.polygons), int); me.attributes['part'].data.foreach_get('value', part)
tri_uv, tri_co, tri_n, tri_part, tri_poly = [], [], [], [], []
for t in me.loop_triangles:
    tri_uv.append([uv[li].uv[:] for li in t.loops])
    tri_co.append([me.vertices[vi].co[:] for vi in t.vertices])
    tri_n.append(t.normal[:])
    tri_part.append(part[t.polygon_index]); tri_poly.append(t.polygon_index)
np.savez(os.path.join(HERE, 'work', f'{name}_tris.npz'), uv=np.array(tri_uv), co=np.array(tri_co),
         n=np.array(tri_n), part=np.array(tri_part), poly=np.array(tri_poly), drill_axis=np.array(bpy.data.objects[name]['drill_axis']))
print('DUMPED', len(tri_uv))
