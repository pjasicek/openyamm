"""New UVs for both texture sets of the reduced textured master (reduce_textured.py) and their maps baked from the
unreduced copy (after the m270 lich's rebake_body_uv.py). Body faces get a Smart UV Project (66 deg, uniform texel
density) in UVMap, head faces one in HeadUV; each set parks the other's faces in a corner texel. Cycles bakes,
selected to active at rest pose (rays within 8 mm, then 3 cm where those miss), GARMENT BY GARMENT (each reduced garment only from its own
unreduced garment: with the whole body as the source, rays from thin shells hit the layer under them), from the
unreduced body with Meshy's UVs and maps (body faces: <body maps> on UVMap, head faces: <head maps> on HeadUV): base
colour and roughness as emission, the normal map as a tangent-space NORMAL bake. Meshy's normal maps are -Y
(DirectX; tools/normal_map_convention.py measures -1.0 on all of them): their green channel is inverted before use,
so the bakes come out +Y. The garments are assembled by bake coverage (alpha; each image starts transparent) and the
islands padded 8 texels. Writes <out>/body/ and <out>/head/ texture_urls_0_{base_color,roughness,normal}.png (Meshy's
names, read by the compose script in place of the Meshy folders) and the master with the new UV layers.
Runs once, guarded by an object property. Args: -- <full blend> <reduced blend> <body maps> <head maps> <out dir>"""
import bpy, bmesh, sys, os, math
import numpy as np
full, red, bdir, hdir, outd = sys.argv[sys.argv.index('--') + 1:]
N = 1024
import json
CFG = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reduce2.json')))
UV_ANGLE, UV_MARGIN = CFG.get('uv_angle', 66), CFG.get('uv_margin', 0.004)   # m398's angular bones: 66 deg made thousands
                                                                         # of tiny islands (26 % of the atlas)
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(red))
body = bpy.data.objects['Body']; me = body.data
if body.get('rebaked_uv'):
    print('REBAKE already applied'); sys.exit(0)
sc = bpy.context.scene
bpy.data.objects['Rig'].data.pose_position = 'REST'
hd = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', hd)
for o in bpy.data.objects:
    o.select_set(o == body)
bpy.context.view_layer.objects.active = body
# ---------------------------------------------------------------- new UV layouts (each set's faces; the other's parked)
for layer, sel in (('UVMap', 0), ('HeadUV', 1)):
    me.uv_layers.active = me.uv_layers[layer]
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_mode(type='FACE'); bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    for p in me.polygons:
        p.select = bool(hd[p.index]) == bool(sel)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(UV_ANGLE), island_margin=UV_MARGIN, area_weight=0.0, scale_to_bounds=False)
    bpy.ops.uv.pack_islands(margin=UV_MARGIN, rotate=True)
    bpy.ops.object.mode_set(mode='OBJECT')
    uv = me.uv_layers[layer].data
    for p in me.polygons:
        if bool(hd[p.index]) != bool(sel):
            for li in p.loop_indices:
                uv[li].uv = (0.5 / N, 0.5 / N)
me.uv_layers.active = me.uv_layers['UVMap']
# ---------------------------------------------------------------- the unreduced body as the bake source
with bpy.data.libraries.load(os.path.abspath(full), link=False) as (src, dst):
    dst.objects = ['Body']
srcb = dst.objects[0]; srcb.name = 'BodySrc'; sc.collection.objects.link(srcb)
for mo in list(srcb.modifiers):
    srcb.modifiers.remove(mo)
for mo in body.modifiers:
    mo.show_render = mo.show_viewport = False
srcb.matrix_world = body.matrix_world.copy()


def img(path, colour, flip_g=False):
    im = bpy.data.images.load(os.path.abspath(path)); im.colorspace_settings.name = 'sRGB' if colour else 'Non-Color'
    if flip_g:
        px = np.array(im.pixels[:]).reshape(-1, 4); px[:, 1] = 1.0 - px[:, 1]; im.pixels[:] = px.ravel()
    return im


SRC = {s: {'base': img(os.path.join(d, 'texture_urls_0_base_color.png'), True),
           'rough': img(os.path.join(d, 'texture_urls_0_roughness.png'), False),
           'normal': img(os.path.join(d, 'texture_urls_0_normal.png'), False, True)} for s, d in (('body', bdir), ('head', hdir))}


def src_material(kind, s):
    layer = 'UVMap' if s == 'body' else 'HeadUV'
    m = bpy.data.materials.new(f'bake_src_{kind}_{s}'); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); uvn = nt.nodes.new('ShaderNodeUVMap'); uvn.uv_map = layer
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = SRC[s][kind]; nt.links.new(uvn.outputs['UV'], t.inputs['Vector'])
    if kind == 'normal':
        bs = nt.nodes.new('ShaderNodeBsdfPrincipled'); nm = nt.nodes.new('ShaderNodeNormalMap'); nm.uv_map = layer
        nt.links.new(t.outputs['Color'], nm.inputs['Color']); nt.links.new(nm.outputs['Normal'], bs.inputs['Normal'])
        nt.links.new(bs.outputs['BSDF'], out.inputs['Surface'])
    else:
        em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(t.outputs['Color'], em.inputs['Color'])
        nt.links.new(em.outputs['Emission'], out.inputs['Surface'])
    return m


def tgt_material(image, layer):
    m = bpy.data.materials.new('bake_tgt'); m.use_nodes = True; nt = m.node_tree
    uvn = nt.nodes.new('ShaderNodeUVMap'); uvn.uv_map = layer
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = image; nt.links.new(uvn.outputs['UV'], t.inputs['Vector'])
    nt.nodes.active = t
    return m


