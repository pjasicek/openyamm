"""Sharp-texture UVs (claude_shared/uv_atlas.py) on the frozen mesh. Three sets, face attribute `mat`: 0 limbs (breeches above the shin bands, shoes, hands: shared by all tiers, ramps), 1 torso (doublet, skirt, mantle, belt, sleeves and the shin bands: per tier),
2 head (one skin with the hair, eyes: per tier). UVMap = upload layout: torso square side ST at (0,0), limbs square side SL at (ST,0), head faces on one point. HeadUV = head set in its own square. PartUV = each set in its own square.
Args: <in blend> <out blend> <upload glb> <report json>. Never re-run once the upload went to Meshy."""
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
fpart = np.zeros(nf, np.int32); me.attributes['part'].data.foreach_get('value', fpart)
pa = np.zeros(nv, np.int32)
for p in me.polygons:
    for v in p.vertices: pa[v] = max(pa[v], fpart[p.index])
fv = np.array([p.vertices[:] for p in me.polygons])
P = np.array([v.co[:] for v in me.vertices]); cen = P[fv].mean(1)
J = {b.name: np.array(rig.matrix_world @ b.head_local) for b in rig.data.bones}
head = (pa[fv] >= 20).any(1)
fp = pa[fv].max(1)
SHIN_Z = -0.50
torso = np.isin(fp, (1, 7, 8, 9)) | ((fp == 5) & (cen[:, 2] < SHIN_Z))
mat = np.where(head, 2, np.where(torso, 1, 0))
print('FACES', {int(k): int((mat == k).sum()) for k in (0, 1, 2)})
hg = {f'Bip01 {s} Hand' for s in 'LR'} | {f'Bip01 {s} {n}{i}' for s in 'LR' for n in ('Thumb', 'Index', 'Middle', 'Ring', 'Pinky') for i in (1, 2, 3)}
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
uL, rL = layout(np.where(mat == 0)[0], 1.5, 'limbs', lambda i, v, names: any(names[g.group] in hg and g.weight > 0.3 for g in v.groups), size=1792)
uT, rT = layout(np.where(mat == 1)[0], 1.0, 'torso', lambda i, v, names: False, size=2048)
uH, rH = layout(np.where(mat == 2)[0], 1.6, 'head', lambda i, v, names: pa[i] == 22 or (P[i, 1] < -0.03 and P[i, 2] < 0.90 and abs(P[i, 0]) < 0.085 and pa[i] == 20), size=1792)
print('USE', rL, rT, rH)
ST = 0.55; SL = 0.45
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
        elif k == 1:
            q = np.array(uT[(f, v)]); bu[li] = q * ST; pu[li] = q
        else:
            q = np.array(uL[(f, v)]); bu[li] = q * SL + [ST, 0]; pu[li] = q
me.uv_layers['UVMap'].data.foreach_set('uv', bu.ravel()); me.uv_layers['HeadUV'].data.foreach_set('uv', hu.ravel()); me.uv_layers['PartUV'].data.foreach_set('uv', pu.ravel())
fa = me.attributes.new('mat', 'INT', 'FACE'); fa.data.foreach_set('value', mat.astype(np.int32).tolist())
me.uv_layers.active = me.uv_layers['UVMap']
bpy.ops.wm.save_as_mainfile(filepath=OUT)
dup = body.copy(); dup.data = me.copy(); dup.modifiers.clear(); dup.parent = None; dup.matrix_world = body.matrix_world
bpy.context.scene.collection.objects.link(dup); dm = dup.data
for g in list(dup.vertex_groups): dup.vertex_groups.remove(g)
for n in ('HeadUV', 'PartUV'): dm.uv_layers.remove(dm.uv_layers[n])
for a in [a.name for a in dm.attributes if a.name in ('part', 'mat', 'hand', 'graft_s', 'graft_side')]:
    dm.attributes.remove(dm.attributes[a])
mat_ = bpy.data.materials.new('m'); dm.materials.clear(); dm.materials.append(mat_)
for o in bpy.data.objects: o.select_set(o is dup)
bpy.context.view_layer.objects.active = dup
bpy.ops.export_scene.gltf(filepath=UP, export_format='GLB', use_selection=True, export_animations=False, export_skins=False, export_yup=True, export_attributes=False, export_materials='EXPORT')
json.dump({'limbs': rL, 'torso': rT, 'head': rH}, open(REP, 'w'), indent=1, default=str)
print('UVDONE')
