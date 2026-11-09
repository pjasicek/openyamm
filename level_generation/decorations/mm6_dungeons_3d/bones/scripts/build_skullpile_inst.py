"""MM6 skull pile `sklplrev` (86 placements, dungeons and outdoors; 214 x 153 units, static), version 2: the Meshy
skull asset (skull/, Codex HD masters -> Meshy Smart Topology -> Meshy retexture; work/skull_tex.blend), baked onto
a low-poly skull (bake_skull_proxy.py), instanced
onto the 120 skull-sized lumps of the Meshy skull pile (skullpile/, Smart Topology from the pile's HD master,
squashed to the sprite's width profile; work/skullpile_tex.blend). The direct Meshy pile (build_skullpile.py) paints
faces on blobs that read as lumps up close; one shared skull texture gives every instance crisp sockets and teeth.

Per lump: a skull scaled to the lump's size, facing outward and a little up, with seeded variety (some show the back
or a side, a few lie upside down, jitter in every axis). LOD0 and LOD1 are the skulls at SKULL_TRIS; LOD2 and LOD3 a
fused mound (voxel remesh of LOD1, decimated), whose texture coordinates all point at one plain bone texel.

Colour (native shading transfer, NATIVE_SHADING_TRANSFER.md, per vertex): light = pile occlusion x (0.2 + 0.8
max(0, UP n_z + OUT |n_xy|)), lit from above and outward at every azimuth. The light of the exposed vertices is
histogram-matched to the native sprite's luminance (its near-black gaps, grey-blue mid tones and cream crowns) and
coloured through the sprite's luminance-to-colour table into COLOR_0, over a grey-normalised copy of the skull's
base colour (textures/skullpale_*: its local detail only; make_skullpale.py, which also writes the native tables).
Writes work/skullpile_export.glb (+ work/skullpile.blend) and textures/skullpale_*.
Usage: python3 make_skullpale.py; blender --background --python build_skullpile_inst.py"""
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Euler, Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blib  # noqa: E402

pl = blib.pl
SKULL_TRIS = (220, 40)            # per skull at LOD0 (Meshy skull) and LOD1 (baked proxy)
MOUND_TRIS = (600, 220)           # LOD2 and LOD3
UP, OUT = 0.8, 0.6
EXPOSED = 0.55
CHROMA = 0.9
PALE = 0.88                       # grey level of the pale texture's median (make_skullpale.py)
LUMA = np.array([0.2126, 0.7152, 0.0722])
rng = np.random.default_rng(6)


def loose_parts(bm):
    bm.verts.ensure_lookup_table()
    label = np.full(len(bm.verts), -1); count = 0
    for v in bm.verts:
        if label[v.index] >= 0:
            continue
        stack = [v]; label[v.index] = count
        while stack:
            w = stack.pop()
            for e in w.link_edges:
                o = e.other_vert(w)
                if label[o.index] < 0:
                    label[o.index] = count; stack.append(o)
        count += 1
    return label, count


def native_tables():
    data = np.load(os.path.join(blib.WORK, 'sklplrev_native_tables.npz'))
    return data['lum'], data['centres'], data['table']


def lumps():
    """(centre, size) of each lump of the Meshy pile, in metres."""
    bpy.ops.wm.open_mainfile(filepath=os.path.join(blib.WORK, 'skullpile_tex.blend'))
    obj = bpy.data.objects['skullpile']
    bm = bmesh.new(); bm.from_mesh(obj.data)
    label, count = loose_parts(bm)
    co = np.array([v.co[:] for v in bm.verts]); bm.free()
    out = []
    for k in range(count):
        p = co[label == k]
        if len(p) < 20:
            continue
        out.append((p.mean(0), float((p.max(0) - p.min(0)).mean())))
    return out


def load(path, name):
    with bpy.data.libraries.load(path) as (src, dst):
        dst.objects = [name]
    obj = dst.objects[0]
    bpy.context.scene.collection.objects.link(obj)
    return obj


