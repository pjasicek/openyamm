"""UV layout dump of work/uv_final.blend -> work/uv_layout.npz (triangles per material), drawn by PIL outside."""
import os, bpy, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'uv_final.blend'))
m = bpy.data.objects['Wyrm']; uv = m.data.uv_layers.active.data
tri = {0: [], 1: []}
for f in m.data.polygons:
    pts = [uv[l].uv[:] for l in f.loop_indices]
    for k in range(1, len(pts) - 1):
        tri[f.material_index].append((pts[0], pts[k], pts[k + 1]))
np.savez(os.path.join(HERE, 'work', 'uv_layout.npz'), body=np.array(tri[0]), head=np.array(tri[1]))
