"""Texture and LOD one satchel tier. Usage: blender --background --python scripts/finish_tier.py -- <tier>
Opens work/t<N>_lod0.blend (LOD0 with packed UVs plus the full-detail High object) and imports the Meshy retexture
output meshy/retex_t<N>/model_urls_glb.glb (the textured High), fitted onto High by its bounds (Meshy normalises
the returned model). Each LOD0 texel takes the source surface point it shows (nearest_hits): base colour and
roughness sampled from the Meshy maps there, and the High surface normal in LOD0's tangent space. Writes
work/textures/satchel_t<N>_basecolor.png (1024; the project_views.py result instead when the tier sets
base_projection), _normal.png and _metal_rough.png (512; R = 1, G = roughness, B = 0), builds LOD1..3 by collapse decimation
of LOD0 (they keep its UVs) and exports work/t<N>_export.glb with nodes LootSatchelT<N>, _LOD1.._LOD3 for
tools/link_static_model_lods.py (finalize.py runs it).
Tier 1's retexture was made on an earlier LOD0 (that mesh is the colour source); its normal comes from High."""
import bpy, bmesh, sys, os
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tiers import TIERS, ROOT, LOD_RATIOS

N = int(sys.argv[sys.argv.index('--') + 1])
CFG = TIERS[N]
WORK = os.path.join(ROOT, 'work'); TEX = os.path.join(WORK, 'textures'); os.makedirs(TEX, exist_ok=True)
RES = 1024

bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, f't{N}_lod0.blend'))
scene = bpy.context.scene
lod0 = bpy.data.objects[f'LootSatchelT{N}']
high = bpy.data.objects[f'LootSatchelT{N}_High']


def bounds(objs):
    co = [o.matrix_world @ v.co for o in objs for v in o.data.vertices]
    return Vector(map(min, *co)), Vector(map(max, *co))


before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT, 'meshy', f'retex_t{N}', 'model_urls_glb.glb'))
src = [o for o in bpy.data.objects if o not in before and o.type == 'MESH']
for o in src:
    o.select_set(True)
bpy.ops.object.select_all(action='DESELECT')
for o in src:
    o.select_set(True)
bpy.context.view_layer.objects.active = src[0]
bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
if len(src) > 1:
    bpy.ops.object.join()
src = bpy.context.view_layer.objects.active
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
target = lod0 if CFG.get('colour_from_lod0') else high
(slo, shi), (tlo, thi) = bounds([src]), bounds([target])
k = (thi - tlo).length / (shi - slo).length
for v in src.data.vertices:
    v.co = (v.co - (slo + shi) / 2) * k + (tlo + thi) / 2
print('FINISH fit scale', round(k, 4), 'source dims', [round(d, 3) for d in src.dimensions],
      'target dims', [round(d, 3) for d in target.dimensions])

smat = src.data.materials[0]; snt = smat.node_tree
s_bsdf = next(n for n in snt.nodes if n.type == 'BSDF_PRINCIPLED')


def surface_texels():
    """LOD0's own surface per texel (UV triangles rasterised here): position, face normal, and the interpolated
    smooth normal, tangent and bitangent (MikkTSpace, as the engine's normal mapping uses), plus the covered mask."""
    me = lod0.data; me.calc_loop_triangles(); me.calc_tangents()
    co = np.array([v.co[:] for v in me.vertices]); uvs = np.array([l.uv[:] for l in me.uv_layers.active.data])
    ln = np.array([l.normal[:] for l in me.loops]); lt = np.array([l.tangent[:] for l in me.loops])
    lb = np.array([l.bitangent[:] for l in me.loops])
    out = {k: np.zeros((RES, RES, 3)) for k in ('pos', 'face', 'n', 't', 'b')}
    covered = np.zeros((RES, RES), bool)
    for t in me.loop_triangles:
        loops = list(t.loops)
        p = uvs[loops] * RES - 0.5
        x0, y0 = np.floor(p.min(0)).astype(int); x1, y1 = np.ceil(p.max(0)).astype(int)
        x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, RES - 1), min(y1, RES - 1)
        den = (p[1, 1] - p[2, 1]) * (p[0, 0] - p[2, 0]) + (p[2, 0] - p[1, 0]) * (p[0, 1] - p[2, 1])
        if abs(den) < 1e-12 or x1 < x0 or y1 < y0:
            continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        w0 = ((p[1, 1] - p[2, 1]) * (xs - p[2, 0]) + (p[2, 0] - p[1, 0]) * (ys - p[2, 1])) / den
        w1 = ((p[2, 1] - p[0, 1]) * (xs - p[2, 0]) + (p[0, 0] - p[2, 0]) * (ys - p[2, 1])) / den
        w = np.stack([w0, w1, 1 - w0 - w1], -1)
        inside = (w >= -0.02).all(-1)
        yi, xi = ys[inside], xs[inside]; wi = w[inside]
        out['pos'][yi, xi] = wi @ co[list(t.vertices)]
        out['face'][yi, xi] = t.normal[:]
        for key, arr in (('n', ln), ('t', lt), ('b', lb)):
            out[key][yi, xi] = wi @ arr[loops]
        covered[yi, xi] = True
    return out, covered


