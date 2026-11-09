"""Surface error of a ladder candidate per make_groups.py group: for each source vertex its distance to the posed
candidate surface at the given frames, binned by the group of its faces. Usage: blender -b -P group_error.py --
<blend> <Cand> <clip:frame,...>"""
import os, sys, bpy, bmesh
import numpy as np
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
blend, cand, frames = sys.argv[sys.argv.index('--') + 1:][:3]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', blend))
sc = bpy.context.scene; src = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']; c = bpy.data.objects[cand]
d = np.load(os.path.join(HERE, 'work', 'mesh_in.npz')); g = np.load(os.path.join(HERE, 'work', 'groups.npy'))
k = np.load(os.path.join(HERE, 'work', 'keep.npy')); g = np.where(k, -1, g)
vg = np.full(len(d['verts']), -1)
for fi, f in enumerate(d['faces']):
    vg[f] = np.maximum(vg[f], g[fi])
acc = {}
for cf in frames.split(','):
    clip, f = cf.split(':'); rig.animation_data.action = bpy.data.actions[clip]; sc.frame_set(int(f))
    deps = bpy.context.evaluated_depsgraph_get()
    bm = bmesh.new(); bm.from_object(c, deps); bm.transform(c.matrix_world); tree = BVHTree.FromBMesh(bm)
    me = src.evaluated_get(deps).to_mesh()
    for i, v in enumerate(me.vertices):
        loc, n, idx, dist = tree.find_nearest(src.matrix_world @ v.co, 0.2)
        acc.setdefault(int(vg[i]), []).append(dist if dist is not None else 0.2)
    src.evaluated_get(deps).to_mesh_clear(); bm.free()
for gg, ds in sorted(acc.items()):
    ds = np.array(ds) * 1000
    print('GROUPERR', gg, 'n', len(ds), 'p99', round(float(np.percentile(ds, 99)), 2), 'max', round(float(ds.max()), 1), '>5mm', int((ds > 5).sum()))
