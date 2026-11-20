"""Where a ladder candidate's surface error sits, by region (work/regions.npy, plus 'hands' for hand/finger-weighted
vertices): over every 3rd frame of every clip, both-way vertex->surface distances above REA_MM (default 5.12 mm, the
p99 limit for 1.706 m), counted per region of the nearest source vertex (body split by dominant bone); also the worst clip frames.
Usage: blender -b -P region_error.py -- <ladder blend in work/> <Cand_NN>"""
import os, sys, bpy, bmesh, collections, numpy as np
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
blend, cand = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', blend))
sc = bpy.context.scene; src = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']; c = bpy.data.objects[cand]
d = np.load(os.path.join(HERE, 'work', 'mesh_in.npz')); reg = np.load(os.path.join(HERE, 'work', 'regions.npy'))
NAMES = {1: 'body', 2: 'head', 3: 'arms', 4: 'helmet', 5: 'shoulder', 6: 'panels', 7: 'trims', 8: 'small'}
vreg = np.zeros(len(d['verts']), int)
for k in range(3):
    vreg[d['faces'][:, k]] = reg
g = np.load(os.path.join(HERE, 'work', 'groups.npz')); dom = [str(x) for x in g['names'][g['W'].argmax(1)]]
lab = lambda i: NAMES[vreg[i]] + ('/' + dom[i] if vreg[i] == 1 else '')
LIM = float(os.environ.get('REA_MM', '5.12')) / 1000
def ev(o):
    b = bmesh.new(); b.from_object(o, bpy.context.evaluated_depsgraph_get()); b.transform(o.matrix_world)
    b.verts.ensure_lookup_table(); return b
tot = collections.Counter(); frames = collections.Counter(); allc = 0
for act in bpy.data.actions:
    rig.animation_data.action = act
    f0, f1 = (int(x) for x in act.frame_range)
    for f in range(f0, f1 + 1, 3):
        sc.frame_set(f)
        bs, bc = ev(src), ev(c); ts, tc = BVHTree.FromBMesh(bs), BVHTree.FromBMesh(bc)
        kd = KDTree(len(bs.verts))
        for v in bs.verts:
            kd.insert(v.co, v.index)
        kd.balance()
        n = 0
        for v in bs.verts:
            allc += 1
            if tc.find_nearest(v.co)[3] > LIM:
                tot[lab(v.index)] += 1; n += 1
        for v in bc.verts:
            allc += 1
            if ts.find_nearest(v.co)[3] > LIM:
                tot[lab(kd.find(v.co)[1])] += 1; n += 1
        frames[f'{act.name}:{f}'] = n; bs.free(); bc.free()
print('REGION over', LIM * 1000, 'mm:', sum(tot.values()), 'of', allc, tot.most_common())
print('FRAMES', frames.most_common(8))
