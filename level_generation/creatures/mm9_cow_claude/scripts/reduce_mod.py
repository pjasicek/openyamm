"""Reduce the weighted 'Body' to a target triangle count with the Decimate modifier (collapse, triangulated, vertex
groups interpolated), keeping the head denser: the modifier's vertex group ('_keep' = 1 - KEEP_HEAD x head weight)
limits where it collapses. Pieces (piece != 0: eyes, teats, beard, tassel) are kept as
they are and joined back. Args: <in blend> <out blend> <report json> <target tris> [KEEP_HEAD 0..1]"""
import bpy, bmesh, sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rigcfg
argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, REP, TARGET = argv[0], argv[1], argv[2], int(argv[3])
KEEP_HEAD = float(argv[4]) if len(argv) > 4 else 0.6   # 0 = head like the body, 1 = head untouched
bpy.ops.wm.open_mainfile(filepath=IN)
ob = bpy.data.objects['Body']
me = ob.data
before = len(me.polygons)
# split the pieces off (kept unchanged)
bpy.context.view_layer.objects.active = ob
for o in bpy.data.objects:
    o.select_set(o == ob)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='DESELECT')
bpy.ops.object.mode_set(mode='OBJECT')
piece = me.attributes['piece']
for v in me.vertices:
    v.select = piece.data[v.index].value != 0
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_mode(type='VERT')
bpy.ops.mesh.separate(type='SELECTED')
bpy.ops.object.mode_set(mode='OBJECT')
pieces = [o for o in bpy.data.objects if o.type == 'MESH' and o != ob and o.name.startswith('Body')]
for o in pieces:   # eyes, teats, tassel, beard: half their triangles
    bpy.context.view_layer.objects.active = o
    for o2 in bpy.data.objects:
        o2.select_set(o2 == o)
    d_ = o.modifiers.new('dec', 'DECIMATE'); d_.ratio = float(os.environ.get('PIECE_RATIO', '0.5'))
    bpy.ops.object.modifier_apply(modifier='dec')
bpy.context.view_layer.objects.active = ob
gi = {g.name: g.index for g in ob.vertex_groups}
head = {gi[n] for n in rigcfg.HEAD_BONES if n in gi}
keep = ob.vertex_groups.new(name='_keep')
for v in me.vertices:
    h = sum(g.weight for g in v.groups if g.group in head)
    keep.add([v.index], 1.0 - KEEP_HEAD * min(1.0, h), 'REPLACE')   # where to decimate (head less)
tris = sum(len(p.vertices) - 2 for p in me.polygons)
from mathutils.bvhtree import BVHTree
bm0 = bmesh.new(); bm0.from_mesh(me)
dense = BVHTree.FromBMesh(bm0)
mod = ob.modifiers.new('dec', 'DECIMATE')
mod.decimate_type = 'COLLAPSE'
mod.use_collapse_triangulate = True
mod.vertex_group = '_keep'
mod.vertex_group_factor = 1.0
piece_tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in pieces)
lo, hi = 0.0, 1.0
for _ in range(14):   # the modifier's ratio is not exact with a vertex group: bisect on the evaluated count
    mod.ratio = (lo + hi) / 2
    dg = bpy.context.evaluated_depsgraph_get()
    n = len(ob.evaluated_get(dg).data.polygons)
    if n + piece_tris > TARGET:
        hi = mod.ratio
    else:
        lo = mod.ratio
mod.ratio = (lo + hi) / 2
bpy.ops.object.modifier_apply(modifier='dec')
ob.vertex_groups.remove(ob.vertex_groups['_keep'])
# collapse optimum placement throws single vertices far off near-flat skin: snap every vertex back onto the dense skin
snapped, worst = 0, 0.0
for v in me.vertices:
    near = dense.find_nearest(v.co)
    d = near[3]
    worst = max(worst, d)
    if d > 0.003:
        v.co = near[0]; snapped += 1
for o in pieces:
    o.select_set(True)
ob.select_set(True)
bpy.context.view_layer.objects.active = ob
bpy.ops.object.join()
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.quads_convert_to_tris()
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.vertex_group_limit_total(limit=4)
bpy.ops.object.vertex_group_normalize_all(lock_active=False)
for p in me.polygons:
    p.use_smooth = True
piece = me.attributes['piece']
rep = {'snapped': snapped, 'worst_off_skin': worst, 'before': before, 'after': len(me.polygons), 'ratio': mod.ratio if False else (lo + hi) / 2,
       'pieces': sum(1 for p in me.polygons if piece.data[p.vertices[0]].value != 0),
       'head_faces': sum(1 for p in me.polygons
                         if sum(sum(g.weight for g in me.vertices[i].groups if g.group in head) for i in p.vertices)
                         / len(p.vertices) >= 0.5)}
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'))
print('REDUCE', rep)