def garment_copy(ob, g, head_sel):
    """a new object with only the faces of one garment (head_sel: None all, 0 body faces, 1 head faces)"""
    o = ob.copy(); o.data = ob.data.copy(); o.name = f'{ob.name}_g{g}'; sc.collection.objects.link(o)
    for mo in list(o.modifiers):
        o.modifiers.remove(mo)
    bm = bmesh.new(); bm.from_mesh(o.data)
    gl = bm.verts.layers.int['garment']; hl = bm.faces.layers.int['head']
    gone = [f for f in bm.faces if f.verts[0][gl] != g or (head_sel is not None and bool(f[hl]) != bool(head_sel))]
    bmesh.ops.delete(bm, geom=gone, context='FACES'); bm.to_mesh(o.data); bm.free()
    return o


gv = np.zeros(len(me.vertices), np.int32); me.attributes['garment'].data.foreach_get('value', gv)
garments = sorted(set(gv.tolist()))
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 1
bk = sc.render.bake; bk.use_selected_to_active = True; bk.cage_extrusion = 0.01; bk.max_ray_distance = 0.03
bk.margin = 0; bk.use_clear = False                     # each image starts transparent: only baked texels get alpha
acc = {(s, k): np.zeros((N, N, 4)) for s in ('body', 'head') for k in ('base', 'rough', 'normal')}
for g in garments:
    src_ = garment_copy(srcb, g, None)
    if not len(src_.data.polygons):
        bpy.data.objects.remove(src_); continue
    for s, sel, layer in (('body', 0, 'UVMap'), ('head', 1, 'HeadUV')):
        tgt = garment_copy(body, g, sel)
        if not len(tgt.data.polygons):
            bpy.data.objects.remove(tgt); continue
        tgt.data.uv_layers.active = tgt.data.uv_layers[layer]; tgt.data.uv_layers[layer].active_render = True
        for kind, btype, colour in (('base', 'EMIT', True), ('rough', 'EMIT', False), ('normal', 'NORMAL', False)):
            im = bpy.data.images.new('bake', N, N, alpha=True, float_buffer=False)
            im.colorspace_settings.name = 'sRGB' if colour else 'Non-Color'; im.pixels[:] = np.zeros(N * N * 4)
            src_.data.materials.clear()
            src_.data.materials.append(src_material(kind, 'body')); src_.data.materials.append(src_material(kind, 'head'))
            # after the slots: materials.clear() resets every face's index to 0 (the heads first baked from the body maps)
            shd = np.zeros(len(src_.data.polygons), np.int32); src_.data.attributes['head'].data.foreach_get('value', shd)
            for p in src_.data.polygons:
                p.material_index = int(shd[p.index])     # 0 body set, 1 head set
            tgt.data.materials.clear(); tgt.data.materials.append(tgt_material(im, layer))
            for o in bpy.data.objects:
                o.select_set(o in (tgt, src_))
            bpy.context.view_layer.objects.active = tgt
            if btype == 'NORMAL':
                bk.normal_space = 'TANGENT'; bk.normal_r, bk.normal_g, bk.normal_b = 'POS_X', 'POS_Y', 'POS_Z'
            # short rays first (8 mm: on one-shell bodies 3 cm rays reached the maw and the body beside the arm), the
            # 3 cm bake only where the short rays found nothing
            res = []
            for cage, dist in ((0.004, 0.008), (0.01, 0.03)):
                bk.cage_extrusion = cage; bk.max_ray_distance = dist
                im.pixels[:] = np.zeros(N * N * 4)
                bpy.ops.object.bake(type=btype)
                res.append(np.array(im.pixels[:]).reshape(N, N, 4))
            px = np.where((res[0][..., 3] > 0.5)[..., None], res[0], res[1])
            m = px[..., 3] > 0.5
            acc[(s, kind)][m] = px[m]; acc[(s, kind)][m, 3] = 1.0
            bpy.data.images.remove(im)
        bpy.data.objects.remove(tgt)
    bpy.data.objects.remove(src_)
for s in ('body', 'head'):
    os.makedirs(os.path.join(outd, s), exist_ok=True)
    print('REBAKE', s, 'garments', len(garments), 'coverage', round(float((acc[(s, 'base')][..., 3] > 0).mean()), 3))
    for kind, name, colour in (('base', 'base_color', True), ('rough', 'roughness', False), ('normal', 'normal', False)):
        a_ = acc[(s, kind)]; filled = a_[..., 3] > 0
        for _ in range(8):                               # pad the islands into the gaps (no scipy in Blender)
            s_ = np.zeros_like(a_); c_ = np.zeros((N, N))
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                sh = np.roll(np.roll(a_, dy, 0), dx, 1); fh = np.roll(np.roll(filled, dy, 0), dx, 1)
                s_[fh] += sh[fh]; c_[fh] += 1
            new = ~filled & (c_ > 0)
            a_[new] = s_[new] / c_[new, None]; filled |= new
        im = bpy.data.images.new('out_' + name, N, N, alpha=False, float_buffer=False)
        im.colorspace_settings.name = 'sRGB' if colour else 'Non-Color'
        a_[..., 3] = 1.0; im.pixels[:] = a_.ravel()
        im.filepath_raw = os.path.join(os.path.abspath(outd), s, f'texture_urls_0_{name}.png'); im.file_format = 'PNG'
        im.save()
for mo in body.modifiers:
    mo.show_render = mo.show_viewport = True
bpy.data.objects.remove(srcb)
bpy.data.objects['Rig'].data.pose_position = 'POSE'
body['rebaked_uv'] = True
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(red))
print('REBAKE done: body and head sets at', N)
