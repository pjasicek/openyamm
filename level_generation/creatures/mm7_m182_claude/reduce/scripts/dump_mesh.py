# Copied from mm8_m492_reduce_claude/scripts (read-only reference) for the m182 v3b reduction.
"""Dump the rest-pose source mesh for texture-aware decimation: work/mesh_in.npz (vertices, triangles, wedge UVs with
the head material shifted by +2 in u, protection flag per face = Head/Jaw dominated)."""
import os, bpy, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'source.blend'))
src = bpy.data.objects[os.environ.get('REA_MESH', 'Body')]
me = src.data; me.calc_loop_triangles(); uv = me.uv_layers.active.data
prot_idx = {g.index for g in src.vertex_groups if any(p in g.name for p in os.environ.get('REA_PROTECT', 'Head,Jaw').split(','))}
pw = np.array([sum(g.weight for g in v.groups if g.group in prot_idx) for v in me.vertices])
tris = me.loop_triangles
np.savez(os.path.join(HERE, 'work', 'mesh_in.npz'),
         verts=np.array([v.co[:] for v in me.vertices]),
         faces=np.array([t.vertices[:] for t in tris], np.int32),
         wuv=np.array([[uv[l].uv[0] + 2.0 * t.material_index, uv[l].uv[1]] for t in tris for l in t.loops]),
         protect=np.array([float(pw[list(t.vertices)].mean() > .5) for t in tris]))
print('DUMPED', len(me.vertices), len(tris))
