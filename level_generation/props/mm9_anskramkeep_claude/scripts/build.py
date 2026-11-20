"""Blender: builds each keep prop's decoration GLB (work/<prop>_export.glb, LOD objects <Prop>, <Prop>_LOD1, ...) and
work/<prop>_meta.json from the raw converter GLBs, with the isle props project's helpers (its scripts/blib.py, paths
pointed at this project): asset frame (the raw import mirrored in X), clean, faces wound to agree with the ABC's
authored normals, open pieces on a double-sided copy of the material, normals smooth within 40 degrees, COLOR_0
vertex occlusion, base centre at the origin; LODs only from 1000 triangles (the native ABC LOD when its count is near,
else a collapse decimation). The wall torch gets the shared CC0 flame flipbook cards at its head.
Usage: blender --background --python build.py -- [prop ...]"""
import json
import os
import sys

import bpy
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ISLE = os.path.join(HERE, '..', 'mm9_isleofashes_claude', 'scripts')
sys.path.insert(0, ISLE)
import blib  # noqa: E402

blib.HERE, blib.WORK, blib.TEX = HERE, os.path.join(HERE, 'work'), os.path.join(HERE, 'textures')
# Import skinned (full) props without Blender 5's bone-display ball (an 80-triangle Icosphere the weapon rack kept
# inside the rack until 2026-10-31); every project that runs this build gets it.
blib.SKIP_BONE_SHAPES = True

SMOOTH = 40.0
# No LODs below 1000 triangles (was 250 until 2026-11-09): they save next to nothing, and decimating a simple prop breaks
# its shape (the raised coffin's LOD2 caved in its lid and tore its sides).
LOD_MIN = 1000
PROPS = {name: {} for name in (
    'barrel', 'barrel03', 'bed', 'bedmedium', 'bookcase02ew', 'bookcase02ns', 'chair02', 'chest', 'chest1', 'crate',
    'desk01', 'desk01ns', 'dresserns', 'scroll', 'tablebench', 'tableround', 'trashpile', 'weaponrack',
    'weaponscabinet01', 'weaponscabinet04', 'spikepit')}
PROPS['chair'] = {'alpha': True}
PROPS['weaponrack'] = {'armature': True}
# The *ns furniture imports a quarter turn from the old transcoder's bake (which the isle's props match to under a
# unit); the turn (degrees about Z, asset frame) puts them back in its frame (placements.py fit 0.5-0.9).
for name in ('bookcase02ns', 'desk01ns', 'dresserns'):
    PROPS[name] = {'turn': 90}
PROPS['chair02'] = {'lods': False}          # 256 triangles, two placements: a decimated LOD2 inverts a leg
# Flame cards on the torch head: (x offset, width, bottom, top, mirrored) in metres from the head's top centre.
PROPS['walltorch'] = {'flame': [(-0.03, 0.30, -0.06, 0.42, False), (0.04, 0.26, -0.06, 0.34, True)]}
# The Imp gates' fires (MM9 Fire objects, FireScale 12): flame cards only, standing on the floor.
PROPS['gatefire'] = {'flame_only': True, 'flame': [(-0.12, 0.85, 0.0, 1.35, False), (0.16, 0.7, 0.0, 1.1, True),
                                                   (0.0, 1.0, 0.0, 1.6, False)]}


def build_flame_only(prop):
    spec = PROPS[prop]
    blib.reset()
    fire_material = blib.texture_material('Fire', 'flame02_basecolor.png', alpha=True)
    fire_material.use_backface_culling = False
    obj = flame_cards(spec['flame'], (0.0, 0.0, 0.0), 'UVMap')
    obj.data.materials.append(fire_material)
    name = prop.capitalize()
    obj.name = name
    obj.data.name = name
    blib.export([obj], os.path.join(blib.WORK, f'{prop}_export.glb'))
    _, lo, hi = blib.base_centre([obj])
    meta = {'prop': prop, 'triangles': [blib.triangles(obj)], 'removed_duplicates': 0, 'removed_small': 0,
            'origin_local_units': [0.0, 0.0, 0.0], 'extent_m': [float(v) for v in hi - lo],
            'height_units': float(hi[2] - lo[2]) * blib.UNITS_PER_METRE, 'flame_head_m': [0.0, 0.0, 0.0]}
    with open(os.path.join(blib.WORK, f'{prop}_meta.json'), 'w') as f:
        json.dump(meta, f, indent=1)
    print('BUILT', prop, meta['triangles'], 'height', round(meta['height_units'], 1))


def lod_sources(prop):
    raw = os.path.join(blib.WORK, 'raw', prop)
    paths = [os.path.join(raw, f'{prop}.glb')]
    n = 1
    while os.path.exists(os.path.join(raw, f'lod{n}', f'{prop}.glb')):
        paths.append(os.path.join(raw, f'lod{n}', f'{prop}.glb'))
        n += 1
    return paths


def open_faces(obj):
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bm.faces.ensure_lookup_table()
    seen, out = set(), []
    for f in bm.faces:
        if f.index in seen:
            continue
        stack, piece = [f], []
        seen.add(f.index)
        while stack:
            g = stack.pop()
            piece.append(g)
            for e in g.edges:
                for h in e.link_faces:
                    if h.index not in seen:
                        seen.add(h.index)
                        stack.append(h)
        if any(len(e.link_faces) != 2 for g in piece for e in g.edges):
            out.extend(g.index for g in piece)
    bm.free()
    return set(out)


