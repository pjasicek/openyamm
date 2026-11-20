"""Sharp-texture UVs (claude_shared/uv_atlas.py) for the two sets, on Meshy's HD-pose shape (attribute `fitco`).

Body set (UVMap): every body part once; the mirrored limb parts (pid 100 + p) share their twin's texels, corner by corner,
as the Dagrell's left limbs. Head set (HeadUV): helmet, skull, jaw, teeth, eyes, neck, mirrored pairs shared too. Uploads are
static GLBs in the HD pose: the whole figure for the body (head and mirror faces collapsed to a UV point, so they occlude but
take no texels), the head parts alone for the head.
Args: <in blend> <out blend> <body upload glb> <head upload glb> <report json> [key=value uv_atlas options]
Never re-run once its uploads went to Meshy: xatlas packs differently per run."""
import bpy, bmesh, sys, os, json
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'claude_shared'))
import uv_atlas
argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, UP_B, UP_H, REP = argv[:5]
opts = {k: (float(v) if '.' in v else int(v) if v.isdigit() else v) for k, v in (a.split('=', 1) for a in argv[5:])}
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; rig = body.parent; me = body.data
if rig.animation_data: rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
bpy.context.view_layer.update()
nv = len(me.vertices); nf = len(me.polygons)
pid = np.zeros(nv, np.int32); me.attributes['pid'].data.foreach_get('value', pid)
fit = np.zeros(nv * 3); me.attributes['fitco'].data.foreach_get('vector', fit); fit = fit.reshape(-1, 3)
fv = np.array([p.vertices[:] for p in me.polygons])
fpid = pid[fv[:, 0]]
HEADP = {11, 15, 19, 21, 22, 26, 40, 45, 46, 54, 55, 63}
HEADP |= {p + 100 for p in HEADP} | {18}
is_head = np.isin(fpid, list(HEADP)) | (fpid >= 200)
is_mirror = (fpid >= 100) & (fpid < 200)
hg = {b for s in 'LR' for b in [f'Bip01 {s} Hand'] + [f'Bip01 {s} {n}{i}' for n in ('Thumb', 'Index', 'Middle', 'Ring', 'Pinky') for i in (1, 2, 3)]}


def layout(faces, factor, name, **options):
    """Unwrap the listed faces on a working copy in the HD pose; returns per-corner UVs {(face, vertex): uv}."""
    dup = body.copy(); dup.data = me.copy(); dup.modifiers.clear(); dup.parent = None; dup.matrix_world = body.matrix_world
    bpy.context.scene.collection.objects.link(dup); dm = dup.data
    dm.attributes.new('fo', 'INT', 'FACE').data.foreach_set('value', list(range(nf)))
    dm.attributes.new('vo', 'INT', 'POINT').data.foreach_set('value', list(range(nv)))
    dm.vertices.foreach_set('co', (np.c_[fit, np.ones(nv)] @ np.linalg.inv(np.array(body.matrix_world)).T)[:, :3].ravel())
    bm = bmesh.new(); bm.from_mesh(dm); bm.faces.ensure_lookup_table()
    keep = set(faces.tolist())
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index not in keep], context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.to_mesh(dm); bm.free(); dm.update()
    names = {g.index: g.name for g in dup.vertex_groups}
    hand = [v.index for v in dm.vertices if any(names[g.group] in hg and g.weight > 0.3 for g in v.groups)]
    for g in list(dup.vertex_groups): dup.vertex_groups.remove(g)
    vg = dup.vertex_groups.new(name='DENSE')
    if hand: vg.add(hand, 1.0, 'REPLACE')
    print('LAYOUT', name, len(dm.polygons), 'dense verts', len(hand), flush=True)
    rep = uv_atlas.unwrap(dup, head_groups=('DENSE',), head_factor=factor, **options)
    fo = np.zeros(len(dm.polygons), np.int32); dm.attributes['fo'].data.foreach_get('value', fo)
    vo = np.zeros(len(dm.vertices), np.int32); dm.attributes['vo'].data.foreach_get('value', vo)
    uv = dm.uv_layers['UVMap'].data
    out = {}
    for p in dm.polygons:
        for li in p.loop_indices:
            out[(int(fo[p.index]), int(vo[dm.loops[li].vertex_index]))] = tuple(uv[li].uv)
    bpy.data.objects.remove(dup)
    return out, rep


