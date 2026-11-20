"""Worst source vertices (distance to the candidate surface) at the given frames, printed with their REST position
(for patch_keep.py) and dominant bone. Usage: REA_CAND=Cand_75 REA_FRAMES=Running:12,... blender -b -P probe_rest.py"""
import os, bpy, bmesh
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'ladder.blend'))
sc = bpy.context.scene; src = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']; cand = bpy.data.objects[os.environ['REA_CAND']]
names = {g.index: g.name for g in src.vertex_groups}
rest = [v.co.copy() for v in src.data.vertices]
def ev(o):
    b = bmesh.new(); b.from_object(o, bpy.context.evaluated_depsgraph_get()); b.transform(o.matrix_world)
    b.verts.ensure_lookup_table(); return b
for clip, f in [(c.split(':')[0], int(c.split(':')[1])) for c in os.environ['REA_FRAMES'].split(',')]:
    rig.animation_data.action = bpy.data.actions[clip]; sc.frame_set(f)
    bs = ev(src); bc = ev(cand); tc = BVHTree.FromBMesh(bc)
    d = sorted(((tc.find_nearest(v.co)[3], v.index) for v in bs.verts), reverse=True)[:12]
    for dist, i in d:
        gs = [g for g in src.data.vertices[i].groups if g.group in names and names[g.group] != 'ReduceProtect']
        g = max(gs, key=lambda g: g.weight) if gs else None
        print('REST', clip, f, '%.1fmm' % (dist * 1000), '%.3f,%.3f,%.3f' % tuple(rest[i]), names[g.group] if g else '-')
    bs.free(); bc.free()
