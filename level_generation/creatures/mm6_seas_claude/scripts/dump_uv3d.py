"""Rest-pose body triangles (material slot 0; UV, 3D position) of the sea serpent -> work/uv3d.npz, for per-texel 3D positions in compose_seas.py."""
import bpy, os, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rig = bpy.data.objects['Seas_Rig']
if rig.animation_data:
    rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
me = bpy.data.objects['Seas'].data; me.calc_loop_triangles(); uv = me.uv_layers.active.data
tris = [t for t in me.loop_triangles if t.material_index == 0]      # body only; the foam collar has its own texture
U = np.array([[tuple(uv[l].uv) for l in t.loops] for t in tris], dtype=np.float32)
X = np.array([[tuple(me.vertices[v].co) for v in t.vertices] for t in tris], dtype=np.float32)
np.savez(os.path.join(HERE, 'work', 'uv3d.npz'), uv=U, xyz=X, part=np.zeros(len(U), np.int32))
print('DUMPED', len(U))
