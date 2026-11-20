"""Reduce the weighted 'Body' after weighting (collapse decimation in the bind pose; vertex groups interpolate).

Args: <in blend> <out blend> <report json> <body ratio> <piece ratio> [head ratio] [root ratio]
Body faces (piece 0) take <body ratio>, except faces whose vertices are mostly head/jaw weighted, which take the milder
[head ratio] (default = body ratio); small pieces (piece 2: mouth tendrils, teeth) take <piece ratio>.
"""
import bpy, sys, json
argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, REP, BODY_R, PIECE_R = argv[0], argv[1], argv[2], float(argv[3]), float(argv[4])
HEAD_R = float(argv[5]) if len(argv) > 5 else BODY_R
ROOT_R = float(argv[6]) if len(argv) > 6 else None
HEAD_BONES = ('Bone27', 'Bone28', 'Bone30', 'Bone37', 'Bone39')   # MM9 wolf skull, muzzle, jaw, ears
bpy.ops.wm.open_mainfile(filepath=IN)
ob = bpy.data.objects['Body']
me = ob.data
HEAD = {ob.vertex_groups[n].index for n in HEAD_BONES if n in ob.vertex_groups}
before = len(me.polygons)


def head_w(v):
    return sum(g.weight for g in v.groups if g.group in HEAD)


def run(select_fn, ratio):
    if ratio >= 0.999:
        return
    bpy.context.view_layer.objects.active = ob
    for o in bpy.data.objects:
        o.select_set(o == ob)
    bpy.ops.object.mode_set(mode='OBJECT')
    piece = me.attributes['piece']
    for p in me.polygons:
        p.select = select_fn(p, piece)
    for v in me.vertices:
        v.select = False
    for e in me.edges:
        e.select = False
    for p in me.polygons:
        if p.select:
            for i in p.vertices:
                me.vertices[i].select = True
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='FACE')
    bpy.ops.mesh.decimate(ratio=ratio, use_vertex_group=False)
    bpy.ops.object.mode_set(mode='OBJECT')


def body_face(p, piece, head):
    if not all(piece.data[i].value == 0 for i in p.vertices):
        return False
    h = sum(head_w(me.vertices[i]) for i in p.vertices) / len(p.vertices) >= 0.5
    return h == head


if ROOT_R is not None and 'Xroot' in ob.vertex_groups:
    ROOT = ob.vertex_groups['Xroot'].index
    run(lambda p, pc: sum(sum(g.weight for g in me.vertices[i].groups if g.group == ROOT) for i in p.vertices)
        / len(p.vertices) >= 0.5, ROOT_R)
    HEAD.discard(ROOT)
    root_faces = len(me.polygons)


def not_root(p):
    if ROOT_R is None or 'Xroot' not in ob.vertex_groups:
        return True
    r = ob.vertex_groups['Xroot'].index
    return sum(sum(g.weight for g in me.vertices[i].groups if g.group == r) for i in p.vertices) / len(p.vertices) < 0.5


run(lambda p, pc: body_face(p, pc, False) and not_root(p), BODY_R)
run(lambda p, pc: body_face(p, pc, True), HEAD_R)
run(lambda p, pc: all(pc.data[i].value == 2 for i in p.vertices), PIECE_R)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.quads_convert_to_tris()
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.vertex_group_limit_total(limit=4)
bpy.ops.object.vertex_group_normalize_all(lock_active=False)
piece = me.attributes['piece']
rep = {'before': before, 'after': len(me.polygons),
       'pieces': sum(1 for p in me.polygons if piece.data[p.vertices[0]].value == 2),
       'max_influences': max(sum(1 for g in v.groups if g.weight > 0) for v in me.vertices)}
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'))
print('REDUCE', rep)