def flame_cards(cards, head, uv_name):
    """Camera-facing cards (openyamm_billboard in finish.py) of the shared Flame02 flipbook above `head`."""
    import bmesh
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new(uv_name)
    for cx, w, b, t, mirrored in cards:
        x0, x1 = head[0] + cx - w / 2, head[0] + cx + w / 2
        verts = [bm.verts.new(c) for c in ((x0, head[1], head[2] + b), (x1, head[1], head[2] + b),
                                            (x1, head[1], head[2] + t), (x0, head[1], head[2] + t))]
        f = bm.faces.new(verts)
        for loop, (u, v) in zip(f.loops, ((0, 1), (1, 1), (1, 0), (0, 0))):
            loop[uvl].uv = (1 - u if mirrored else u, (1 - v) * 0.8)
    me = bpy.data.meshes.new('Fire')
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new('Fire', me)
    bpy.context.scene.collection.objects.link(obj)
    attr = me.color_attributes.new('Color', 'FLOAT_COLOR', 'POINT')
    attr.data.foreach_set('color', np.ones(len(me.vertices) * 4, np.float32))
    me.color_attributes.active_color = attr
    return obj


def join(objects, name):
    for o in bpy.data.objects:
        o.select_set(o in objects)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    objects[0].name = name
    objects[0].data.name = name
    return objects[0]


def build(prop):
    spec = PROPS[prop]
    if spec.get('flame_only'):
        return build_flame_only(prop)
    blib.reset()
    origin = blib.binding_origins()[prop]
    sources = lod_sources(prop)
    mats = {'solid': blib.texture_material(prop, f'{prop}_basecolor.png', alpha=spec.get('alpha', False))}
    mats['double'] = mats['solid'].copy()
    mats['double'].name = f'{prop}_2s'
    mats['double'].use_backface_culling = False
    if spec.get('flame'):
        mats['fire'] = blib.texture_material('Fire', 'flame02_basecolor.png', alpha=True)
        mats['fire'].use_backface_culling = False
    armature = spec.get('armature', False)
    lod0 = blib.import_raw(sources[0], 'lod0', origin, apply_armature=armature)
    if spec.get('turn'):
        from mathutils import Matrix
        import math
        lod0.data.transform(Matrix.Rotation(math.radians(spec['turn']), 4, 'Z'))
    dup, small = blib.clean(lod0)
    count0 = blib.triangles(lod0)
    levels = [lod0]
    if count0 >= LOD_MIN and spec.get('lods', True):
        natives = []
        for path in sources[1:]:
            o = blib.import_raw(path, 'native', origin, apply_armature=armature)
            blib.clean(o)
            natives.append(o)
        for target, window in ((0.5, (0.4, 0.65)), (0.25, (0.18, 0.35))):
            pick = next((o for o in natives if window[0] <= blib.triangles(o) / count0 <= window[1]), None)
            if pick is None:
                pick = lod0.copy()
                pick.data = lod0.data.copy()
                bpy.context.scene.collection.objects.link(pick)
                blib.decimate(pick, target)
            else:
                natives.remove(pick)
            levels.append(pick)
        for o in natives:
            bpy.data.objects.remove(o, do_unlink=True)
    centre, lo, hi = blib.base_centre([lod0])
    centre.x += spec.get('frame_x', 0.0)      # a frame kept from an earlier install (blib.BOOK_BALL_FRAME_X_M)
    names = [prop.capitalize()] + [f'{prop.capitalize()}_LOD{i}' for i in range(1, len(levels))]
    finished, counts = [], []
    head = None
    for obj, name in zip(levels, names):
        blib.shift([obj], centre)
        for v in obj.data.vertices:
            if v.co.z < 0.0:
                v.co.z = 0.0
        obj.data.materials.clear()
        for key in ('solid', 'double'):
            obj.data.materials.append(mats[key])
        opened = open_faces(obj)
        for p in obj.data.polygons:
            p.material_index = 1 if p.index in opened else 0
        blib.smooth(obj, SMOOTH)
        size = max(hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2])
        blib.occlusion(obj, distance=0.15 * size, strength=0.55)
        if spec.get('flame'):
            if head is None:      # the torch head: the top 12 % of LOD0's vertices
                pts = np.array([v.co[:] for v in obj.data.vertices])
                top = pts[pts[:, 2] >= pts[:, 2].max() - 0.12 * (pts[:, 2].max() - pts[:, 2].min())]
                head = (float(top[:, 0].mean()), float(top[:, 1].mean()), float(pts[:, 2].max()))
            fire = flame_cards(spec['flame'], head, obj.data.uv_layers.active.name)
            fire.data.materials.append(mats['fire'])
            obj = join([obj, fire], name)
        obj.name = name
        obj.data.name = name
        used = {p.material_index for p in obj.data.polygons}
        for index in sorted(range(len(obj.data.materials)), reverse=True):
            if index not in used:
                obj.data.materials.pop(index=index)
        finished.append(obj)
        counts.append(blib.triangles(obj))
    blib.export(finished, os.path.join(blib.WORK, f'{prop}_export.glb'))
    _, lo2, hi2 = blib.base_centre([finished[0]])
    meta = {'prop': prop, 'triangles': counts, 'removed_duplicates': dup, 'removed_small': small,
            'origin_local_units': [-centre.x * blib.UNITS_PER_METRE, -centre.y * blib.UNITS_PER_METRE,
                                   centre.z * blib.UNITS_PER_METRE],
            'extent_m': [float(v) for v in hi2 - lo2], 'height_units': float(hi2[2] - lo2[2]) * blib.UNITS_PER_METRE,
            'flame_head_m': head}
    with open(os.path.join(blib.WORK, f'{prop}_meta.json'), 'w') as f:
        json.dump(meta, f, indent=1)
    print('BUILT', prop, counts, 'height', round(meta['height_units'], 1))


def main():
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    for prop in args or sorted(PROPS):
        build(prop)


main()