def skull_levels(materials):
    """LOD0: the Meshy skull without its loose teeth, collapse-decimated to SKULL_TRIS[0] (cleanly: its sockets, nose
    and teeth row stay readable down to about 140); LOD1: the low-poly baked skull (bake_skull_proxy.py) decimated to
    SKULL_TRIS[1] (the Meshy mesh breaks into shards below about 100). Both centred on their bounds, front -y."""
    meshy = load(os.path.join(blib.WORK, 'skull_tex.blend'), 'skull')
    bm = bmesh.new(); bm.from_mesh(meshy.data)
    label, count = loose_parts(bm)
    sizes = np.bincount(label)
    bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if sizes[label[v.index]] < 200], context='VERTS')
    bm.to_mesh(meshy.data); bm.free()
    proxy = load(os.path.join(blib.WORK, 'skullproxy.blend'), 'skullproxy')
    levels, extent = [], None
    for obj, target, mat in ((meshy, SKULL_TRIS[0], materials[0]), (proxy, SKULL_TRIS[1], materials[1])):
        co = np.array([v.co[:] for v in obj.data.vertices])
        obj.data.transform(Matrix.Translation(-Vector((co.min(0) + co.max(0)) / 2)))
        if extent is None:
            extent = float((co.max(0) - co.min(0)).mean())
        obj.data.materials.clear(); obj.data.materials.append(mat)
        for o in bpy.data.objects:
            o.select_set(o is obj)
        bpy.context.view_layer.objects.active = obj
        pl.decimate_to(obj, target)
        for p in obj.data.polygons:
            p.use_smooth = True
        print('SKULL LEVEL', obj.name, pl.triangles(obj))
        levels.append(obj)
    return levels, extent


def cull_hidden(obj, rays=48):
    """Delete the triangles no outside viewer can see: from each triangle's centre, rays over its outer hemisphere
    (never into the ground); a triangle with every ray blocked within the pile's size is buried."""
    from mathutils.bvhtree import BVHTree
    bm = bmesh.new(); bm.from_mesh(obj.data)
    bm.faces.ensure_lookup_table()
    tree = BVHTree.FromBMesh(bm)
    dirs = rng.normal(size=(rays, 3)); dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
    dirs[:, 2] = np.abs(dirs[:, 2]) * 0.9 + 0.1 * np.sign(dirs[:, 2] + 1e-9)
    dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
    reach = blib.u(400)
    hidden = []
    for face in bm.faces:
        centre = face.calc_center_median(); n = face.normal
        start = centre + n * 1e-4
        seen = False
        for d in dirs:
            d = Vector(d)
            if d.dot(n) <= 0.05:
                continue
            if tree.ray_cast(start, d, reach)[0] is None:
                seen = True
                break
        if not seen:
            hidden.append(face)
    bmesh.ops.delete(bm, geom=hidden, context='FACES')
    bm.to_mesh(obj.data); bm.free()
    return len(hidden)


def placements(lump_list, extent):
    """A world matrix per lump: outward-facing skull with seeded variety."""
    out = []
    for centre, size in lump_list:
        c = Vector(centre)
        radial = Vector((c.x, c.y, 0))
        radial = radial.normalized() if radial.length > 1e-4 else Vector((0, -1, 0))
        facing = (radial + Vector((0, 0, 0.05 + 0.25 * rng.random()))).normalized()
        roll = rng.normal(0, 12)
        kind = rng.random()
        if kind < 0.12:
            facing = -facing                               # shows the back of the cranium
        elif kind < 0.27:
            facing = Matrix.Rotation(math.radians(rng.choice((-90, 90))), 3, 'Z') @ facing   # profile
        elif kind < 0.32:
            roll += 160                                    # lies upside down
        facing = (Euler([math.radians(a) for a in rng.normal(0, 14, 3)]).to_matrix() @ facing).normalized()
        rotation = facing.to_track_quat('-Y', 'Z').to_matrix().to_4x4() @ Matrix.Rotation(
            math.radians(roll), 4, 'Y')
        scale = size / extent * (1.06 + rng.normal(0, 0.05))
        out.append(Matrix.Translation(c) @ rotation @ Matrix.Scale(scale, 4))
    return out


