"""Sharp-texture UVs (claude_shared/uv_atlas.py): body set (UVMap, hands denser) and head set (HeadUV: face, hair, teeth, eyes; mouth and eyes denser), plus the uploads:
the whole figure for the body (head faces collapsed to one UV point: they occlude but take no texels), the head parts alone for the head.
Args: <in blend> <out blend> <body upload> <head upload> <report json>. Never re-run once its uploads went to Meshy."""
import bpy, bmesh, sys, os, json
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'claude_shared'))
import uv_atlas
IN, OUT, UP_B, UP_H, REP = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; rig = body.parent; me = body.data
if rig.animation_data: rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
bpy.context.view_layer.update()
nv = len(me.vertices); nf = len(me.polygons)
assert all(len(p.vertices) == 3 for p in me.polygons)
pa = np.zeros(nv, np.int32); me.attributes['part'].data.foreach_get('value', pa)
fv = np.array([p.vertices[:] for p in me.polygons])
is_head = (pa[fv] >= 10).all(1)
hg = {f'Bip01 {s} Hand' for s in 'LR'} | {f'Bip01 {s} Finger{n}' for s in 'LR' for n in ('0', '01', '02', '1', '11', '12', '2', '21', '22', '3', '31', '32', '41', '42')}
P = np.array([v.co[:] for v in me.vertices])


def layout(faces, factor, name, dense, **options):
    dup = body.copy(); dup.data = me.copy(); dup.modifiers.clear(); dup.parent = None; dup.matrix_world = body.matrix_world
    bpy.context.scene.collection.objects.link(dup); dm = dup.data
    dm.attributes.new('fo', 'INT', 'FACE').data.foreach_set('value', list(range(nf)))
    dm.attributes.new('vo', 'INT', 'POINT').data.foreach_set('value', list(range(nv)))
    bm = bmesh.new(); bm.from_mesh(dm); bm.faces.ensure_lookup_table()
    keep = set(faces.tolist())
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index not in keep], context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.to_mesh(dm); bm.free(); dm.update()
    names = {g.index: g.name for g in dup.vertex_groups}
    vo = np.zeros(len(dm.vertices), np.int32); dm.attributes['vo'].data.foreach_get('value', vo)
    idx = [v.index for v in dm.vertices if dense(int(vo[v.index]), v, names)]
    for g in list(dup.vertex_groups): dup.vertex_groups.remove(g)
    vg = dup.vertex_groups.new(name='DENSE')
    if idx: vg.add(idx, 1.0, 'REPLACE')
    print('LAYOUT', name, len(dm.polygons), 'dense verts', len(idx), flush=True)
    rep = uv_atlas.unwrap(dup, head_groups=('DENSE',), head_factor=factor, **options)
    fo = np.zeros(len(dm.polygons), np.int32); dm.attributes['fo'].data.foreach_get('value', fo)
    uv = dm.uv_layers['UVMap'].data
    out = {}
    vo2 = np.zeros(len(dm.vertices), np.int32); dm.attributes['vo'].data.foreach_get('value', vo2)
    for p in dm.polygons:
        for li in p.loop_indices:
            out[(int(fo[p.index]), int(vo2[dm.loops[li].vertex_index]))] = tuple(uv[li].uv)
    bpy.data.objects.remove(dup)
    return out, rep


body_f = np.where(~is_head)[0]; head_f = np.where(is_head)[0]
ub, rb = layout(body_f, 1.5, 'body', lambda i, v, names: any(names[g.group] in hg and g.weight > 0.3 for g in v.groups))
uh, rh = layout(head_f, 1.6, 'head', lambda i, v, names: pa[i] in (12, 13) or (P[i, 1] < -0.02 and P[i, 2] > 0.6 and pa[i] == 10))
for name in ('UVMap', 'HeadUV'):
    if name in me.uv_layers: me.uv_layers.remove(me.uv_layers[name])
    me.uv_layers.new(name=name)
loops = np.zeros(len(me.loops), np.int32); me.loops.foreach_get('vertex_index', loops)
bu = np.zeros((len(me.loops), 2), np.float32); hu = bu.copy()
for p in me.polygons:
    f = p.index
    for li in p.loop_indices:
        v = int(loops[li])
        if is_head[f]: hu[li] = uh[(f, v)]
        else: bu[li] = ub[(f, v)]
me.uv_layers['UVMap'].data.foreach_set('uv', bu.ravel()); me.uv_layers['HeadUV'].data.foreach_set('uv', hu.ravel())
fa = me.attributes.new('head', 'INT', 'FACE'); fa.data.foreach_set('value', is_head.astype(np.int32).tolist())
me.uv_layers.active = me.uv_layers['UVMap']
bpy.ops.wm.save_as_mainfile(filepath=OUT)


def upload(path, faces, uvname):
    dup = body.copy(); dup.data = me.copy(); dup.modifiers.clear(); dup.parent = None; dup.matrix_world = body.matrix_world
    bpy.context.scene.collection.objects.link(dup); dm = dup.data
    for g in list(dup.vertex_groups): dup.vertex_groups.remove(g)
    if uvname == 'HeadUV':
        dm.uv_layers.active = dm.uv_layers['UVMap']
        for i in range(len(dm.loops)): dm.uv_layers['UVMap'].data[i].uv = dm.uv_layers['HeadUV'].data[i].uv
    dm.uv_layers.remove(dm.uv_layers['HeadUV'])
    for a in [a.name for a in dm.attributes if a.name in ('part', 'head')]:
        dm.attributes.remove(dm.attributes[a])
    bm = bmesh.new(); bm.from_mesh(dm); bm.faces.ensure_lookup_table()
    keep = set(faces.tolist())
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index not in keep], context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.to_mesh(dm); bm.free(); dm.update()
    mat = bpy.data.materials.new('m'); dm.materials.clear(); dm.materials.append(mat)
    for o in bpy.data.objects: o.select_set(o is dup)
    bpy.context.view_layer.objects.active = dup
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_animations=False, export_skins=False, export_yup=True, export_attributes=False, export_materials='EXPORT')
    bpy.data.objects.remove(dup)


upload(UP_B, np.arange(nf), 'UVMap')
upload(UP_H, head_f, 'HeadUV')
json.dump({'body': rb, 'head': rh}, open(REP, 'w'), indent=1, default=str)
print('UVDONE', rb.get('use') if isinstance(rb, dict) else rb, rh.get('use') if isinstance(rh, dict) else rh)
