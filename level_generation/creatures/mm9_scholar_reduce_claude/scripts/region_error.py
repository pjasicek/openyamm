"""Where a ladder candidate's surface error sits: for the given frames, both-way vertex->surface distances, counted
per dominant bone of the nearest source vertex (distances above REA_MM, default 5 mm). Usage: blender -b -P
region_error.py -- <Cand_75> <clip:frame,...>"""
import os, sys, bpy, bmesh, collections
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cand, frames = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', os.environ.get('REA_BLEND', 'ladder.blend')))
sc = bpy.context.scene; src = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']; c = bpy.data.objects[cand]
names = {g.index: g.name for g in src.vertex_groups}
dom = [names[max([g for g in v.groups if names[g.group] != 'ReduceProtect'] or v.groups, key=lambda g: g.weight).group] if v.groups else '-' for v in src.data.vertices]
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
    cnt = collections.Counter()
    for v in bs.verts:
        if tc.find_nearest(v.co)[3] > LIM:
            cnt[dom[v.index]] += 1
    for v in bc.verts:
        if ts.find_nearest(v.co)[3] > LIM:
            cnt[dom[kd.find(v.co)[1]]] += 1
    print('REGION', cf, sum(cnt.values()), cnt.most_common(10), flush=True)
