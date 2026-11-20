"""The ladder's pooled error (reduce_ladder.py: every 3rd frame of every clip, source vertex -> candidate surface and candidate
vertex -> source surface), split by source vertex so the top 1 % can be attributed to parts. Writes work/errpool_<cand>_<blend>.npz
(d1: (frames, source verts), d2 pooled list). Usage: blender -b -P err_pool.py -- <Cand_60>   (env REA_BLEND)"""
import os, sys, bpy, bmesh, numpy as np
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cand = sys.argv[sys.argv.index('--') + 1]; blend = os.environ.get('REA_BLEND', 'ladder.blend')
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', blend))
sc = bpy.context.scene; src = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']; c = bpy.data.objects[cand]
def ev(o):
    b = bmesh.new(); b.from_object(o, bpy.context.evaluated_depsgraph_get()); b.transform(o.matrix_world); return b
D1, D2 = [], []
for act in bpy.data.actions:
    rig.animation_data.action = act; f0, f1 = (int(x) for x in act.frame_range)
    for f in range(f0, f1 + 1, 3):
        sc.frame_set(f); bs, bc = ev(src), ev(c); ts, tc = BVHTree.FromBMesh(bs), BVHTree.FromBMesh(bc)
        D1.append([tc.find_nearest(v.co)[3] for v in bs.verts]); D2 += [ts.find_nearest(v.co)[3] for v in bc.verts]
        bs.free(); bc.free()
np.savez(os.path.join(HERE, 'work', f'errpool_{cand}_{blend[:-6]}.npz'), d1=np.array(D1), d2=np.array(D2))
print('POOL', np.array(D1).shape, len(D2))