body_f = np.where(~is_head & ~is_mirror)[0]; head_f = np.where(is_head & ~is_mirror)[0]
ub, rb = layout(body_f, opts.pop('hand_factor', 1.4), 'body', **opts)
uh, rh = layout(head_f, 1.0, 'head', **opts)
# mirror twin: i-th vertex of part p <-> i-th vertex of part p + 100; faces by their sorted vertices
twin = {}
for p in np.unique(fpid[is_mirror]):
    a = np.where(pid == p - 100)[0]; b = np.where(pid == p)[0]; assert len(a) == len(b), p
    twin.update(dict(zip(b.tolist(), a.tolist())))
by_verts = {tuple(sorted(f.tolist())): i for i, f in enumerate(fv) if not is_mirror[i]}
for name in ('UVMap', 'HeadUV'):
    if name in me.uv_layers: me.uv_layers.remove(me.uv_layers[name])
    me.uv_layers.new(name=name)
loops = np.zeros(len(me.loops), np.int32); me.loops.foreach_get('vertex_index', loops)
bu = np.zeros((len(me.loops), 2), np.float32); hu = bu.copy()
for p in me.polygons:
    f = p.index
    src = f
    vmap = {}
    if is_mirror[f]:
        vs = [twin[int(v)] for v in p.vertices]
        src = by_verts[tuple(sorted(vs))]
        vmap = {int(v): twin[int(v)] for v in p.vertices}
    for li in p.loop_indices:
        v = int(loops[li]); w = vmap.get(v, v)
        if is_head[f]: hu[li] = uh[(src, w)]
        else: bu[li] = ub[(src, w)]
me.uv_layers['UVMap'].data.foreach_set('uv', bu.ravel()); me.uv_layers['HeadUV'].data.foreach_set('uv', hu.ravel())
fa = me.attributes.new('head', 'INT', 'FACE'); fa.data.foreach_set('value', is_head.astype(np.int32).tolist())
me.attributes.new('hand', 'INT', 'FACE').data.foreach_set('value', [0] * nf)
json.dump(dict(body=rb, head=rh, faces=nf, body_unique=len(body_f), head_unique=len(head_f)), open(REP, 'w'), indent=1, default=str)
bpy.ops.wm.save_as_mainfile(filepath=OUT)


def upload(path, which):
    dup = body.copy(); dup.data = me.copy(); dup.modifiers.clear(); dup.parent = None; dup.matrix_world = body.matrix_world
    bpy.context.scene.collection.objects.link(dup); dm = dup.data
    for g in list(dup.vertex_groups): dup.vertex_groups.remove(g)
    dm.vertices.foreach_set('co', (np.c_[fit, np.ones(nv)] @ np.linalg.inv(np.array(body.matrix_world)).T)[:, :3].ravel())
    if which == 'head':
        bm = bmesh.new(); bm.from_mesh(dm); bm.faces.ensure_lookup_table()
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if not is_head[f.index]], context='FACES')
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
        bm.to_mesh(dm); bm.free()
        d2 = np.zeros(len(dm.loops) * 2, np.float32); dm.uv_layers['HeadUV'].data.foreach_get('uv', d2); dm.uv_layers['UVMap'].data.foreach_set('uv', d2)
    else:
        # head and mirror faces: one UV point (they occlude, take no texels)
        d = np.zeros((len(dm.loops), 2), np.float32); dm.uv_layers['UVMap'].data.foreach_get('uv', d.ravel())
        for p in dm.polygons:
            if is_head[p.index] or is_mirror[p.index]:
                for li in p.loop_indices: d[li] = (0.0005, 0.0005)
        dm.uv_layers['UVMap'].data.foreach_set('uv', d.ravel())
    dm.uv_layers.remove(dm.uv_layers['HeadUV'])
    dm.uv_layers.active = dm.uv_layers['UVMap']
    for a in [a.name for a in dm.attributes if a.name in ('pid', 'fitco', 'head', 'hand')]: dm.attributes.remove(dm.attributes[a])
    for o in bpy.data.objects: o.select_set(o == dup)
    bpy.context.view_layer.objects.active = dup
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=path, use_selection=True, export_format='GLB', export_yup=True, export_skins=False,
                              export_animations=False, export_materials='NONE', export_attributes=False)
    print('UPLOAD', path, len(dm.polygons), flush=True)
    bpy.data.objects.remove(dup)


upload(UP_B, 'body'); upload(UP_H, 'head')
print('UV done', json.dumps(dict(body=rb, head=rh), default=str)[:1500])
