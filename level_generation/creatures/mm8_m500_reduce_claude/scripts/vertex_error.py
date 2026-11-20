"""Per source vertex: the largest distance to a candidate's surface over every STEP-th frame of every clip ->
work/verr_<cand>.npy (source.blend vertex order = work/mesh_in.npz). Finds the spots behind the ladder's max error so
a patch around them can be kept. Usage: blender -b -P vertex_error.py -- <ladder blend> <Cand_55> [step]"""
import os, sys, bpy, bmesh
import numpy as np
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', args[0]))
STEP = int(args[2]) if len(args) > 2 else 3
sc = bpy.context.scene; src = bpy.data.objects['Body']; cand = bpy.data.objects[args[1]]; rig = bpy.data.objects['Rig']
def ev(o):
    b = bmesh.new(); b.from_object(o, bpy.context.evaluated_depsgraph_get()); b.transform(o.matrix_world)
    b.verts.ensure_lookup_table(); return b
err = np.zeros(len(src.data.vertices))
for a in bpy.data.actions:
    rig.animation_data.action = a
    for f in range(0, int(a.frame_range[1]) + 1, STEP):
        sc.frame_set(f); bs, bc = ev(src), ev(cand); tc = BVHTree.FromBMesh(bc)
        d = np.array([tc.find_nearest(v.co)[3] for v in bs.verts]); err = np.maximum(err, d); bs.free(); bc.free()
np.save(os.path.join(HERE, 'work', f'verr_{args[1]}.npy'), err)
print('VERR', args[1], 'p99 %.1f max %.1f mm, over 15 mm: %d' % (np.percentile(err, 99) * 1000, err.max() * 1000, (err > .015).sum()))
