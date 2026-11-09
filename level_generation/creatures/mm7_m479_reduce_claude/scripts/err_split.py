"""Rest-pose versus posed error of every ladder candidate (work/ladder.blend): two-way vertex -> surface distances in
the rest pose (geometry only) and at REA_FRAMES (geometry + weights). Prints p99/max per candidate. Usage: -- none"""
import os, bpy, bmesh, numpy as np
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'ladder.blend'))
sc = bpy.context.scene; src = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']
def ev(o):
    b = bmesh.new(); b.from_object(o, bpy.context.evaluated_depsgraph_get()); b.transform(o.matrix_world); return b
def err(c):
    bs, bc = ev(src), ev(c); ts, tc = BVHTree.FromBMesh(bs), BVHTree.FromBMesh(bc)
    d1 = np.array([ts.find_nearest(v.co)[3] for v in bc.verts]); d2 = np.array([tc.find_nearest(v.co)[3] for v in bs.verts])
    bs.free(); bc.free(); return d1, d2
cands = [o for o in bpy.data.objects if o.name.startswith('Cand_')]
for spec in ['rest'] + os.environ.get('REA_FRAMES', 'Standing:24,Attack:18,Death:10').split(','):
    if spec == 'rest':
        rig.animation_data.action = None
        for b in rig.pose.bones:
            b.matrix_basis.identity()
        bpy.context.view_layer.update()
    else:
        a, f = spec.split(':'); rig.animation_data.action = bpy.data.actions[a]; sc.frame_set(int(f))
    for c in cands:
        d1, d2 = err(c); allv = np.r_[d1, d2]
        print('ERR', spec, c.name, 'p99', round(float(np.percentile(allv, 99)) * 1000, 1), 'max', round(float(allv.max()) * 1000, 1),
              'cand->src max', round(float(d1.max()) * 1000, 1), 'src->cand max', round(float(d2.max()) * 1000, 1), flush=True)
