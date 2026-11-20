"""Which region carries a ladder candidate's surface error: both-way vertex->surface distances over every 3rd frame of
every clip (as reduce_ladder.py), each sample labelled by the region (work/groups.npy, kept faces as 99) of the nearest
source vertex. Prints per region: samples over 5 mm, its max, and the overall p99 without that region.
Usage: blender -b -P group_error.py -- <ladder blend> <Cand_80,...>"""
import os, sys, bpy, bmesh
import numpy as np
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
blend, cands = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', blend))
sc = bpy.context.scene; src = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']
d = np.load(os.path.join(HERE, 'work/mesh_in.npz')); g = np.load(os.environ.get('REA_LABELS', os.path.join(HERE, 'work/groups.npy'))).copy()
keep = np.load(os.environ.get('REA_KEEP_FACES', os.path.join(HERE, 'work/keep_base.npy'))); g[keep] = 99
vg = np.full(len(d["verts"]), 99)
for k in range(3):
    np.minimum.at(vg, d['faces'][:, k], g)
def ev(o):
    b = bmesh.new(); b.from_object(o, bpy.context.evaluated_depsgraph_get()); b.transform(o.matrix_world)
    b.verts.ensure_lookup_table(); return b
for cn in cands.split(','):
    c = bpy.data.objects[cn]; dist, lab = [], []
    for act in bpy.data.actions:
        rig.animation_data.action = act; f0, f1 = (int(x) for x in act.frame_range)
        for f in range(f0, f1 + 1, 3):
            sc.frame_set(f); bs, bc = ev(src), ev(c); ts, tc = BVHTree.FromBMesh(bs), BVHTree.FromBMesh(bc)
            kd = KDTree(len(bs.verts))
            for v in bs.verts:
                kd.insert(v.co, v.index)
            kd.balance()
            for v in bs.verts:
                dist.append(tc.find_nearest(v.co)[3]); lab.append(vg[v.index])
            for v in bc.verts:
                dist.append(ts.find_nearest(v.co)[3]); lab.append(vg[kd.find(v.co)[1]])
            bs.free(); bc.free()
    dist = np.array(dist) * 1000; lab = np.array(lab)
    print('GROUPERR', cn, 'p99', round(float(np.percentile(dist, 99)), 2), 'max', round(float(dist.max()), 1))
    for k in sorted(set(lab.tolist())):
        m = lab == k
        print(f'  region {k}: samples {m.sum()}, >5mm {(dist[m] > 5).sum()}, p99 {np.percentile(dist[m], 99):.2f}, '
              f'max {dist[m].max():.1f}, overall p99 without it {np.percentile(dist[~m], 99):.2f}', flush=True)
