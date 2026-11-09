"""New body UVs for the reduced textured master and its textures baked from the unreduced one (reduce_textured.py):
Meshy's fragmented layout did not survive the collapse. Body (non-head) faces get a Smart UV Project (66 deg, uniform
texel density) in UVMap; head faces (they use HeadUV and the head set) are parked in a corner texel. Cycles bakes,
selected to active at rest pose (both bodies share the rest shape; rays within 3 cm), PIECE BY PIECE (each reduced
piece only from its own unreduced piece: with the whole body as the source, rays from the thin pauldrons hit the
coif and the plate under them), from the unreduced body with Meshy's own UVs and maps: the base colour and the roughness as emission, the normal map as a tangent-space NORMAL
bake. Meshy's normal map is in the -Y (DirectX) convention (prepare_actor_glb.py converted it); its green channel is
inverted before use, so the bake comes out +Y. Writes <out dir>/texture_urls_0_{base_color,roughness,normal}.png
(Meshy's names: compose_m270.py reads them in place of meshy/retexture_v1) and the master with the new UVMap. The
pieces are assembled by bake coverage (alpha) and the islands padded 8 texels.
Runs once, guarded by an object property. Args: -- <full blend> <reduced blend> <out dir>"""
import bpy, sys, os, math
import numpy as np
full, red, outd = sys.argv[sys.argv.index('--') + 1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
M = os.path.join(HERE, 'meshy', 'retexture_v1')
N = 1024
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(red))
body = bpy.data.objects['Body']; me = body.data
if body.get('rebaked_uv'):
    print('REBAKE already applied'); sys.exit(0)
os.makedirs(outd, exist_ok=True)
sc = bpy.context.scene
bpy.data.objects['Rig'].data.pose_position = 'REST'
# ---------------------------------------------------------------- new UVMap on the body faces
hd = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', hd)
me.uv_layers.active = me.uv_layers['UVMap']
for o in bpy.data.objects:
    o.select_set(o == body)
bpy.context.view_layer.objects.active = body
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_mode(type='FACE'); bpy.ops.mesh.select_all(action='DESELECT')
bpy.ops.object.mode_set(mode='OBJECT')
for p in me.polygons:
    p.select = not hd[p.index]
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.004, area_weight=0.0, scale_to_bounds=False)
bpy.ops.uv.pack_islands(margin=0.004, rotate=True)
bpy.ops.object.mode_set(mode='OBJECT')
uv = me.uv_layers['UVMap'].data
for p in me.polygons:
    if hd[p.index]:
        for li in p.loop_indices:
            uv[li].uv = (0.5 / N, 0.5 / N)
# ---------------------------------------------------------------- the unreduced body as the bake source
with bpy.data.libraries.load(os.path.abspath(full), link=False) as (src, dst):
    dst.objects = ['Body']
srcb = dst.objects[0]; srcb.name = 'BodySrc'; sc.collection.objects.link(srcb)
for mo in list(srcb.modifiers):
    srcb.modifiers.remove(mo)
for mo in body.modifiers:
    mo.show_render = mo.show_viewport = False
srcb.matrix_world = body.matrix_world.copy()


def img(path, colour):
    im = bpy.data.images.load(path); im.colorspace_settings.name = 'sRGB' if colour else 'Non-Color'; return im


nrm = img(os.path.join(M, 'texture_urls_0_normal.png'), False)
px = np.array(nrm.pixels[:]).reshape(-1, 4); px[:, 1] = 1.0 - px[:, 1]; nrm.pixels[:] = px.ravel()
SRC = {'base': img(os.path.join(M, 'texture_urls_0_base_color.png'), True),
       'rough': img(os.path.join(M, 'texture_urls_0_roughness.png'), False), 'normal': nrm}


def src_material(kind):
    m = bpy.data.materials.new('bake_src_' + kind); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); uvn = nt.nodes.new('ShaderNodeUVMap'); uvn.uv_map = 'UVMap'
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = SRC['base' if kind == 'base' else 'rough' if kind == 'rough' else 'normal']
    nt.links.new(uvn.outputs['UV'], t.inputs['Vector'])
    if kind == 'normal':
        bs = nt.nodes.new('ShaderNodeBsdfPrincipled'); nm = nt.nodes.new('ShaderNodeNormalMap'); nm.uv_map = 'UVMap'
        nt.links.new(t.outputs['Color'], nm.inputs['Color']); nt.links.new(nm.outputs['Normal'], bs.inputs['Normal'])
        nt.links.new(bs.outputs['BSDF'], out.inputs['Surface'])
    else:
        em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(t.outputs['Color'], em.inputs['Color'])
        nt.links.new(em.outputs['Emission'], out.inputs['Surface'])
    return m


