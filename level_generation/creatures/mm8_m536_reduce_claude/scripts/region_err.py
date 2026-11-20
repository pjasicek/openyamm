"""Where the ladder error sits: source vertex -> candidate surface distances per dominant source bone, at rest and
over every 3rd frame of every clip (rest error is geometry, the rest is skinning). Saves work/worst_<cand>.npy (per source vertex, metres). Usage: blender -b -P region_err.py -- <Cand_NN>"""
import os, sys, bpy, bmesh
import numpy as np
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'ladder.blend'))
sc = bpy.context.scene; src = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']
cand = bpy.data.objects[sys.argv[sys.argv.index('--') + 1]]
names = {g.index: g.name for g in src.vertex_groups}
dom = np.array([names[max((g for g in v.groups if names[g.group] != 'ReduceProtect'), key=lambda g: g.weight, default=v.groups[0]).group]
                if v.groups else '-' for v in src.data.vertices])
def ev(o):
    b = bmesh.new(); b.from_object(o, bpy.context.evaluated_depsgraph_get()); b.transform(o.matrix_world); return b
def dist():
    bs, bc = ev(src), ev(cand); tc = BVHTree.FromBMesh(bc)
    d = np.array([tc.find_nearest(v.co)[3] for v in bs.verts]); bs.free(); bc.free(); return d
rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
bpy.context.view_layer.update(); rest = dist()
worst = np.zeros(len(rest)); at = np.empty(len(rest), object)
for act in bpy.data.actions:
    rig.animation_data.action = act; f0, f1 = (int(x) for x in act.frame_range)
    for f in range(f0, f1 + 1, 3):
        sc.frame_set(f); d = dist(); m = d > worst; worst[m] = d[m]; at[m] = f'{act.name}:{f}'
np.save(os.path.join(HERE, 'work', f'worst_{cand.name}.npy'), worst)
rows = []
for b in np.unique(dom):
    m = dom == b
    rows.append((np.percentile(worst[m], 99) * 1000, b, m.sum(), np.percentile(rest[m], 99) * 1000, worst[m].max() * 1000, at[m][worst[m].argmax()]))
for r in sorted(rows, reverse=True)[:14]:
    print(f'REGION {r[1]:18s} n={r[2]:5d} anim p99 {r[0]:6.1f} mm  rest p99 {r[3]:5.1f}  max {r[4]:6.1f} at {r[5]}')
print('ALL anim p99 %.1f rest p99 %.1f' % (np.percentile(worst, 99) * 1000, np.percentile(rest, 99) * 1000))
