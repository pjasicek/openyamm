"""Ladder error split by part (Winged Mutant): over every 3rd frame of every clip, both-way vertex -> surface distances
of a candidate (as reduce_ladder.py) pooled, then p99/max for everything, for everything but the hair (brief: hair is
judged at party distance and in the front close-up) and for the hair alone. A source vertex is hair when its faces are
hair (sets.npz group 1, not kept); a candidate vertex when its group label (mesh_r<NN>.npz group) is 1.
Usage: blender -b -P eval_split.py -- <ladder blend> <Cand_NN> [<Cand_NN> ...]"""
import os, sys, json, bpy, bmesh, numpy as np
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', a[0]))
sc = bpy.context.scene; src = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']
m = np.load(os.path.join(HERE, 'work', 'mesh_in.npz')); S = np.load(os.path.join(HERE, 'work', 'sets.npz'))
sh = np.zeros(len(m['verts']), bool); sh[m['faces'][(S['group'] == 1) & ~S['keep']].ravel()] = True
def ev(o):
    b = bmesh.new(); b.from_object(o, bpy.context.evaluated_depsgraph_get()); b.transform(o.matrix_world); return b
out = {}
for cn in a[1:]:
    c = bpy.data.objects[cn]; d = np.load(os.path.join(HERE, os.environ.get('NPZDIR', 'work'), f'mesh_r{cn.split("_")[1]}.npz'))
    if 'group' in d.files:
        ch = np.zeros(len(d['verts']), bool); ch[d['faces'][d['group'] == 1].ravel()] = True
    else:   # mpqem steps: every vertex is a source vertex (src_index)
        ch = sh[d['src_index']]
    D, H = [], []
    worst = (0, '')
    for act in bpy.data.actions:
        rig.animation_data.action = act; f0, f1 = (int(x) for x in act.frame_range)
        for f in range(f0, f1 + 1, 3):
            sc.frame_set(f); bs, bc = ev(src), ev(c); ts, tc = BVHTree.FromBMesh(bs), BVHTree.FromBMesh(bc)
            d1 = np.array([tc.find_nearest(v.co)[3] for v in bs.verts]); d2 = np.array([ts.find_nearest(v.co)[3] for v in bc.verts])
            D += [d1, d2]; H += [sh, ch]
            nh = np.concatenate([d1[~sh], d2[~ch]]).max()
            if nh > worst[0]:
                worst = (nh, f'{act.name}:{f}')
            bs.free(); bc.free()
    D = np.concatenate(D) * 1000; H = np.concatenate(H)
    r = {'all_p99': round(float(np.percentile(D, 99)), 2), 'all_max': round(float(D.max()), 2),
         'nonhair_p99': round(float(np.percentile(D[~H], 99)), 2), 'nonhair_max': round(float(D[~H].max()), 2), 'nonhair_worst_at': worst[1],
         'hair_p99': round(float(np.percentile(D[H], 99)), 2) if H.any() else 0, 'hair_max': round(float(D[H].max()), 2) if H.any() else 0}
    out[cn] = r; print('SPLIT', cn, json.dumps(r), flush=True)
json.dump(out, open(os.path.join(HERE, 'work', f'split_{a[0].replace(".blend", "")}.json'), 'w'), indent=1)