def dilate(rgb, covered, steps=16):
    """Grow covered texels into the gutters (mean of covered 4-neighbours per step), so mip levels and collapsed
    LODs do not pull in black."""
    rgb = rgb.copy(); done = covered.copy()
    for _ in range(steps):
        acc = np.zeros_like(rgb); cnt = np.zeros(done.shape, np.float32)
        for axis, shift in ((0, 1), (0, -1), (1, 1), (1, -1)):
            m = np.roll(done, shift, axis); acc += np.roll(rgb * done[..., None], shift, axis); cnt += m
        grow = ~done & (cnt > 0)
        rgb[grow] = acc[grow] / cnt[grow][:, None]; done |= grow
    return rgb


def nearest_hits(source, surf, covered):
    """For each covered LOD0 texel, the point of the source surface it shows: the nearest point, or, where that faces
    away (inner wall, far side of a thin fold), the outermost surface along the texel's face normal as a cage bake
    would. Ray-cast baking alone picked up pleats and the bag mouth where decimation moved LOD0 off the surface.
    Returns the source loop triangles (vertex and loop indices) and barycentric weights per texel."""
    sme = source.data; sme.calc_loop_triangles()
    tri_v = np.array([t.vertices[:] for t in sme.loop_triangles]); tri_l = np.array([t.loops[:] for t in sme.loop_triangles])
    sv = np.array([v.co[:] for v in sme.vertices])
    bvh = BVHTree.FromPolygons([tuple(v) for v in sv], [tuple(t) for t in tri_v])
    rows, cols = np.nonzero(covered)
    loc = np.zeros((len(rows), 3)); tri = np.zeros(len(rows), int)
    reach = 0.06 * CFG['width']; fixed = 0
    for k, (r, c) in enumerate(zip(rows, cols)):
        p = Vector(surf['pos'][r, c]); n = Vector(surf['face'][r, c])
        hit = bvh.find_nearest(p)
        if hit[1].dot(n) < 0.2:
            ray = bvh.ray_cast(p + n * reach, -n, 2 * reach)
            if ray[0] is not None and ray[1].dot(n) > 0:
                hit = ray; fixed += 1
        loc[k] = hit[0]; tri[k] = hit[2]
    print('FINISH nearest', source.name, len(rows), 'texels,', fixed, 'from the outer ray')
    a, b, c = sv[tri_v[tri, 0]], sv[tri_v[tri, 1]], sv[tri_v[tri, 2]]
    v0, v1, v2 = b - a, c - a, loc - a
    d00 = (v0 * v0).sum(1); d01 = (v0 * v1).sum(1); d11 = (v1 * v1).sum(1); d20 = (v2 * v0).sum(1); d21 = (v2 * v1).sum(1)
    den = np.where(np.abs(d00 * d11 - d01 * d01) < 1e-20, 1e-20, d00 * d11 - d01 * d01)
    wb = (d11 * d20 - d01 * d21) / den; wc = (d00 * d21 - d01 * d20) / den
    return rows, cols, tri_l[tri], np.stack([1 - wb - wc, wb, wc], 1)


