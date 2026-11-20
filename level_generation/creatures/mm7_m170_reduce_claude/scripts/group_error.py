"""Per-region error of a ladder candidate: for every 4th frame of every clip, the distance from each posed source vertex
to the posed candidate surface, grouped by the source vertex's region label (work/groups.npy majority over its faces;
kept faces count as 'kept'). Prints p99 / max mm and the worst frame per region. GE_CLIP=<clip> measures its frame 0 only.
Usage: blender -b -P group_error.py -- <ladder blend> <Cand_NN>"""
import os, sys, bpy, bmesh, numpy as np
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
blend, cand = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', blend))
sc = bpy.context.scene; src = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']; c = bpy.data.objects[cand]
d = np.load(os.path.join(HERE, 'work', 'mesh_in.npz')); f = d['faces']
g = np.load(os.path.join(HERE, 'work', 'groups.npy')); keep = np.load(os.environ.get('GE_KEEP', os.path.join(HERE, 'work', 'keep_base.npy')))
lab = np.where(keep, 99, g)
vl = np.full(len(d['verts']), -1)
for k in range(3):
    vl[f[:, k]] = np.maximum(vl[f[:, k]], lab)
names = {0: 'rest', 1: 'face', 2: 'hair', 3: 'L hand', 4: 'R hand', 5: 'skirt', 6: 'robe top', 7: 'helmet', 8: 'crescent', 9: 'banners', 99: 'kept'}
def ev(o):
    b = bmesh.new(); b.from_object(o, bpy.context.evaluated_depsgraph_get()); b.transform(o.matrix_world); return b
dist = {}; where = {}
only = os.environ.get('GE_CLIP')
for act in bpy.data.actions:
    if only and act.name != only:
        continue
    rig.animation_data.action = act
    for fr in range(int(act.frame_range[0]), int(act.frame_range[1]) + 1, 4) if not only else [0]:
        sc.frame_set(fr); bs, bc = ev(src), ev(c); tc = BVHTree.FromBMesh(bc)
        dd = np.array([tc.find_nearest(v.co)[3] for v in bs.verts]) * 1000
        for k in np.unique(vl):
            x = dd[vl == k]; dist.setdefault(k, []).append(x)
            if x.max() > where.get(k, (0, ''))[0]:
                where[k] = (x.max(), f'{act.name}:{fr}')
        bs.free(); bc.free()
for k in sorted(dist):
    x = np.concatenate(dist[k]); print(f'GERR {names.get(k, k):16s} p99 {np.percentile(x, 99):6.2f} max {x.max():6.1f} at {where[k][1]}')
