"""Helpers of the figure statues (7dec54, 7dec55, dec94, dec95): rigged MM6 creatures (assets_source, read only)
posed with world-space bone operations (../../../mm6_dungeons_3d/leftovers/scripts/corpse_pose.py, read only) and
baked static, a stone surface baked into a unique texture on the creature's own atlas, procedural trim parts
(swept rings, horns, blades), and LOD helpers. Blender metres in the creature's own scale (the binding height scales
the model); the statue faces -y (toward the sprite camera)."""
import json
import math
import os
import struct
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dlib  # noqa: E402

sys.path.insert(0, os.path.join(dlib.DECO, 'mm6_dungeons_3d', 'leftovers', 'scripts'))
import corpse_pose as cp  # noqa: E402

pl, hl = dlib.pl, dlib.hl
STONE_SRC = os.path.join(dlib.TEXTURES, 'source')
SRC = os.path.join(dlib.WORK, 'statue_src')


# ---------------------------------------------------------------- creature import and pose
def level_glb(path, mesh_index):
    """A copy of a creature GLB whose skinned node shows its own LOD mesh `mesh_index` (0..3)."""
    raw = open(path, 'rb').read()
    size = struct.unpack_from('<I', raw, 12)[0]
    document = json.loads(raw[20:20 + size]); binary = raw[20 + size:]
    node = next((n for n in document['nodes'] if 'mesh' in n and 'skin' in n), None) or \
        next(n for n in document['nodes'] if 'mesh' in n)
    node['mesh'] = mesh_index
    encoded = json.dumps(document, separators=(',', ':')).encode()
    encoded += b' ' * (-len(encoded) % 4)
    os.makedirs(SRC, exist_ok=True)
    out = os.path.join(SRC, f'{os.path.splitext(os.path.basename(path))[0]}_lod{mesh_index}.glb')
    with open(out, 'wb') as f:
        f.write(struct.pack('<III', 0x46546c67, 2, 20 + len(encoded) + len(binary))
                + struct.pack('<II', len(encoded), 0x4e4f534a) + encoded + binary)
    return out


def load(path, mesh_index=0):
    """Import the creature at LOD mesh_index: (armature, body). Other meshes (stray markers) are removed, clips
    dropped, the rest pose restored."""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=level_glb(path, mesh_index))
    new = [o for o in bpy.data.objects if o not in before]
    arm = next(o for o in new if o.type == 'ARMATURE')
    meshes = [o for o in new if o.type == 'MESH']
    body = max(meshes, key=lambda o: len(o.data.polygons))
    for o in new:
        if o not in (arm, body):
            bpy.data.objects.remove(o)
    arm.animation_data_clear()
    for pb in arm.pose.bones:
        pb.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()
    return arm, body


def joints(arm):
    return {pb.name: (arm.matrix_world @ pb.head, arm.matrix_world @ pb.tail, arm.matrix_world @ pb.matrix)
            for pb in arm.pose.bones}


def posed(path, mesh_index, ops, name, place=None):
    """Load, place (world 4x4), pose and bake one level: (static object, joints)."""
    for o in list(bpy.data.objects):
        if o.type == 'ARMATURE' or (o.parent and o.parent.type == 'ARMATURE'):
            bpy.data.objects.remove(o)
    arm, body = load(path, mesh_index)
    if place is not None:
        arm.matrix_world = place
        bpy.context.view_layer.update()
    cp.pose(arm, ops)
    j = joints(arm)
    static = cp.bake(arm, body, name)
    for o in (arm, body):
        bpy.data.objects.remove(o)
    if 'rest' in static.data.attributes:
        static.data.attributes.remove(static.data.attributes['rest'])
    for key in ('custom_normal',):
        if key in static.data.attributes:
            static.data.attributes.remove(static.data.attributes[key])
    return static, j


def strongest(obj):
    return np.array(cp.strongest_bone(obj))


def delete_verts(obj, mask):
    bm = bmesh.new(); bm.from_mesh(obj.data); bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[bm.verts[i] for i in np.nonzero(mask)[0]], context='VERTS')
    bm.to_mesh(obj.data); bm.free()


