"""Share of posed two-way error samples over LIM mm per dominant bone (and per GLB part label of the nearest source
vertex), over every 3rd frame of every clip: where does a ladder step's p99 come from.
Usage: blender -b -P err_by_bone.py -- <Cand_60> [lim_mm]"""
import os, sys, bpy, bmesh, collections
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]; cand = a[0]; LIM = float(a[1]) / 1000 if len(a) > 1 else 0.007
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', os.environ.get('REA_BLEND', 'ladder.blend')))
sc = bpy.context.scene; src = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']; c = bpy.data.objects[cand]
names = {g.index: g.name for g in src.vertex_groups}
dom = [names[max([g for g in v.groups if names[g.group] != 'ReduceProtect'] or v.groups, key=lambda g: g.weight).group] if v.groups else '-' for v in src.data.vertices]
mat = [0] * len(src.data.vertices)
for p in src.data.polygons:
    for v in p.vertices: mat[v] = p.material_index
def ev(o):
    b = bmesh.new(); b.from_object(o, bpy.context.evaluated_depsgraph_get()); b.transform(o.matrix_world)
    b.verts.ensure_lookup_table(); return b
cnt = collections.Counter(); tot = 0; worst = collections.defaultdict(float)
for act in bpy.data.actions:
    rig.animation_data.action = act; f0, f1 = (int(x) for x in act.frame_range)
    for f in range(f0, f1 + 1, 3):
        sc.frame_set(f); bs, bc = ev(src), ev(c); ts, tc = BVHTree.FromBMesh(bs), BVHTree.FromBMesh(bc)
        kd = KDTree(len(bs.verts))
        for v in bs.verts: kd.insert(v.co, v.index)
        kd.balance()
        for v in bs.verts:
            d = tc.find_nearest(v.co)[3]; tot += 1
            if d > LIM: k = (mat[v.index], dom[v.index]); cnt[k] += 1; worst[k] = max(worst[k], d)
        for v in bc.verts:
            d = ts.find_nearest(v.co)[3]; tot += 1
            if d > LIM: i = kd.find(v.co)[1]; k = (mat[i], dom[i]); cnt[k] += 1; worst[k] = max(worst[k], d)
        bs.free(); bc.free()
print('TOTAL samples', tot, 'over', LIM * 1000, 'mm:', sum(cnt.values()), f'({sum(cnt.values()) / tot * 100:.2f} %)')
for k, n in cnt.most_common(30):
    print('BONE', k[0], k[1], n, f'{n / tot * 100:.3f} %', 'worst', round(worst[k] * 1000, 1))
