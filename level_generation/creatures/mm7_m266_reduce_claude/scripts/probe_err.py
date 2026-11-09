"""Largest posed surface errors of a ladder candidate at one clip frame, both ways, with position, distance and the
dominant bone of the nearest source vertex. Usage: blender -b -P probe_err.py -- <Cand_70> <clip:frame> [n]"""
import os, sys, bpy, bmesh
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]; cand, cf = a[:2]; N = int(a[2]) if len(a) > 2 else 12
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', os.environ.get('REA_BLEND', 'ladder.blend')))
sc = bpy.context.scene; src = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']; c = bpy.data.objects[cand]
names = {g.index: g.name for g in src.vertex_groups}
_vg = lambda v: [g for g in v.groups if names[g.group] != 'ReduceProtect']
dom = [names[max(_vg(v), key=lambda g: g.weight).group] if _vg(v) else '-' for v in src.data.vertices]
clip, f = cf.split(':'); rig.animation_data.action = bpy.data.actions[clip]; sc.frame_set(int(f))
def ev(o):
    b = bmesh.new(); b.from_object(o, bpy.context.evaluated_depsgraph_get()); b.transform(o.matrix_world)
    b.verts.ensure_lookup_table(); return b
bs, bc = ev(src), ev(c); ts, tc = BVHTree.FromBMesh(bs), BVHTree.FromBMesh(bc)
kd = KDTree(len(bs.verts))
for v in bs.verts:
    kd.insert(v.co, v.index)
kd.balance()
rows = [('src', v.index, tc.find_nearest(v.co)[3], v.co, dom[v.index]) for v in bs.verts]
rows += [('cand', v.index, ts.find_nearest(v.co)[3], v.co, dom[kd.find(v.co)[1]]) for v in bc.verts]
rows.sort(key=lambda r: -r[2])
for side, i, d, co, b in rows[:N]:
    print('ERR', side, i, round(d * 1000, 1), [round(x, 3) for x in co], b)