def coords(obj):
    co = np.empty(len(obj.data.vertices) * 3); obj.data.vertices.foreach_get('co', co)
    return co.reshape(-1, 3)


def set_coords(obj, co):
    obj.data.vertices.foreach_set('co', np.asarray(co, float).ravel()); obj.data.update()


# ---------------------------------------------------------------- mesh helpers
def single_material(obj, mat):
    obj.data.materials.clear(); obj.data.materials.append(mat)
    for p in obj.data.polygons:
        p.material_index = 0


def duplicate(obj, name):
    copy = obj.copy(); copy.data = obj.data.copy(); copy.name = name; copy.data.name = name
    bpy.context.scene.collection.objects.link(copy)
    return copy


def decimate(obj, target):
    """Collapse to the target, keeping UV seams (the atlas texture stays put)."""
    if pl.triangles(obj) <= target:
        return pl.triangles(obj)
    return pl.decimate_to(obj, target)


def smooth(obj, angle=60):
    for p in obj.data.polygons:
        p.use_smooth = True
    try:
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True)
        bpy.ops.object.shade_auto_smooth(angle=math.radians(angle))
        bpy.ops.object.modifier_apply(modifier=obj.modifiers[-1].name) if obj.modifiers else None
    except Exception as error:      # noqa: BLE001 - auto smooth is cosmetic
        print('SMOOTH skipped', error)


def ring_around(name, centre, axis, radius, width, thick, segments, mat):
    """A flat band (rectangular section) around an axis: a hoop on a limb or a helmet rim. Sizes in metres."""
    axis = Vector(axis).normalized()
    side = axis.orthogonal().normalized(); other = axis.cross(side)
    bm = bmesh.new(); uv = bm.loops.layers.uv.verify()
    profile = [(radius - thick * 0.3, -width / 2), (radius + thick, -width / 2), (radius + thick * 1.15, 0),
               (radius + thick, width / 2), (radius - thick * 0.3, width / 2)]
    rings = []
    for r, h in profile:
        ring = []
        for s in range(segments):
            a = 2 * math.pi * s / segments
            ring.append(bm.verts.new(Vector(centre) + axis * h + (side * math.cos(a) + other * math.sin(a)) * r))
        rings.append(ring)
    for i in range(len(rings) - 1):
        for s in range(segments):
            s2 = (s + 1) % segments
            f = bm.faces.new((rings[i][s], rings[i][s2], rings[i + 1][s2], rings[i + 1][s]))
            for loop, (a, b) in zip(f.loops, ((s, i), (s + 1, i), (s + 1, i + 1), (s, i + 1))):
                loop[uv].uv = (a / segments * 4, b / 4)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return pl.to_object(name, bm, mat, True)


def sweep_m(name, points, radii, sides, mat, closed=False, caps=True, flat=1.0, up=None, phase=0.0):
    """hl.sweep with points and radii in metres."""
    k = dlib.UNITS_PER_METRE
    radii = [r * k for r in radii] if isinstance(radii, (list, tuple)) else radii * k
    return hl.sweep(name, [Vector(p) * k for p in points], radii, sides, mat, closed=closed, caps=caps, flat=flat,
                    up=up, phase=phase)


def limb_radius(obj, bones, centre, axis, band=0.02):
    """Median distance from the axis of the vertices of the given bones within +-band of centre along the axis."""
    co = coords(obj); names = strongest(obj)
    mask = np.isin(names, bones)
    axis = np.array(axis, float); axis /= np.linalg.norm(axis)
    d = co[mask] - np.array(centre)
    along = d @ axis
    near = np.abs(along) < band
    if not near.any():
        return 0.05
    radial = np.linalg.norm(d[near] - along[near, None] * axis, axis=1)
    return float(np.percentile(radial, 80))