def sample_images(source, hits, images, covered):
    """Source textures sampled bilinearly at each hit's UV, dilated into the gutters."""
    rows, cols, loops, w = hits
    suv = np.array([l.uv[:] for l in source.data.uv_layers.active.data])
    uv = (w[:, :, None] * suv[loops]).sum(1)
    results = []
    for img in images:
        iw, ih = img.size
        px = np.empty(iw * ih * 4, np.float32); img.pixels.foreach_get(px); px = px.reshape(ih, iw, 4)[..., :3]
        x = (uv[:, 0] % 1.0) * iw - 0.5; y = (uv[:, 1] % 1.0) * ih - 0.5
        x0 = np.floor(x).astype(int); y0 = np.floor(y).astype(int); fx = (x - x0)[:, None]; fy = (y - y0)[:, None]
        x0 %= iw; y0 %= ih; x1 = (x0 + 1) % iw; y1 = (y0 + 1) % ih
        val = (px[y0, x0] * (1 - fx) * (1 - fy) + px[y0, x1] * fx * (1 - fy) + px[y1, x0] * (1 - fx) * fy
               + px[y1, x1] * fx * fy)
        out = np.zeros((RES, RES, 3), np.float32); out[rows, cols] = val
        results.append(dilate(out, covered))
    return results


def tangent_normals(source, hits, surf, covered):
    """The source's smooth surface normal at each hit, in LOD0's tangent space, encoded 0..1 (glTF normal map)."""
    rows, cols, loops, w = hits
    source.data.calc_loop_triangles()
    sn = np.array([l.normal[:] for l in source.data.loops])
    n_hi = (w[:, :, None] * sn[loops]).sum(1)
    n_hi /= np.maximum(np.linalg.norm(n_hi, axis=1), 1e-9)[:, None]
    t, b, n = surf['t'][rows, cols], surf['b'][rows, cols], surf['n'][rows, cols]
    n_hi *= np.where((n_hi * n).sum(1) < 0, -1.0, 1.0)[:, None]     # the leather shell's winding is not reliable
    ts = np.stack([(n_hi * t).sum(1), (n_hi * b).sum(1), (n_hi * n).sum(1)], 1)
    ts[:, 2] = np.maximum(ts[:, 2], 0.05)
    ts /= np.linalg.norm(ts, axis=1)[:, None]
    out = np.zeros((RES, RES, 3), np.float32); out[..., 2] = 1.0; out[rows, cols] = ts
    return dilate(out * 0.5 + 0.5, covered)


s_imgs = {}
for key in ('Base Color', 'Roughness'):
    link = s_bsdf.inputs[key].links[0] if s_bsdf.inputs[key].links else None
    node = link.from_node if link else None
    while node is not None and node.type != 'TEX_IMAGE':
        node = node.inputs[0].links[0].from_node if node.inputs and node.inputs[0].links else None
    s_imgs[key] = node.image
s_imgs['Base Color'].colorspace_settings.name = 'Non-Color'    # read the stored sRGB values, no conversion
surf, covered = surface_texels()
hits = nearest_hits(src, surf, covered)
base, rough_rgb = sample_images(src, hits, [s_imgs['Base Color'], s_imgs['Roughness']], covered)
# Tier 1's colour source is an early low-poly mesh; its surface normal comes from High.
normal_source = high if CFG.get('colour_from_lod0') else src
normal_hits = nearest_hits(normal_source, surf, covered) if normal_source is high else hits
normal = tangent_normals(normal_source, normal_hits, surf, covered)
if CFG.get('base_projection'):
    # project_views.py input: the High surface point and normal each LOD0 texel shows (same hits as the normal map)
    rows, cols, loops, w = normal_hits
    hme = high.data
    hv = np.array([v.co[:] for v in hme.vertices]); hn = np.array([l.normal[:] for l in hme.loops])
    lv = np.array([l.vertex_index for l in hme.loops])
    pos = np.zeros((RES, RES, 3)); nrm = np.zeros((RES, RES, 3))
    pos[rows, cols] = (w[:, :, None] * hv[lv[loops]]).sum(1)
    n_hi = (w[:, :, None] * hn[loops]).sum(1)
    n_hi *= np.where((n_hi * surf['face'][rows, cols]).sum(1) < 0, -1.0, 1.0)[:, None]
    nrm[rows, cols] = n_hi / np.maximum(np.linalg.norm(n_hi, axis=1), 1e-9)[:, None]
    tris = np.array([t.vertices[:] for t in hme.loop_triangles])
    np.savez_compressed(os.path.join(WORK, f't{N}_surface.npz'), pos=pos, nrm=nrm, valid=covered, verts=hv, tris=tris)
rough = rough_rgb[..., 1:2]                                  # glTF metallic-roughness: G


def save(name, rgb, size, colorspace):
    img = bpy.data.images.new(name, RES, RES, alpha=False); img.colorspace_settings.name = colorspace
    rgba = np.concatenate([np.clip(rgb, 0, 1), np.ones((RES, RES, 1), np.float32)], 2)
    img.pixels.foreach_set(rgba.ravel())
    if size != RES:
        img.scale(size, size)
    img.filepath_raw = os.path.join(TEX, name + '.png'); img.file_format = 'PNG'; img.save()
    return img


