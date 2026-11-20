"""Worst two-way surface distances between the source and a ladder candidate at one frame: prints the top points
(position, dominant source bone, which side) to find what drives the max. Usage: blender -b -P worst_points.py --
<Cand_75> <clip:frame> [n]"""
import os, sys, bpy, bmesh
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]; cand, cf = a[:2]; n = int(a[2]) if len(a) > 2 else 12
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'ladder.blend'))
sc = bpy.context.scene; src = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']; c = bpy.data.objects[cand]
names = {g.index: g.name for g in src.vertex_groups}
dom = [names[max(v.groups, key=lambda g: g.weight).group] if v.groups else '-' for v in src.data.vertices]
clip, f = cf.split(':'); rig.animation_data.action = bpy.data.actions[clip]; sc.frame_set(int(f))
def ev(o):
    b = bmesh.new(); b.from_object(o, bpy.context.evaluated_depsgraph_get()); b.transform(o.matrix_world)
    b.verts.ensure_lookup_table(); return b
bs, bc = ev(src), ev(c); ts, tc = BVHTree.FromBMesh(bs), BVHTree.FromBMesh(bc)
kd = KDTree(len(bs.verts))
for v in bs.verts:
    kd.insert(v.co, v.index)
kd.balance()
rows = [(tc.find_nearest(v.co)[3], 'src', v.index, dom[v.index], tuple(round(x, 3) for x in v.co)) for v in bs.verts]
rows += [(ts.find_nearest(v.co)[3], 'cand', v.index, dom[kd.find(v.co)[1]], tuple(round(x, 3) for x in v.co)) for v in bc.verts]
for r in sorted(rows, reverse=True)[:n]:
    print('WORST', round(r[0] * 1000, 1), 'mm', *r[1:])
