"""Ladder error per source region: source vertex -> candidate surface distance over every 3rd frame of every clip
(the ladder's source direction), grouped by the region label (work/groups.npy, majority of adjacent faces) and the
keep mask. Prints per region the vertex count, p95/p99 of samples (mm) and samples over the p99 limit.
Usage: REA_LIMIT_MM=4.2 blender -b -P region_error.py -- <ladder blend> <Cand_81,...>"""
import os, sys, bpy, bmesh, numpy as np
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', args[0]))
sc = bpy.context.scene; src = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']
d = np.load(os.path.join(HERE, 'work', 'mesh_in.npz')); f = d['faces']; g = np.load(os.path.join(HERE, 'work', 'groups.npy'))
keep = np.load(os.path.join(HERE, 'work', os.environ.get('REA_KEEP', 'keep_p2.npy')))
lab = np.full(len(d['verts']), -1)
for gi in np.unique(g):
    lab[np.unique(f[g == gi])] = gi
lab[np.unique(f[keep])] = 99
LIM = float(os.environ.get('REA_LIMIT_MM', '4.2')) / 1000
def ev(o):
    b = bmesh.new(); b.from_object(o, bpy.context.evaluated_depsgraph_get()); b.transform(o.matrix_world)
    b.verts.ensure_lookup_table(); return b
for cn in args[1].split(','):
    c = bpy.data.objects[cn]; D = []
    for act in bpy.data.actions:
        rig.animation_data.action = act; f0, f1 = (int(x) for x in act.frame_range)
        for fr in range(f0, f1 + 1, 3):
            sc.frame_set(fr); bs, bc = ev(src), ev(c); tc = BVHTree.FromBMesh(bc)
            D.append([tc.find_nearest(v.co)[3] for v in bs.verts]); bs.free(); bc.free()
    D = np.array(D)
    print('REGION', cn, 'all p99', round(float(np.percentile(D, 99)) * 1000, 2))
    for gi in sorted(np.unique(lab)):
        x = D[:, lab == gi]
        print(f'  region {gi:3d} verts {x.shape[1]:5d} p95 {np.percentile(x, 95) * 1000:6.2f} p99 {np.percentile(x, 99) * 1000:6.2f} over {int((x > LIM).sum()):6d}')
