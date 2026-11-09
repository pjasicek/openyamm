"""Rest-pose triangles of the 40 % candidate with their installed UVs (corner positions and UVs) for compose.py's
barycentric transfer of the installed texture. Out: work/old_tris.npz."""
import os, bpy, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'ladder.blend'))
o = bpy.data.objects[os.environ.get('REA_CAND', 'Cand_40')]; me = o.data; me.calc_loop_triangles(); uv = me.uv_layers.active.data
P = np.array([[me.vertices[v].co[:] for v in t.vertices] for t in me.loop_triangles], np.float32)
U = np.array([[uv[l].uv[:] for l in t.loops] for t in me.loop_triangles], np.float32)
np.savez(os.path.join(HERE, 'work', 'old_tris.npz'), pos=P, uv=U); print('OLD TRIS', len(P))