save(f'satchel_t{N}_basecolor_meshy', base, RES, 'sRGB')
projected = os.path.join(TEX, f'satchel_t{N}_projected.png')
if CFG.get('base_projection') and os.path.exists(projected):
    # project_views.py output (the Codex views projected onto this LOD0's atlas, Meshy colour where unseen)
    p_img = bpy.data.images.load(projected)
    a = np.empty(RES * RES * 4, np.float32); p_img.pixels.foreach_get(a)
    base = a.reshape(RES, RES, 4)[..., :3]
    print('FINISH base colour from', os.path.basename(projected))
base_png = save(f'satchel_t{N}_basecolor', base, RES, 'sRGB')
normal_png = save(f'satchel_t{N}_normal', normal, 512, 'Non-Color')
r = np.clip(rough, 0.35, 1.0)
mr_png = save(f'satchel_t{N}_metal_rough', np.concatenate([np.ones_like(r), r, np.zeros_like(r)], 2), 512,
              'Non-Color')
for img in (base_png, normal_png, mr_png):
    img.reload()

mat = bpy.data.materials.new(f'LootSatchelT{N}'); mat.use_nodes = True
nt = mat.node_tree; pb = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')


def tex(img):
    n = nt.nodes.new('ShaderNodeTexImage'); n.image = img; return n


nt.links.new(tex(base_png).outputs['Color'], pb.inputs['Base Color'])
nm = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(tex(normal_png).outputs['Color'], nm.inputs['Color'])
nt.links.new(nm.outputs['Normal'], pb.inputs['Normal'])
sp = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(tex(mr_png).outputs['Color'], sp.inputs['Color'])
nt.links.new(sp.outputs['Green'], pb.inputs['Roughness'])
pb.inputs['Metallic'].default_value = 0.0
lod0.data.materials.clear(); lod0.data.materials.append(mat)
if CFG.get('gem_emissive'):
    # Rubies glow faintly: their faces (base colour at the face's UV centre is a saturated red) take a copy of the
    # material with a small emissive factor, which the renderer adds after lighting. The sapphires are left alone:
    # their blue cannot be told apart from the royal-blue velvet by colour.
    gem = mat.copy(); gem.name = f'LootSatchelT{N}_Gems'
    gb = next(n for n in gem.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    gb.inputs['Emission Color'].default_value = (*CFG['gem_emissive'], 1.0); gb.inputs['Emission Strength'].default_value = 1.0
    lod0.data.materials.append(gem)
    uvl = lod0.data.uv_layers.active.data
    count = 0
    for poly in lod0.data.polygons:
        u = sum(uvl[i].uv[0] for i in poly.loop_indices) / poly.loop_total
        v = sum(uvl[i].uv[1] for i in poly.loop_indices) / poly.loop_total
        r, g, b = base[min(RES - 1, int(v * RES)), min(RES - 1, int(u * RES))]
        if r > 0.45 and g < 0.22 and b < 0.3 and r > 2.2 * g:
            poly.material_index = 1; count += 1
    print('FINISH ruby faces', count)
for o in (src, high):
    bpy.data.objects.remove(o, do_unlink=True)


def islands(mesh):
    """Face index lists of the connected pieces, with each piece's bounding-box diagonal."""
    bm = bmesh.new(); bm.from_mesh(mesh); bm.faces.ensure_lookup_table()
    seen = set(); out = []
    for f in bm.faces:
        if f.index in seen:
            continue
        stack = [f]; seen.add(f.index); faces = []
        while stack:
            g = stack.pop(); faces.append(g)
            for e in g.edges:
                for h in e.link_faces:
                    if h.index not in seen:
                        seen.add(h.index); stack.append(h)
        co = [v.co for g in faces for v in g.verts]
        diag = (Vector(map(max, *co)) - Vector(map(min, *co))).length
        out.append(([g.index for g in faces], diag))
    bm.free(); return out


def cap_holes(o):
    """Close open boundaries (the culled underside, the bag mouth): collapse stalls on open edges, so coarse levels
    could not reach their budget. Cap loops take the UVs their vertices have in the neighbouring faces (a smear of the
    rim, only seen far away)."""
    bm = bmesh.new(); bm.from_mesh(o.data)
    uv = bm.loops.layers.uv.active
    rim = {}
    for f in bm.faces:
        for loop in f.loops:
            rim.setdefault(loop.vert.index, loop[uv].uv.copy())
    new = bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary], sides=0)['faces']
    for f in new:
        for loop in f.loops:
            loop[uv].uv = rim.get(loop.vert.index, loop[uv].uv)
    bmesh.ops.triangulate(bm, faces=new)
    bm.to_mesh(o.data); bm.free()


