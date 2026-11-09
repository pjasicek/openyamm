"""Debug: a source vertex at a clip frame against the candidate: posed positions, nearest candidate vertices with their
rest positions and weights. Usage: blender -b -P dbg_vertex.py -- <Cand> <clip:frame> <source vertex>"""
import os, sys, bpy, bmesh
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cand, cf, vi = sys.argv[sys.argv.index('--') + 1:][:3]; vi = int(vi)
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'ladder.blend'))
sc = bpy.context.scene; src = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']; c = bpy.data.objects[cand]
def ev(o):
    b = bmesh.new(); b.from_object(o, bpy.context.evaluated_depsgraph_get()); b.transform(o.matrix_world); b.verts.ensure_lookup_table(); return b
for clip_f in ('Standing:0', cf):
    clip, f = clip_f.split(':'); rig.animation_data.action = bpy.data.actions[clip]; sc.frame_set(int(f))
    bs, bc = ev(src), ev(c); tc = BVHTree.FromBMesh(bc)
    p = bs.verts[vi].co; loc, nrm, fi, d = tc.find_nearest(p)
    print('DBG', clip_f, 'src', [round(x, 3) for x in p], 'nearest cand', [round(x, 3) for x in loc], round(d * 1000, 1), 'face', fi)
    near = sorted(range(len(bc.verts)), key=lambda i: (bc.verts[i].co - p).length)[:4]
    gn = {g.index: g.name for g in c.vertex_groups}
    for i in near:
        print('DBG   cand v', i, [round(x, 3) for x in bc.verts[i].co], round((bc.verts[i].co - p).length * 1000, 1), 'rest', [round(x, 3) for x in c.data.vertices[i].co],
              [(gn[g.group], round(g.weight, 2)) for g in c.data.vertices[i].groups])