# ---------------------------------------------------------------- stone texture bake
def stone_bake(obj, out_png, size, stone='rock_01', scale=7.0, samples=64):
    """Bake into out_png (.npy, the object's UVs, rows bottom to top): R = box-projected stone luminance (object
    space, `scale` repeats per metre), G = ambient occlusion, B = world normal z remapped to 0..1, A = 1 where baked
    (0 elsewhere). The colour itself is composed in numpy (statue_compose.py)."""
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = samples
    scene.cycles.device = 'CPU'
    mat = bpy.data.materials.new('StoneBake'); mat.use_nodes = True
    nt = mat.node_tree; nodes = nt.nodes
    for n in list(nodes):
        nodes.remove(n)
    out = nodes.new('ShaderNodeOutputMaterial')
    emission = nodes.new('ShaderNodeEmission')
    coord = nodes.new('ShaderNodeTexCoord'); mapping = nodes.new('ShaderNodeMapping')
    mapping.inputs['Scale'].default_value = (scale, scale, scale)
    tex = nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(os.path.join(STONE_SRC, stone, f'{stone}_diff_1k.png'))
    tex.projection = 'BOX'; tex.projection_blend = 0.3
    nt.links.new(coord.outputs['Object'], mapping.inputs['Vector']); nt.links.new(mapping.outputs['Vector'],
                                                                                   tex.inputs['Vector'])
    ao = nodes.new('ShaderNodeAmbientOcclusion'); ao.samples = 16; ao.inputs['Distance'].default_value = 0.08
    lum = nodes.new('ShaderNodeRGBToBW'); nt.links.new(tex.outputs['Color'], lum.inputs['Color'])
    combine = nodes.new('ShaderNodeCombineColor')
    nt.links.new(lum.outputs['Val'], combine.inputs['Red']); nt.links.new(ao.outputs['AO'], combine.inputs['Green'])
    geometry = nodes.new('ShaderNodeNewGeometry'); split = nodes.new('ShaderNodeSeparateXYZ')
    remap = nodes.new('ShaderNodeMath'); remap.operation = 'MULTIPLY_ADD'
    remap.inputs[1].default_value = 0.5; remap.inputs[2].default_value = 0.5
    nt.links.new(geometry.outputs['Normal'], split.inputs['Vector']); nt.links.new(split.outputs['Z'], remap.inputs[0])
    nt.links.new(remap.outputs['Value'], combine.inputs['Blue'])
    nt.links.new(combine.outputs['Color'], emission.inputs['Color'])
    nt.links.new(emission.outputs['Emission'], out.inputs['Surface'])
    target = nodes.new('ShaderNodeTexImage')
    img = bpy.data.images.new('stonebake', size[0], size[1], float_buffer=True)
    img.colorspace_settings.name = 'Non-Color'
    img.pixels.foreach_set(np.zeros(size[0] * size[1] * 4, np.float32))
    target.image = img; nodes.active = target
    saved = list(obj.data.materials)
    obj.data.materials.clear(); obj.data.materials.append(mat)
    for p in obj.data.polygons:
        p.material_index = 0
    bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True); bpy.context.view_layer.objects.active = obj
    scene.render.bake.margin = 8
    bpy.ops.object.bake(type='EMIT')
    px = np.array(img.pixels[:], np.float32).reshape(size[1], size[0], 4)
    np.save(out_png, px)
    obj.data.materials.clear()
    for m in saved:
        obj.data.materials.append(m)
    print('BAKED', out_png, px[..., 0].mean(), px[..., 1].mean())
    return px


