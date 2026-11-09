"""Reduce the weighted body after weighting (collapse decimation in the bind pose, which is already an S-curve).

Args: <in blend> <out blend> <report json> <body ratio> <head ratio> <teeth ratio>
Head skin (dominant Xheadpiv/Xhead/Xjawpiv) gets the milder ratio, the teeth pieces their own; eyes are kept.
Weights are carried by the collapse (vertex groups interpolate).
"""
import bpy, bmesh, sys, json
argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, REP, BODY_R, HEAD_R, TEETH_R = argv[0], argv[1], argv[2], float(argv[3]), float(argv[4]), float(argv[5])
bpy.ops.wm.open_mainfile(filepath=IN)
ob = bpy.data.objects['Dfly']
me = ob.data
HEAD = {ob.vertex_groups[n].index for n in ('Xheadpiv', 'Xhead', 'Xjawpiv') if n in ob.vertex_groups}
before = len(me.polygons)


def head_w(v):
    return sum(g.weight for g in v.groups if g.group in HEAD)


def run(select_fn, ratio):
    bpy.context.view_layer.objects.active = ob
    for o in bpy.data.objects:
        o.select_set(o == ob)
    piece = me.attributes['piece']
    bpy.ops.object.mode_set(mode='OBJECT')
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


def is_body(p, piece):
    return all(piece.data[i].value == 0 for i in p.vertices) and \
        sum(head_w(me.vertices[i]) for i in p.vertices) / len(p.vertices) < 0.5


def is_head(p, piece):
    return all(piece.data[i].value == 0 for i in p.vertices) and \
        sum(head_w(me.vertices[i]) for i in p.vertices) / len(p.vertices) >= 0.5


run(is_body, BODY_R)
mid = len(me.polygons)
run(is_head, HEAD_R)
run(lambda p, piece: all(piece.data[i].value == 2 for i in p.vertices), TEETH_R)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.quads_convert_to_tris()
bpy.ops.object.mode_set(mode='OBJECT')
# piece attribute survives decimation only on kept vertices; re-check the four-influence limit
mx = max(sum(1 for g in v.groups if g.weight > 0) for v in me.vertices)
rep = {'before': before, 'after_body': mid, 'after': len(me.polygons), 'max_influences': mx,
       'wings': len(bpy.data.objects['Dfly_Wings'].data.polygons)}
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'))
print('REDUCE', rep)