def drop_small_islands(o, min_fraction):
    """Delete pieces whose bounding-box diagonal is below min_fraction of the largest piece's (cord ends, single
    coins): collapse cannot take a piece below a few triangles, so coarse levels would stall on them."""
    pieces = islands(o.data)
    total = max(d for _, d in pieces)
    drop = {i for faces, d in pieces if d < min_fraction * total for i in faces}
    bm = bmesh.new(); bm.from_mesh(o.data); bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[bm.faces[i] for i in drop], context='FACES'); bm.to_mesh(o.data); bm.free()


lods = [lod0]
tris0 = len(lod0.data.polygons)
for i, ratio in enumerate(LOD_RATIOS, 1):
    target = int(tris0 * ratio)
    for cap, min_fraction in ((False, 0.0), (True, 0.0), (True, 0.15), (True, 0.3), (True, 0.5)):
        o = lods[-1].copy(); o.data = lods[-1].data.copy()
        o.name = f'LootSatchelT{N}_LOD{i}'
        scene.collection.objects.link(o)
        if min_fraction:
            drop_small_islands(o, min_fraction)
        if cap:
            cap_holes(o)
        mod = o.modifiers.new('dec', 'DECIMATE'); mod.decimate_type = 'COLLAPSE'
        mod.ratio = min(1.0, target / len(o.data.polygons)); mod.use_collapse_triangulate = True
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.select_all(action='DESELECT'); o.select_set(True)
        bpy.ops.object.modifier_apply(modifier=mod.name)
        if len(o.data.polygons) <= target * 1.2 or min_fraction == 0.5:
            break                                # the last attempt stays even above target (counts still fall)
        bpy.data.objects.remove(o, do_unlink=True)
    if len(o.data.polygons) > target * 1.2:
        # Collapse still stalls (overlapping folds): use LOD0's convex hull, collapsed to the budget, with LOD0's
        # UVs transferred onto it (the mouth fills in; this level is only seen far away).
        prev = lods[0]
        bm = bmesh.new(); bm.from_mesh(prev.data)
        hull = bmesh.ops.convex_hull(bm, input=bm.verts)
        bmesh.ops.delete(bm, geom=[g for g in hull['geom_interior'] + hull['geom_unused'] if isinstance(g, bmesh.types.BMVert)], context='VERTS')
        bmesh.ops.delete(bm, geom=list({f for f in bm.faces} - set(g for g in hull['geom'] if isinstance(g, bmesh.types.BMFace))), context='FACES')
        bm.to_mesh(o.data); bm.free()
        bpy.context.view_layer.objects.active = o
        if len(o.data.polygons) > target * 1.2:
            mod = o.modifiers.new('dec', 'DECIMATE'); mod.decimate_type = 'COLLAPSE'
            mod.ratio = min(1.0, target / len(o.data.polygons)); mod.use_collapse_triangulate = True
            bpy.ops.object.modifier_apply(modifier=mod.name)
        dt = o.modifiers.new('uv', 'DATA_TRANSFER'); dt.object = prev
        dt.use_loop_data = True; dt.data_types_loops = {'UV'}; dt.loop_mapping = 'POLYINTERP_NEAREST'
        bpy.ops.object.modifier_apply(modifier=dt.name)
        bpy.ops.object.shade_smooth()
        min_fraction = 'hull'
    print('LOD', i, 'target', target, 'tris', len(o.data.polygons), 'dropped islands below', min_fraction)
    lods.append(o)
counts = [len(o.data.polygons) for o in lods]
assert all(a > b for a, b in zip(counts, counts[1:])), counts
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, f't{N}_lods.blend'))
bpy.ops.object.select_all(action='DESELECT')
for o in lods:
    o.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(WORK, f't{N}_export.glb'), use_selection=True, export_format='GLB',
                          export_yup=True, export_animations=False, export_skins=False, export_morph=False,
                          export_image_format='AUTO', export_extras=False, export_attributes=False)
print('FINISH', N, 'tris', counts)