def srgb_to_linear(c):
    c = np.asarray(c, float)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(c):
    c = np.clip(np.asarray(c, float), 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def save_png(path, rgb, size=None):
    from PIL import Image
    img = Image.fromarray((np.clip(rgb, 0, 1) * 255 + 0.5).astype(np.uint8))
    if size:
        img = img.resize(size, Image.LANCZOS)
    img.save(path)
    print('WROTE', path, img.size)


def sprite_ramp(names, exclude_gold=True):
    """The native sprites' opaque pixels sorted by luminance: (luminance 0..1 sorted, sRGB colours 0..1)."""
    from PIL import Image
    pix = []
    for n in names:
        im = np.asarray(Image.open(os.path.join(dlib.X2, n)).convert('RGBA')).astype(float) / 255
        p = im[im[..., 3] > 0.5][:, :3]
        if exclude_gold:
            mx, mn = p.max(1), p.min(1)
            sat = (mx - mn) / np.maximum(mx, 1e-3)
            p = p[~((sat > 0.35) & (p[:, 0] > p[:, 1]) & (p[:, 1] > p[:, 2]) & (mx > 0.24))]
        pix.append(p)
    p = np.concatenate(pix)
    lum = p @ np.array([0.2126, 0.7152, 0.0722])
    order = np.argsort(lum)
    return lum[order], p[order]


def ramp_lookup(rank, ramp_colours):
    """Colour at rank 0..1 in a luminance-sorted ramp (median of a small window)."""
    n = len(ramp_colours)
    idx = np.clip((rank * (n - 1)).astype(int), 0, n - 1)
    # smooth the ramp: mean over windows of 1 % of the ramp
    k = max(1, n // 100)
    cs = np.cumsum(np.vstack([np.zeros(3), ramp_colours]), axis=0)
    lo = np.clip(idx - k, 0, n); hi = np.clip(idx + k, 0, n)
    return (cs[hi] - cs[lo]) / np.maximum(hi - lo, 1)[:, None]


def rank_of(values, weights=None):
    """Area-weighted rank 0..1 of each value."""
    flat = values.ravel()
    order = np.argsort(flat)
    w = np.ones_like(flat) if weights is None else weights.ravel()
    cum = np.cumsum(w[order]); cum /= cum[-1]
    rank = np.empty_like(flat); rank[order] = cum
    return rank.reshape(values.shape)


def tint_groups(obj, groups, keep=None):
    """COLOR_0 = softened occlusion x a per-group linear factor, so each group's albedo mean (texture reference mean x
    COLOR_0) equals its sprite target. groups: {material name: (target sRGB 0..255, reference sRGB mean of the
    texture texels that show, or None for the whole texture's mean)}; keep: {material name: fraction of the
    occlusion kept (default 1)}."""
    me = obj.data
    colour = me.color_attributes['Color']
    occ = np.empty(len(me.vertices) * 4, np.float32); colour.data.foreach_get('color', occ); occ = occ.reshape(-1, 4)
    slot = np.zeros(len(me.vertices), int)
    for polygon in me.polygons:
        for index in polygon.vertices:
            slot[index] = polygon.material_index
    for index, mat in enumerate(me.materials):
        mask = slot == index
        if not mask.any() or mat.name not in groups:
            continue
        target, reference = groups[mat.name]
        if reference is None:
            reference = hl.texture_mean(mat)
        k = (keep or {}).get(mat.name, 1.0)
        occ[mask, :3] = 1.0 - (1.0 - occ[mask, :3]) * k
        factor = srgb_to_linear(np.array(target) / 255) / srgb_to_linear(np.array(reference) / 255) \
            / float(occ[mask, 0].mean())
        occ[mask, :3] *= factor
        print('TINT', obj.name, mat.name, 'target', target, 'reference', np.round(reference).tolist(), 'factor',
              np.round(factor, 3).tolist(), 'clipped', round(float((occ[mask, :3] > 1).mean()), 3))
    colour.data.foreach_set('color', np.clip(occ, 0, 1).ravel())


def _image_array(image):
    w, h = image.size
    px = np.empty(w * h * 4, np.float32); image.pixels.foreach_get(px)
    return px.reshape(h, w, 4)


def far_lod(source, name, target, voxel, mat, smooth_iterations=0, gain=1.12):
    """A far level as one closed shell: voxel remesh of `source` (a finished level with materials and COLOR_0),
    collapse-decimated to `target`, cube-projected texture coordinates on `mat` (a neutral tileable texture), and
    COLOR_0 carrying the colour of the nearest source surface (its base colour texel x its COLOR_0), divided by
    `mat`'s mean so the far level shows the same albedo."""
    from mathutils.bvhtree import BVHTree
    far = duplicate(source, name)
    bpy.ops.object.select_all(action='DESELECT'); far.select_set(True); bpy.context.view_layer.objects.active = far
    # The creature's open surfaces (legs under the tunic) vanish in a voxel remesh; an octree remesh first closes
    # them into one surface, the voxel pass then evens it out.
    mod = far.modifiers.new('Octree', 'REMESH'); mod.mode = 'SMOOTH'; mod.octree_depth = 7; mod.scale = 0.95
    mod.use_remove_disconnected = False
    bpy.ops.object.modifier_apply(modifier=mod.name)
    mod = far.modifiers.new('Remesh', 'REMESH'); mod.mode = 'VOXEL'; mod.voxel_size = voxel
    bpy.ops.object.modifier_apply(modifier=mod.name)
    if smooth_iterations:
        mod = far.modifiers.new('Smooth', 'SMOOTH'); mod.iterations = smooth_iterations; mod.factor = 0.5
        bpy.ops.object.modifier_apply(modifier=mod.name)
    robust_decimate(far, target)
    # texture coordinates: cube projection
    bm = bmesh.new(); bm.from_mesh(far.data)
    uv = bm.loops.layers.uv.verify()
    for f in bm.faces:
        n = f.normal
        axis = max(range(3), key=lambda k: abs(n[k]))
        for loop in f.loops:
            co = loop.vert.co
            a, b = [(1, 2), (0, 2), (0, 1)][axis]
            loop[uv].uv = (co[a] * 3.0, co[b] * 3.0)
    bm.to_mesh(far.data); bm.free()
    far.data.materials.clear(); far.data.materials.append(mat)
    for p in far.data.polygons:
        p.material_index = 0
        p.use_smooth = True
    for attr in [a.name for a in far.data.color_attributes]:
        far.data.color_attributes.remove(far.data.color_attributes[attr])
    # colours from the source
    deps = bpy.context.evaluated_depsgraph_get()
    bvh = BVHTree.FromObject(source, deps)
    sme = source.data
    scol = np.empty(len(sme.vertices) * 4, np.float32)
    sme.color_attributes['Color'].data.foreach_get('color', scol); scol = scol.reshape(-1, 4)
    images = {}
    for index, m in enumerate(sme.materials):
        tex = next((n for n in m.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image and
                    n.image.colorspace_settings.name == 'sRGB'), None)
        images[index] = _image_array(tex.image) if tex else None
    suv = sme.uv_layers[0].data
    tile_mean = srgb_to_linear(np.array(hl.texture_mean(mat)) / 255)
    out = []
    for v in far.data.vertices:
        loc, normal, face, dist = bvh.find_nearest(v.co)
        poly = sme.polygons[face]
        loops = list(poly.loop_indices)
        u = np.mean([suv[i].uv[0] for i in loops]); w = np.mean([suv[i].uv[1] for i in loops])
        img = images.get(poly.material_index)
        if img is None:
            base = np.ones(3) * 0.5
        else:
            h, wd = img.shape[:2]
            base = img[int((w % 1.0) * (h - 1)), int((u % 1.0) * (wd - 1)), :3]
        lin = srgb_to_linear(base) * scol[list(poly.vertices), :3].mean(0)
        c = np.clip(lin / tile_mean * gain, 0, 1)        # gain: nearest texels sit a little in shadow
        out.append((c[0], c[1], c[2], 1.0))
    attr = far.data.color_attributes.new('Color', 'FLOAT_COLOR', 'POINT')
    attr.data.foreach_set('color', np.array(out, np.float32).ravel())
    far.data.color_attributes.active_color = attr
    print('FAR', name, pl.triangles(far))
    return far


def drop_small_pieces(obj, min_diagonal):
    """Delete loose parts whose bounding-box diagonal is below min_diagonal (studs, buttons, knobs) and return the
    count removed."""
    bm = bmesh.new(); bm.from_mesh(obj.data); bm.verts.ensure_lookup_table()
    seen = set(); remove = []
    for v in bm.verts:
        if v.index in seen:
            continue
        stack = [v]; part = []
        seen.add(v.index)
        while stack:
            x = stack.pop(); part.append(x)
            for e in x.link_edges:
                o = e.other_vert(x)
                if o.index not in seen:
                    seen.add(o.index); stack.append(o)
        co = np.array([p.co[:] for p in part])
        if np.linalg.norm(co.max(0) - co.min(0)) < min_diagonal:
            remove += part
    bmesh.ops.delete(bm, geom=remove, context='VERTS')
    bm.to_mesh(obj.data); bm.free()
    return len(remove)


def decimated_lod(source, name, target, min_piece=0.0):
    """A far level as a decimated copy of a finished level (materials, texture coordinates and COLOR_0 kept)."""
    far = duplicate(source, name)
    if min_piece:
        print('DROPPED verts', drop_small_pieces(far, min_piece))
    bpy.ops.object.select_all(action='DESELECT'); far.select_set(True); bpy.context.view_layer.objects.active = far
    mod = far.modifiers.new('Tri', 'TRIANGULATE'); bpy.ops.object.modifier_apply(modifier=mod.name)
    robust_decimate(far, target)
    print('DECIMATED', name, pl.triangles(far))
    return far


def robust_decimate(obj, target, steps=30):
    """Collapse in applied steps (each at most halving) until within the target; a final un-normalised collapse
    (no UV seam delimit) if the steps stall."""
    bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True); bpy.context.view_layer.objects.active = obj
    for _ in range(steps):
        count = pl.triangles(obj)
        if count <= target:
            return count
        mod = obj.modifiers.new('Decimate', 'DECIMATE'); mod.decimate_type = 'COLLAPSE'
        mod.ratio = max(0.5, target / count * 0.98); mod.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier=mod.name)
        if pl.triangles(obj) >= count:
            # stalled on seams: weld by distance and continue
            bm = bmesh.new(); bm.from_mesh(obj.data)
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.002)
            bm.to_mesh(obj.data); bm.free()
    return pl.triangles(obj)