def tgt_material(image):
    m = bpy.data.materials.new('bake_tgt'); m.use_nodes = True; nt = m.node_tree
    uvn = nt.nodes.new('ShaderNodeUVMap'); uvn.uv_map = 'UVMap'
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = image; nt.links.new(uvn.outputs['UV'], t.inputs['Vector'])
    nt.nodes.active = t
    return m


import bmesh


def piece_copy(ob, piece, body_only):
    """a new object with only the faces of one piece (and, for the target, only body faces)"""
    o = ob.copy(); o.data = ob.data.copy(); o.name = f'{ob.name}_p{piece}'; sc.collection.objects.link(o)
    for mo in list(o.modifiers):
        o.modifiers.remove(mo)
    bm = bmesh.new(); bm.from_mesh(o.data)
    pl = bm.verts.layers.int['piece']; hl = bm.faces.layers.int.get('head')
    gone = [f for f in bm.faces if f.verts[0][pl] != piece or (body_only and hl is not None and f[hl])]
    bmesh.ops.delete(bm, geom=gone, context='FACES'); bm.to_mesh(o.data); bm.free()
    return o


pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
pieces = sorted({int(pv[p.vertices[0]]) for p in me.polygons if not hd[p.index]})
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 1
bk = sc.render.bake; bk.use_selected_to_active = True; bk.cage_extrusion = 0.01; bk.max_ray_distance = 0.03
bk.margin = 0; bk.use_clear = False         # each image starts transparent: only the texels a piece bakes get alpha
acc = {k: np.zeros((N, N, 4)) for k in ('base', 'rough', 'normal')}
for piece in pieces:
    tgt = piece_copy(body, piece, True); src_ = piece_copy(srcb, piece, False)
    if not len(tgt.data.polygons) or not len(src_.data.polygons):
        bpy.data.objects.remove(tgt); bpy.data.objects.remove(src_); continue
    tgt.data.uv_layers.active = tgt.data.uv_layers['UVMap']
    for kind, btype, colour in (('base', 'EMIT', True), ('rough', 'EMIT', False), ('normal', 'NORMAL', False)):
        im = bpy.data.images.new('bake', N, N, alpha=True, float_buffer=False)
        im.colorspace_settings.name = 'sRGB' if colour else 'Non-Color'; im.pixels[:] = np.zeros(N * N * 4)
        src_.data.materials.clear(); src_.data.materials.append(src_material(kind))
        tgt.data.materials.clear(); tgt.data.materials.append(tgt_material(im))
        for o in bpy.data.objects:
            o.select_set(o in (tgt, src_))
        bpy.context.view_layer.objects.active = tgt
        if btype == 'NORMAL':
            bk.normal_space = 'TANGENT'; bk.normal_r, bk.normal_g, bk.normal_b = 'POS_X', 'POS_Y', 'POS_Z'
        bpy.ops.object.bake(type=btype)
        px = np.array(im.pixels[:]).reshape(N, N, 4)
        m = px[..., 3] > 0.5
        acc[kind][m] = px[m]; acc[kind][m, 3] = 1.0
        bpy.data.images.remove(im)
    bpy.data.objects.remove(tgt); bpy.data.objects.remove(src_)
print('REBAKE pieces', len(pieces), 'coverage', round(float((acc['base'][..., 3] > 0).mean()), 3))
for kind, name, colour in (('base', 'base_color', True), ('rough', 'roughness', False), ('normal', 'normal', False)):
    a_ = acc[kind]; filled = a_[..., 3] > 0
    for _ in range(8):                                   # pad the islands into the gaps (no scipy in Blender)
        s_ = np.zeros_like(a_); c_ = np.zeros((N, N))
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            sh = np.roll(np.roll(a_, dy, 0), dx, 1); fh = np.roll(np.roll(filled, dy, 0), dx, 1)
            s_[fh] += sh[fh]; c_[fh] += 1
        new = ~filled & (c_ > 0)
        a_[new] = s_[new] / c_[new, None]; filled |= new
    im = bpy.data.images.new('out_' + name, N, N, alpha=False, float_buffer=False)
    im.colorspace_settings.name = 'sRGB' if colour else 'Non-Color'
    a_[..., 3] = 1.0; im.pixels[:] = a_.ravel()
    im.filepath_raw = os.path.join(os.path.abspath(outd), f'texture_urls_0_{name}.png'); im.file_format = 'PNG'; im.save()
    print('REBAKE', name, '->', im.filepath_raw)
# ---------------------------------------------------------------- restore the master (materials, modifiers) and save
for mo in body.modifiers:
    mo.show_render = mo.show_viewport = True
bpy.data.objects.remove(srcb)
bpy.data.objects['Rig'].data.pose_position = 'POSE'
body['rebaked_uv'] = True
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(red))
print('REBAKE body UVMap islands baked at', N)