def instances(template, matrices, name):
    parts = []
    for k, m in enumerate(matrices):
        obj = template.copy(); obj.data = template.data.copy(); obj.name = f'{name}_{k}'
        bpy.context.scene.collection.objects.link(obj)
        obj.data.transform(m)
        parts.append(obj)
    joined = pl.join(name, parts)
    for v in joined.data.vertices:
        v.co.z = max(v.co.z, 0.0)
    return joined


def mound(source, target, name, uv, voxel):
    obj = blib.duplicate(source, name)
    for o in bpy.data.objects:
        o.select_set(o is obj)
    bpy.context.view_layer.objects.active = obj
    mod = obj.modifiers.new('R', 'REMESH'); mod.mode = 'VOXEL'; mod.voxel_size = blib.u(voxel)
    bpy.ops.object.modifier_apply(modifier=mod.name)
    pl.decimate_to(obj, target)
    for v in obj.data.vertices:
        v.co.z = max(v.co.z, 0.0)
    if not obj.data.uv_layers:
        obj.data.uv_layers.new(name='UVMap')
    for loop in obj.data.uv_layers[0].data:
        loop.uv = uv
    return obj


def displayed_mean(obj, grid):
    """Mean linear luminance shown at light one: texture (sampled at each loop's UV) x COLOR_0, over the loops."""
    h, w = grid.shape
    me = obj.data
    uv = np.empty(len(me.loops) * 2, np.float32); me.uv_layers[0].data.foreach_get('uv', uv); uv = uv.reshape(-1, 2)
    verts = np.empty(len(me.loops), np.int32); me.loops.foreach_get('vertex_index', verts)
    colours = np.empty(len(me.vertices) * 4, np.float32); me.color_attributes['Color'].data.foreach_get('color', colours)
    lum = colours.reshape(-1, 4)[:, :3] @ LUMA
    tex = grid[np.clip((uv[:, 1] * h).astype(int), 0, h - 1), np.clip((uv[:, 0] * w).astype(int), 0, w - 1)]
    return float((tex * lum[verts]).mean())


def colour(obj, rays, native):
    """COLOR_0 from the per-vertex light histogram-matched to the native sprite (see the module docstring)."""
    for p in obj.data.polygons:
        p.use_smooth = True
    pl.vertex_occlusion(obj, rays=rays, distance=blib.u(30), strength=1.0, floor=True)
    attr = obj.data.color_attributes['Color']
    occ = np.empty(len(obj.data.vertices) * 4, np.float32); attr.data.foreach_get('color', occ)
    occ = occ.reshape(-1, 4)[:, 0].astype(np.float64)
    # Each skull is shaded as the sprite's are, like a ball: by the direction from its own centre (smooth over the
    # few big triangles of a low-poly skull), times the pile occlusion averaged half with its skull's mean.
    bm = bmesh.new(); bm.from_mesh(obj.data)
    label, count = loose_parts(bm); bm.free()
    co = np.array([v.co[:] for v in obj.data.vertices])
    centres_of = np.array([co[label == k].mean(0) for k in range(count)])
    mean_occ = np.array([occ[label == k].mean() for k in range(count)])
    radial = co - centres_of[label]
    radial /= np.maximum(np.linalg.norm(radial, axis=1, keepdims=True), 1e-9)
    occ = 0.5 * occ + 0.5 * mean_occ[label]
    light = occ * (0.2 + 0.8 * np.clip(UP * radial[:, 2] + OUT * np.linalg.norm(radial[:, :2], axis=1), 0, 1))
    native_lum, centres, table = native
    exposed = light[occ > EXPOSED]
    q = np.linspace(0, 1, 129)
    lum = np.interp(light, np.quantile(exposed, q), np.quantile(native_lum, q))
    tone = os.path.join(blib.WORK, 'pile_tone.npz')
    if os.path.exists(tone):                       # pile_tone.py: matches the rendered front view to the sprite
        curve = np.load(tone)
        lum = np.interp(lum, curve['before'], curve['after'])
    rgb = np.stack([np.interp(lum, centres, table[:, c]) for c in range(3)], axis=-1)
    grey = (rgb @ LUMA)[:, None]
    rgb = grey + (rgb - grey) * CHROMA             # the yellow crowns turn olive over the texture's darker detail
    rgb *= (lum / np.maximum(rgb @ LUMA, 1e-4))[:, None]
    linear = blib.srgb_to_linear(np.clip(rgb, 0, 1)) / blib.srgb_to_linear(PALE)
    clipped = float((linear > 1).mean())
    values = np.c_[np.clip(linear, 0, 1), np.ones(len(linear))].astype(np.float32)
    attr.data.foreach_set('color', values.ravel())
    return clipped


