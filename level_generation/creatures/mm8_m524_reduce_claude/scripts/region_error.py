"""Where a ladder candidate's surface error sits: for the given frames, both-way vertex->surface distances, counted
per dominant bone of the nearest source vertex (distances above REA_MM, default 5 mm). Usage: blender -b -P
region_error.py -- <Cand_75> <clip:frame,...>"""
import os, sys, bpy, bmesh, collections
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cand, frames = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'ladder.blend'))
sc = bpy.context.scene; src = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']; c = bpy.data.objects[cand]
names = {g.index: g.name for g in src.vertex_groups}
# the ladder's own ReduceProtect group (weight 1 on head/jaw) is not a bone
dg = lambda v: [g for g in v.groups if names[g.group] != 'ReduceProtect']
dom = [names[max(dg(v), key=lambda g: g.weight).group] if dg(v) else '-' for v in src.data.vertices]
LIM = float(os.environ.get('REA_MM', '5')) / 1000
def ev(o):
    b = bmesh.new(); b.from_object(o, bpy.context.evaluated_depsgraph_get()); b.transform(o.matrix_world)
    b.verts.ensure_lookup_table(); return b
for cf in frames.split(','):
    clip, f = cf.split(':'); rig.animation_data.action = bpy.data.actions[clip]; sc.frame_set(int(f))
    bs, bc = ev(src), ev(c); ts, tc = BVHTree.FromBMesh(bs), BVHTree.FromBMesh(bc)
    kd = KDTree(len(bs.verts))
    for v in bs.verts:
        kd.insert(v.co, v.index)
    kd.balance()
    cnt = collections.Counter(); worst = (0, '')
    for v in bs.verts:
        dd = tc.find_nearest(v.co)[3]
        if dd > LIM:
            cnt[dom[v.index]] += 1
        if dd > worst[0]:
            worst = (dd, f'src {dom[v.index]} at {tuple(round(x, 2) for x in v.co)}')
    for v in bc.verts:
        if ts.find_nearest(v.co)[3] > LIM:
            cnt[dom[kd.find(v.co)[1]]] += 1
        dd = ts.find_nearest(v.co)[3]
        if dd > worst[0]:
            worst = (dd, f'cand {dom[kd.find(v.co)[1]]} at {tuple(round(x, 2) for x in v.co)}')
    print('REGION', cf, sum(cnt.values()), cnt.most_common(10), 'worst', round(worst[0] * 1000, 1), 'mm', worst[1], flush=True)
