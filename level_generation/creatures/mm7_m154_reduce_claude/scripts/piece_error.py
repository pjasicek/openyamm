"""Where a ladder candidate's error sits, per source piece (work/piece.npy labels; README pieces table): two-way
vertex -> surface distances over every 3rd frame of every clip, each distance assigned to the piece of the source
vertex (candidate vertices: their nearest source vertex at rest). Prints per piece p99 / max (mm) and the 8 worst
spots (clip:frame, rest position, piece). Usage: blender -b -P piece_error.py -- <ladder blend> <Cand_NN>"""
import os, sys, bpy, bmesh
import numpy as np
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
blend, cand = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', blend))
sc = bpy.context.scene; src = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']; c = bpy.data.objects[cand]
d = np.load(os.path.join(HERE, 'work', 'mesh_in.npz')); pc = np.load(os.path.join(HERE, 'work', 'piece.npy'))
vp = np.zeros(len(d['verts']), int); vp[d['faces'].ravel()] = np.repeat(pc, 3)
kd = KDTree(len(src.data.vertices))
for v in src.data.vertices:
    kd.insert(v.co, v.index)
kd.balance()
cmap = np.array([kd.find(v.co)[1] for v in c.data.vertices])
srest = np.array([v.co[:] for v in src.data.vertices])
rig.animation_data.action = None


def ev(o):
    b = bmesh.new(); b.from_object(o, bpy.context.evaluated_depsgraph_get()); b.transform(o.matrix_world)
    b.verts.ensure_lookup_table(); return b


per = {}; worst = []
for act in bpy.data.actions:
    rig.animation_data.action = act
    for f in range(int(act.frame_range[0]), int(act.frame_range[1]) + 1, 3):
        sc.frame_set(f); bs, bc = ev(src), ev(c); ts, tc = BVHTree.FromBMesh(bs), BVHTree.FromBMesh(bc)
        e1 = np.array([ts.find_nearest(v.co)[3] for v in bc.verts]); e2 = np.array([tc.find_nearest(v.co)[3] for v in bs.verts])
        for e, idx in ((e1, cmap), (e2, np.arange(len(e2)))):
            for p in np.unique(vp[idx]):
                per.setdefault(int(p), []).append(e[vp[idx] == p])
            for i in np.argsort(-e)[:3]:
                worst.append((float(e[i]), f'{act.name}:{f}', tuple(np.round(srest[idx[i]], 3)), int(vp[idx[i]])))
        bs.free(); bc.free()
for p, L in sorted(per.items(), key=lambda kv: -np.percentile(np.concatenate(kv[1]), 99)):
    a = np.concatenate(L) * 1000
    print(f'PIECE {p:3d} p99 {np.percentile(a, 99):6.2f} max {a.max():6.2f} n {len(a)}')
seen = set()
for e, at, pos, p in sorted(worst, reverse=True):
    if (at, p) in seen:
        continue
    seen.add((at, p)); print(f'WORST {e * 1000:.1f} mm {at} rest {pos} piece {p}')
    if len(seen) >= 10:
        break
