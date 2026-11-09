"""Blender: the desert's mirror (DAT WorldObjects Mirror0-3; scripts/mirror_source.py wrote work/mirror/mirror.json
from Mirror0, all four share its shape) as a decoration GLB: work/mirror_export.glb and work/mirror_meta.json in the
build.py format (finish.py takes it). LT points about the brush's box centre -> asset frame (Blender (-x, -z, y) x 2.56
/ 81.7, which the glTF export and the engine's (-x, z, y) placement turn back into native (x, z, y)), base centre at the
origin. Each face is wound to its DAT front (the Newell vector of MM9's ring), flat shaded (a hard-edged frame), MM9's
surface mapping as UVs (texels / 128), white COLOR_0. Two materials: `mirror` (the rusty frame, refinerysolidrusta.dtx
as the map's x4 master refixbtk8r) and `mirror_glass` (Icebolt.dtx, the map's icebh2sdfc master, opaque: MM9's glass
surface has no transparency flag). Usage: blender --background --python build_mirror.py"""
import json
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, '..', 'mm9_isleofashes_claude', 'scripts'))
import blib  # noqa: E402

blib.HERE, blib.WORK, blib.TEX = HERE, os.path.join(HERE, 'work'), os.path.join(HERE, 'textures')
S = blib.MM9_SCALE / blib.UNITS_PER_METRE
MATERIALS = ['mirror', 'mirror_glass']


def to_blender(p):
    return Vector((-p[0] * S, -p[2] * S, p[1] * S))


def main():
    blib.reset()
    source = json.load(open(os.path.join(blib.WORK, 'mirror', 'mirror.json')))
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new('UVMap')
    verts = {}

    def vert(p):
        key = tuple(round(c, 3) for c in p)
        if key not in verts:
            verts[key] = bm.verts.new(to_blender(p))
        return verts[key]
    flipped = 0
    for tri in source['triangles']:
        p = np.array(tri['p'])
        front = to_blender(np.cross(p[1] - p[0], p[2] - p[0]))    # the DAT front, as a direction in Blender
        vs, uv = [vert(q) for q in tri['p']], tri['uv']
        if len(set(vs)) < 3:
            continue
        normal = (vs[1].co - vs[0].co).cross(vs[2].co - vs[0].co)
        if normal.length < 1e-12:
            continue
        if normal.dot(front) < 0:
            vs, uv = vs[::-1], uv[::-1]
            flipped += 1
        try:
            f = bm.faces.new(vs)
        except ValueError:
            continue
        f.material_index = MATERIALS.index(tri['material'])
        for loop, (u, v) in zip(f.loops, uv):
            loop[uvl].uv = (u, 1.0 - v)
    me = bpy.data.meshes.new('Mirror')
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new('Mirror', me)
    bpy.context.scene.collection.objects.link(obj)
    for p in me.polygons:
        p.use_smooth = False
    attr = me.color_attributes.new('Color', 'FLOAT_COLOR', 'POINT')
    attr.data.foreach_set('color', np.ones(len(me.vertices) * 4, np.float32))
    me.color_attributes.active_color = attr
    me.materials.append(blib.texture_material('mirror', 'mirror_basecolor.png', roughness=0.8, metallic=0.3))
    me.materials.append(blib.texture_material('mirror_glass', 'mirror_glass_basecolor.png', roughness=0.25))
    # outward check: the frame is a closed box, so every face but the inset glass should face away from the centre
    inward = sum(1 for p in me.polygons if p.normal.dot(p.center) < 0 and p.material_index == 0)
    centre, lo, hi = blib.base_centre([obj])
    blib.shift([obj], centre)
    blib.export([obj], os.path.join(blib.WORK, 'mirror_export.glb'))
    _, lo2, hi2 = blib.base_centre([obj])
    meta = {'prop': 'mirror', 'triangles': [blib.triangles(obj)], 'removed_duplicates': 0, 'removed_small': 0,
            'origin_local_units': [0.0, 0.0, -float(hi2[2] - lo2[2]) * blib.UNITS_PER_METRE / 2],
            'extent_m': [float(v) for v in hi2 - lo2], 'height_units': float(hi2[2] - lo2[2]) * blib.UNITS_PER_METRE,
            'flame_head_m': None, 'materials': MATERIALS}
    with open(os.path.join(blib.WORK, 'mirror_meta.json'), 'w') as f:
        json.dump(meta, f, indent=1)
    print('BUILT mirror', meta['triangles'], 'height', round(meta['height_units'], 1), 'faces', len(me.polygons),
          'flipped to the DAT front', flipped, 'frame faces facing inward', inward)


main()
