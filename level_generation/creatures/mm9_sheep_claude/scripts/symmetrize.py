"""Make the fitted 'Body' mirror-symmetric (MM9's sheep is): keep the half closer to MM9's surface (or KEEP=+1/-1),
mirror it across x = 0 (Blender Symmetrize, seam welded), and swap the left/right leg chain ids on the mirrored half.
Reports the asymmetry before (mean / p95 distance from each vertex's mirror image to the surface).
Args: <in blend> <out blend> <report json>"""
import bpy, bmesh, sys, json, os
import numpy as np
from mathutils.bvhtree import BVHTree
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, REP = argv
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']
me = body.data
bm = bmesh.new(); bm.from_mesh(me)
bvh = BVHTree.FromBMesh(bm)
P = np.array([tuple(v.co) for v in me.vertices])
d = np.array([(bvh.find_nearest(Vector((-p[0], p[1], p[2])))[3] or 0) for p in P])
mm9 = []
for o in bpy.data.objects:
    if o.type == 'MESH' and o.name != 'Body':
        mm9 += [tuple(o.matrix_world @ v.co) for v in o.data.vertices]
from mathutils.kdtree import KDTree
k = KDTree(len(mm9))
for i, p in enumerate(mm9):
    k.insert(p, i)
k.balance()
dm = np.array([k.find(Vector(p))[2] for p in P])
side_err = {'+X': float(dm[P[:, 0] > 0.01].mean()), '-X': float(dm[P[:, 0] < -0.01].mean())}
keep = os.environ.get('KEEP') or ('+X' if side_err['+X'] <= side_err['-X'] else '-X')
bpy.context.view_layer.objects.active = body
for o in bpy.data.objects:
    o.select_set(o == body)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.symmetrize(direction='POSITIVE_X' if keep == '+X' else 'NEGATIVE_X', threshold=0.0005)
bpy.ops.object.mode_set(mode='OBJECT')
me = body.data
P2 = np.array([tuple(v.co) for v in me.vertices])
ch = me.attributes['chain']
swap = {0: 1, 1: 0, 2: 3, 3: 2}
mirrored = (P2[:, 0] < -1e-4) if keep == '+X' else (P2[:, 0] > 1e-4)
# chain ids: +X = the sheep's left (0 front-left, 2 hind-left); the mirrored half takes the other side's id
for i in np.nonzero(mirrored)[0]:
    c = ch.data[int(i)].value
    want_left = P2[i, 0] > 0
    if c in swap and ((c in (0, 2)) != want_left):
        ch.data[int(i)].value = swap[c]
bm2 = bmesh.new(); bm2.from_mesh(me)
bvh2 = BVHTree.FromBMesh(bm2)
d2 = np.array([(bvh2.find_nearest(Vector((-p[0], p[1], p[2])))[3] or 0) for p in P2])
rep = {'before_mean': float(d.mean()), 'before_p95': float(np.percentile(d, 95)), 'side_dist_to_mm9': side_err,
       'kept': keep, 'after_mean': float(d2.mean()), 'after_p95': float(np.percentile(d2, 95)),
       'verts': len(me.vertices), 'tris': sum(len(p.vertices) - 2 for p in me.polygons)}
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1)
print('SYM ' + json.dumps(rep))