def drop_pieces(obj, predicate):
    """Delete loose parts for which predicate(vertex count, centroid, min, max) is true; returns the count dropped."""
    bm = bmesh.new(); bm.from_mesh(obj.data); bm.verts.ensure_lookup_table()
    seen = set(); remove = []; dropped = 0
    for v in bm.verts:
        if v.index in seen:
            continue
        stack = [v]; part = []
        seen.add(v.index)
        while stack:
            x = stack.pop(); part.append(x)
            for e in x.link_edges:
                o = e.other_vert(x)
                if o.index not in seen:
                    seen.add(o.index); stack.append(o)
        co = np.array([p.co[:] for p in part])
        if predicate(len(part), co.mean(0), co.min(0), co.max(0)):
            remove += part; dropped += 1
    bmesh.ops.delete(bm, geom=remove, context='VERTS')
    bm.to_mesh(obj.data); bm.free()
    return dropped


def decimate_pieces(obj, target, minimum=24):
    """Collapse each loose piece on its own toward its share of the target (at least `minimum` triangles, or its own
    count when smaller), so thin parts (a sword, horns, rings) keep a shape instead of collapsing into shards."""
    bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True); bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.separate(type='LOOSE'); bpy.ops.object.mode_set(mode='OBJECT')
    pieces = [o for o in bpy.context.selected_objects]
    total = sum(pl.triangles(p) for p in pieces)
    ratio = target / max(total, 1)
    for p in pieces:
        n = pl.triangles(p)
        want = max(min(n, minimum), int(n * ratio))
        if want < n:                 # one collapse pass (chained passes erode thin parts into shards)
            bpy.ops.object.select_all(action='DESELECT'); p.select_set(True); bpy.context.view_layer.objects.active = p
            m = p.modifiers.new('Decimate', 'DECIMATE'); m.ratio = want / n; m.use_collapse_triangulate = True
            bpy.ops.object.modifier_apply(modifier=m.name)
    name = obj.name
    joined = pl.join(name, pieces)
    print('PIECES', name, len(pieces), total, '->', pl.triangles(joined))
    return joined
