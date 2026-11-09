"""Reduce the weighted mouse 'Body' by region to triangle targets (collapse decimation in the bind pose; vertex groups
interpolate). Regions: tail tube (part 1), head (Bone08 + Bone06 >= 0.5), paws (Leg* >= 0.5), body (the rest),
eyes (piece 1, kept: 2 x 192 triangles is already small).

Args: <in blend> <out blend> <report json> <body> <head> <paws> <tail>   (target triangles per region)
"""
import bpy, sys, json
argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, REP = argv[:3]
TARGET = dict(zip(('body', 'head', 'paws', 'tail'), map(int, argv[3:7])))
bpy.ops.wm.open_mainfile(filepath=IN)
ob = bpy.data.objects['Body']
me = ob.data
before = len(me.polygons)


def region_of(p):
    piece, part = me.attributes['piece'], me.attributes['part']
    if any(piece.data[i].value == 1 for i in p.vertices):
        return 'eyes'
    if all(part.data[i].value == 1 for i in p.vertices):
        return 'tail'
    gi = {g.index: g.name for g in ob.vertex_groups}
    head = paws = 0.0
    for i in p.vertices:
        for g in me.vertices[i].groups:
            name = gi[g.group]
            if name in ('Bone08', 'Bone06'):
                head += g.weight
            elif name.startswith('Leg'):
                paws += g.weight
    k = len(p.vertices)
    if paws / k >= 0.5:
        return 'paws'
    if head / k >= 0.5:
        return 'head'
    return 'body'


def count():
    out = {}
    for p in me.polygons:
        r = region_of(p)
        out[r] = out.get(r, 0) + 1
    return out


start = count()
for region, target in TARGET.items():
    have = sum(1 for p in me.polygons if region_of(p) == region)
    if have <= target:
        continue
    bpy.context.view_layer.objects.active = ob
    for o in bpy.data.objects:
        o.select_set(o == ob)
    bpy.ops.object.mode_set(mode='OBJECT')
    for v in me.vertices:
        v.select = False
    for e in me.edges:
        e.select = False
    for p in me.polygons:
        p.select = region_of(p) == region
    for p in me.polygons:
        if p.select:
            for i in p.vertices:
                me.vertices[i].select = True
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='FACE')
    bpy.ops.mesh.decimate(ratio=target / have, use_vertex_group=False, use_symmetry=True, symmetry_axis='X')
    bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.quads_convert_to_tris()
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.vertex_group_limit_total(limit=4)
bpy.ops.object.vertex_group_normalize_all(lock_active=False)
for p in me.polygons:
    p.use_smooth = True
rep = {'before': before, 'regions_before': start, 'regions_after': count(), 'after': len(me.polygons),
       'max_influences': max(sum(1 for g in v.groups if g.weight > 0) for v in me.vertices)}
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1)
print('REDUCE', json.dumps(rep))
