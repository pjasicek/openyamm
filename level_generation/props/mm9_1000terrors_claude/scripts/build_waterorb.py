"""Blender: the 1000 Terrors water orb (the translucent blue flame brushes over the invisible candles, DAT
WorldObjects; scripts/waterorb_source.py wrote work/waterorb/orb.json from WorldObject20, all 117 share its shape) as
a decoration GLB: work/waterorb_export.glb and work/waterorb_meta.json in the build.py format (finish.py takes it).
LT points about the orb's box centre -> asset frame (Blender (-x, -z, y) x 2.56 / 81.7, which the glTF export and the
engine's (-x, z, y) placement turn back into native (x, z, y)), base centre at the origin, each triangle wound away
from the centre (the orb is closed and convex), MM9's surface mapping as UVs (water123.spr frame 0, texels / 128),
smooth shading, white COLOR_0 (a glow volume: no occlusion). One material 'waterorb', single-sided; finish.py makes it
alpha-blended at 0.4 (the WorldObjects' Alpha). Usage: blender --background --python build_waterorb.py"""
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


def main():
    blib.reset()
    orb = json.load(open(os.path.join(blib.WORK, 'waterorb', 'orb.json')))
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new('UVMap')
    verts = {}

    def vert(p):
        key = tuple(round(c, 3) for c in p)
        if key not in verts:
            verts[key] = bm.verts.new((-p[0] * S, -p[2] * S, p[1] * S))
        return verts[key]
    for tri in orb['triangles']:
        vs = [vert(p) for p in tri['p']]
        if len(set(vs)) < 3:
            continue
        centre = sum((v.co for v in vs), Vector()) / 3
        normal = (vs[1].co - vs[0].co).cross(vs[2].co - vs[0].co)
        uv = tri['uv']
        if normal.length < 1e-9:
            continue
        if normal.dot(centre) < 0:
            vs, uv = vs[::-1], uv[::-1]
        try:
            f = bm.faces.new(vs)
        except ValueError:
            continue
        for loop, (u, v) in zip(f.loops, uv):
            # centred in one frame of the flipbook (waterorb_flipbook.py): MM9's mapping spans -0.12..0.12
            loop[uvl].uv = (u + 0.5, 0.5 - v)
    me = bpy.data.meshes.new('Waterorb')
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new('Waterorb', me)
    bpy.context.scene.collection.objects.link(obj)
    for p in me.polygons:
        p.use_smooth = True
    attr = me.color_attributes.new('Color', 'FLOAT_COLOR', 'POINT')
    attr.data.foreach_set('color', np.ones(len(me.vertices) * 4, np.float32))
    me.color_attributes.active_color = attr
    material = blib.texture_material('waterorb', 'waterorb_basecolor.png', alpha=False, roughness=0.3)
    me.materials.append(material)
    centre, lo, hi = blib.base_centre([obj])
    blib.shift([obj], centre)
    blib.export([obj], os.path.join(blib.WORK, 'waterorb_export.glb'))
    _, lo2, hi2 = blib.base_centre([obj])
    meta = {'prop': 'waterorb', 'triangles': [blib.triangles(obj)], 'removed_duplicates': 0, 'removed_small': 0,
            'origin_local_units': [0.0, 0.0, -float(hi2[2] - lo2[2]) * blib.UNITS_PER_METRE / 2],
            'extent_m': [float(v) for v in hi2 - lo2], 'height_units': float(hi2[2] - lo2[2]) * blib.UNITS_PER_METRE,
            'flame_head_m': None, 'materials': ['waterorb']}
    with open(os.path.join(blib.WORK, 'waterorb_meta.json'), 'w') as f:
        json.dump(meta, f, indent=1)
    print('BUILT waterorb', meta['triangles'], 'height', round(meta['height_units'], 1), 'faces', len(me.polygons))


main()
