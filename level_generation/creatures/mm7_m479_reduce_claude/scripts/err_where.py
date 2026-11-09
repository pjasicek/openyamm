"""Rest-pose error map of one candidate (REA_CAND in work/ladder.blend): per source vertex the distance to the
candidate surface and per candidate vertex the distance to the source -> work/errmap_<cand>.npz. Usage: -- none"""
import os, bpy, bmesh, numpy as np
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'ladder.blend'))
src = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']; c = bpy.data.objects[os.environ.get('REA_CAND', 'Cand_77')]
rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
def ev(o):
    b = bmesh.new(); b.from_object(o, bpy.context.evaluated_depsgraph_get()); b.transform(o.matrix_world); return b
bs, bc = ev(src), ev(c); ts, tc = BVHTree.FromBMesh(bs), BVHTree.FromBMesh(bc)
d1 = np.array([ts.find_nearest(v.co)[3] for v in bc.verts]); d2 = np.array([tc.find_nearest(v.co)[3] for v in bs.verts])
np.savez(os.path.join(HERE, 'work', f'errmap_{c.name}.npz'), cand=d1, src=d2, cco=np.array([v.co[:] for v in bc.verts]),
         sco=np.array([v.co[:] for v in bs.verts]))
print('ERRMAP', c.name, len(d1), len(d2))
