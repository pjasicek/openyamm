"""(colloidal warrior, from mm9_bigfoot_claude/uv_bf.py) Sharp-texture UVs (claude_shared/uv_atlas.py) on the frozen reduced mesh. Two sets, face attribute `mat`: 0 body (below the neck plane), 2 head (face, crest, ears, eyes). UVMap = body square, head faces on one point (the upload). HeadUV = head set.
The uploads: whole figure with UVMap. Args: <in blend> <out blend> <upload glb> <report json>. Never re-run once the upload went to Meshy."""
import bpy, bmesh, sys, os, json
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'claude_shared'))
import uv_atlas
IN, OUT, UP, REP = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; rig = body.parent; me = body.data
if rig.animation_data: rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
bpy.context.view_layer.update()
nv = len(me.vertices); nf = len(me.polygons)
assert all(len(p.vertices) == 3 for p in me.polygons)
pa = np.zeros(nv, np.int32); me.attributes['part'].data.foreach_get('value', pa)
fv = np.array([p.vertices[:] for p in me.polygons])
P = np.array([v.co[:] for v in me.vertices]); cen = P[fv].mean(1)
J = {b.name: np.array(rig.matrix_world @ b.head_local) for b in rig.data.bones}
C = np.array([0.0, -0.35, 0.53]); Nk = np.array([0.0, -0.43, 1.0]); Nk /= np.linalg.norm(Nk)
head = (pa[fv] >= 13).any(1) | ((((cen - C) @ Nk) > -0.08) & (np.abs(cen[:, 0]) < 0.40))      # face, dome and the upper throat rolls
mat = np.where(head, 2, 0)
print('FACES', {int(k): int((mat == k).sum()) for k in (0, 2)})
hg = {f'Bip01 {s} Hand' for s in 'LR'}
def area(mask):
    t = P[fv[mask]]; return float(np.linalg.norm(np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0]), axis=1).sum() / 2)
print('AREA', area(mat == 0), area(mat == 1), area(mat == 2))
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
uL, rL = layout(np.where(mat == 0)[0], 1.5, 'body', lambda i, v, names: any(names[g.group] in hg and g.weight > 0.3 for g in v.groups), size=2048)
uH, rH = layout(np.where(mat == 2)[0], 1.7, 'head', lambda i, v, names: pa[i] >= 13 or (P[i, 1] < -0.25 and P[i, 2] > 0.55 and abs(P[i, 0]) < 0.25), size=2048)
print('USE', rL, rH)
for name in ('UVMap', 'HeadUV', 'MHUV'):
    if name in me.uv_layers: me.uv_layers.remove(me.uv_layers[name])
me.uv_layers.new(name='UVMap'); me.uv_layers.new(name='HeadUV'); me.uv_layers.new(name='PartUV')
loops = np.zeros(len(me.loops), np.int32); me.loops.foreach_get('vertex_index', loops)
bu = np.zeros((len(me.loops), 2), np.float32); hu = bu.copy(); pu = bu.copy()
for p in me.polygons:
    f = p.index; k = mat[f]
    for li in p.loop_indices:
        v = int(loops[li])
        if k == 2: hu[li] = uH[(f, v)]; pu[li] = uH[(f, v)]
        else:
            q = np.array(uL[(f, v)]); bu[li] = q; pu[li] = q
me.uv_layers['UVMap'].data.foreach_set('uv', bu.ravel()); me.uv_layers['HeadUV'].data.foreach_set('uv', hu.ravel()); me.uv_layers['PartUV'].data.foreach_set('uv', pu.ravel())
fa = me.attributes.new('mat', 'INT', 'FACE'); fa.data.foreach_set('value', mat.astype(np.int32).tolist())
me.uv_layers.active = me.uv_layers['UVMap']
bpy.ops.wm.save_as_mainfile(filepath=OUT)
dup = body.copy(); dup.data = me.copy(); dup.modifiers.clear(); dup.parent = None; dup.matrix_world = body.matrix_world
bpy.context.scene.collection.objects.link(dup); dm = dup.data
for g in list(dup.vertex_groups): dup.vertex_groups.remove(g)
for n in ('HeadUV', 'PartUV'): dm.uv_layers.remove(dm.uv_layers[n])
for a in [a.name for a in dm.attributes if a.name in ('part', 'mat', 'fpart', 'hand', 'graft_s', 'graft_side')]:
    dm.attributes.remove(dm.attributes[a])
mat_ = bpy.data.materials.new('m'); dm.materials.clear(); dm.materials.append(mat_)
for o in bpy.data.objects: o.select_set(o is dup)
bpy.context.view_layer.objects.active = dup
bpy.ops.export_scene.gltf(filepath=UP, export_format='GLB', use_selection=True, export_animations=False, export_skins=False, export_yup=True, export_attributes=False, export_materials='EXPORT')
json.dump({'body': rL, 'head': rH}, open(REP, 'w'), indent=1, default=str)
print('UVDONE')
