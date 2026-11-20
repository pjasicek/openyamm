"""Where a ladder candidate deviates most: per clip frame, the candidate/source vertices farthest from the other
surface, with their dominant bone. Usage: blender -b -P worst_probe.py -- Cand_55 Death:15 [Attack:9 ...]"""
import os, sys, bpy, bmesh
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'ladder.blend'))
src = bpy.data.objects['Body']; cand = bpy.data.objects[args[0]]; rig = bpy.data.objects['Rig']; sc = bpy.context.scene
def ev(o):
    b = bmesh.new(); b.from_object(o, bpy.context.evaluated_depsgraph_get()); b.transform(o.matrix_world); return b
for spec in args[1:]:
    act, f = spec.split(':'); rig.animation_data.action = bpy.data.actions[act]; sc.frame_set(int(f))
    for a, b_, tag in ((cand, src, 'cand'), (src, cand, 'src')):
        ba, bb = ev(a), ev(b_); t = BVHTree.FromBMesh(bb)
        d = sorted(((t.find_nearest(v.co)[3], v.index, tuple(round(x, 3) for x in v.co)) for v in ba.verts), reverse=True)[:6]
        for dist, i, co in d:
            vg = a.data.vertices[i].groups
            bone = a.vertex_groups[max(vg, key=lambda g: g.weight).group].name if len(vg) else '-'
            print('WORST', spec, tag, round(dist * 1000, 1), 'mm at', co, bone)
        ba.free(); bb.free()
