"""Source vertices no ray can reach (skin under the vest, shorts and pack): 64 hemisphere rays per vertex in the
Standing pose; hidden when every ray hits the mesh. -> work/hidden.npy (bool per source vertex). The ladder error
(REA_HIDDEN) then skips them; poke-through still shows as candidate -> source error on visible surfaces."""
import os, math, bpy, bmesh, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'source.blend'))
src = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']
rig.animation_data.action = bpy.data.actions['Standing']; bpy.context.scene.frame_set(0)
b = bmesh.new(); b.from_object(src, bpy.context.evaluated_depsgraph_get()); b.transform(src.matrix_world)
b.verts.ensure_lookup_table(); b.normal_update(); t = BVHTree.FromBMesh(b)
N = 160; dirs = []
for i in range(N):
    z = 1 - 2 * (i + .5) / N; r = math.sqrt(1 - z * z); a = i * math.pi * (3 - math.sqrt(5))
    dirs.append(Vector((r * math.cos(a), r * math.sin(a), z)))
hidden = np.zeros(len(b.verts), bool)
for v in b.verts:
    n = v.normal
    ds = [d for d in dirs if d.dot(n) > .05]
    hidden[v.index] = all(t.ray_cast(v.co + d * 1e-3, d, 3.0)[0] is not None for d in ds)
np.save(os.path.join(HERE, 'work', 'hidden.npy'), hidden)
print('HIDDEN', int(hidden.sum()), 'of', len(hidden))