def main():
    native = native_tables()
    lump_list = lumps()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    material = blib.texture_material('Bone', 'skullpale')
    far = blib.texture_material('BoneFar', 'proxypale')
    levels, extent = skull_levels((material, far))
    matrices = placements(lump_list, extent)
    lods = [instances(levels[0], matrices, 'SkullPile'), instances(levels[1], matrices, 'SkullPile_LOD1')]
    for obj in levels:
        bpy.data.objects.remove(obj)
    if '--no-cull' not in sys.argv:
        for obj in lods:
            print('CULLED', obj.name, cull_hidden(obj), 'kept', pl.triangles(obj))
    # A plain texel of the pale texture for the mounds: the one nearest its mean grey in a smooth neighbourhood.
    image = next(n for n in far.node_tree.nodes if n.type == 'TEX_IMAGE').image
    w, h = image.size
    grid = np.array(image.pixels[:], np.float32).reshape(h, w, 4)[..., 0]
    blocks = grid.reshape(h // 8, 8, w // 8, 8)
    score = np.abs(blocks.mean((1, 3)) - PALE) + blocks.std((1, 3))
    row, col = np.unravel_index(np.argmin(score), score.shape)
    uv = ((col + 0.5) * 8 / w, (row + 0.5) * 8 / h)
    lods += [mound(lods[1], MOUND_TRIS[0], 'SkullPile_LOD2', uv, 11.0), mound(lods[1], MOUND_TRIS[1], 'SkullPile_LOD3', uv, 14.0)]
    grids = {}
    for mat in (material, far):
        img = next(n for n in mat.node_tree.nodes if n.type == 'TEX_IMAGE').image
        grids[mat.name] = blib.srgb_to_linear(np.array(img.pixels[:], np.float32).reshape(
            img.size[1], img.size[0], 4)[..., 0])
    lod1_mean = None
    for level, (obj, rays) in enumerate(zip(lods, (32, 20, 16, 12))):
        clipped = colour(obj, rays, native)
        shown = displayed_mean(obj, grids[obj.data.materials[0].name])
        if level == 1:
            lod1_mean = shown
        elif level > 1:
            # The fused mounds lose the dark gaps between the skulls: scale them to LOD1's displayed brightness.
            attr = obj.data.color_attributes['Color']
            values = np.empty(len(obj.data.vertices) * 4, np.float32); attr.data.foreach_get('color', values)
            values = values.reshape(-1, 4); values[:, :3] *= lod1_mean / shown
            attr.data.foreach_set('color', values.ravel())
        lo, hi = pl.bounds([obj])
        print('LEVEL', level, obj.name, 'tris', pl.triangles(obj), 'clipped', round(clipped, 3),
              'size units', [round(v * blib.dl.UNITS_PER_METRE, 1) for v in (hi - lo)])
    print('SKULLS', len(matrices))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(blib.WORK, 'skullpile.blend'))
    pl.export(lods, os.path.join(blib.WORK, 'skullpile_export.glb'))


main()
