"""Texture one v2 tier onto the shared sack. Usage: blender --background --python v2/scripts/finish.py -- <tier>
Opens work/shared.blend (LOD0 with packed UVs plus the full-detail High, 1 m plan width) and imports the tier's Meshy
retexture of High (meshy/retex_t<N>/model_urls_glb.glb), fitted onto High by its bounds (Meshy normalises the returned
model). Each LOD0 texel takes the High surface point it shows (nearest_hits, as v1 finish_tier.py): base colour and
roughness sampled from the Meshy maps, and High's normal in LOD0 tangent space. Writes work/textures/satchel_t<N>_*
(base colour 1024; normal and metal-roughness 512, R 1, G roughness, B 0), scales LOD0 to the tier's width (plan
centre on the origin, base on the ground), gives tiers with gem_emissive a second material on the clasp faces
(tiers.CLASP: faces whose centre lies within the clasp sphere of the 1 m mesh) and exports work/t<N>_export.glb
(one mesh node, no LODs)."""
import bpy, sys, os
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tiers import TIERS, ROOT, CLASP

N = int(sys.argv[sys.argv.index('--') + 1])
CFG = TIERS[N]
WORK = os.path.join(ROOT, 'work'); TEX = os.path.join(WORK, 'textures'); os.makedirs(TEX, exist_ok=True)
RES = 1024

bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, 'shared.blend'))
scene = bpy.context.scene
lod0 = bpy.data.objects['LootSatchel']
high = bpy.data.objects['LootSatchel_High']
lod0.name = f'LootSatchelT{N}'


def bounds(objs):
    co = [o.matrix_world @ v.co for o in objs for v in o.data.vertices]
    return Vector(map(min, *co)), Vector(map(max, *co))


before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT, 'meshy', f'retex_t{N}', 'model_urls_glb.glb'))
src = [o for o in bpy.data.objects if o not in before and o.type == 'MESH']
bpy.ops.object.select_all(action='DESELECT')
for o in src:
    o.select_set(True)
bpy.context.view_layer.objects.active = src[0]
bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
if len(src) > 1:
    bpy.ops.object.join()
src = bpy.context.view_layer.objects.active
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
(slo, shi), (tlo, thi) = bounds([src]), bounds([high])
k = (thi - tlo).length / (shi - slo).length
for v in src.data.vertices:
    v.co = (v.co - (slo + shi) / 2) * k + (tlo + thi) / 2
print('FINISH fit scale', round(k, 4), 'source dims', [round(d, 3) for d in src.dimensions],
      'target dims', [round(d, 3) for d in high.dimensions])

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
    reach = 0.06; fixed = 0
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
normal = tangent_normals(src, hits, surf, covered)
rough = rough_rgb[..., 1:2]                                  # glTF metallic-roughness: G


def save(name, rgb, size, colorspace):
    img = bpy.data.images.new(name, RES, RES, alpha=False); img.colorspace_settings.name = colorspace
    rgba = np.concatenate([np.clip(rgb, 0, 1), np.ones((RES, RES, 1), np.float32)], 2)
    img.pixels.foreach_set(rgba.ravel())
    if size != RES:
        img.scale(size, size)
    img.filepath_raw = os.path.join(TEX, name + '.png'); img.file_format = 'PNG'; img.save()
    return img


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
    # The clasp gem glows: the clasp faces of the shared mesh take a copy of the material with an emissive factor,
    # which the renderer adds after lighting.
    gem = mat.copy(); gem.name = f'LootSatchelT{N}_Gem'
    gb = next(n for n in gem.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    gb.inputs['Emission Color'].default_value = (*CFG['gem_emissive'], 1.0)
    gb.inputs['Emission Strength'].default_value = 1.0
    lod0.data.materials.append(gem)
    centre = Vector(CLASP['centre'])
    polys = lod0.data.polygons
    by_vertex = {}
    for poly in polys:
        for v in poly.vertices:
            by_vertex.setdefault(v, []).append(poly.index)
    stack = [min(polys, key=lambda poly: (poly.center - centre).length).index]; island = set(stack)
    while stack:
        for v in polys[stack.pop()].vertices:
            for other in by_vertex[v]:
                if other not in island:
                    island.add(other); stack.append(other)
    for index in island:
        polys[index].material_index = 1
    print('FINISH clasp gem faces', len(island))
for o in (src, high):
    bpy.data.objects.remove(o, do_unlink=True)
# Final width: the shared mesh is 1 m wide with its plan centre on the origin and its base at z = 0.
s = CFG['width']
for v in lod0.data.vertices:
    v.co = v.co * s
bpy.ops.object.select_all(action='DESELECT'); lod0.select_set(True); bpy.context.view_layer.objects.active = lod0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, f't{N}.blend'))
bpy.ops.export_scene.gltf(filepath=os.path.join(WORK, f't{N}_export.glb'), use_selection=True, export_format='GLB',
                          export_yup=True, export_animations=False, export_skins=False, export_morph=False,
                          export_image_format='AUTO', export_extras=False, export_attributes=False)
print('FINISH', N, 'tris', len(lod0.data.polygons), 'dims', [round(d, 3) for d in lod0.dimensions])
