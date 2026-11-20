"""Wooden barrel `dec03` -> work/barrel_export.glb (LOD0..2).

A lathed barrel after the MM6 barrel lathe (../../../mm6_new_sorpigal_3d/scripts/build_prop.py: bulged profile,
recessed open top with an inner wall and floor darkened with depth), traced from the sprite instead of the MM6 scan:
an open barrel with uneven stave tops and a broken notch at the front, and two thick rounded steel hoops at 26 % and
70 % of the height. One material on one atlas (make_textures.py `barrel`): staves around the side (18 planks of the
weathered_planks scan, its nail rows under the hoops), spun steel for the hoops.
Usage: blender --background --python build_barrel.py"""
import math
import os
import sys

import bmesh
import bpy
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mm8lib as ml  # noqa: E402

pl = ml.pl
H = 0.75                      # barrel height (m); the sprite's opaque 124 units include the rim ellipse
R = 0.30                      # radius at the belly
BULGE = 0.085                 # radius drop toward the ends: r = R (1 - BULGE (2z/H - 1)^2)
RIM = 0.022                   # stave thickness at the rim
FLOOR = 0.09                  # inner floor height
HOOPS = [(0.26, 0.07), (0.70, 0.07)]     # centre (fraction of H), height (fraction of H)
HOOP_OUT = 0.016              # hoop thickness outside the staves
WOOD_V = (0.25, 1.0)          # atlas rows of the staves (v up)
HOOP_V = (0.01, 0.21)
NOTCH = {0: 0.0, 1: 0.07, 2: 0.035}       # broken stave tops (fraction of H) by segment offset from the front
LEVELS = [
    {'segments': 24, 'rings': 9, 'hoop_rings': 5, 'inner_rings': 3},
    {'segments': 16, 'rings': 6, 'hoop_rings': 3, 'inner_rings': 2},
    {'segments': 10, 'rings': 3, 'hoop_rings': 2, 'inner_rings': 1},     # open too: the liquid overlay shows
]


def radius(z):
    return R * (1 - BULGE * (2 * z / H - 1) ** 2)


def build(name, segments, rings, hoop_rings, inner_rings):
    rng = np.random.default_rng(3)
    bm = bmesh.new(); uv = bm.loops.layers.uv.new('UVMap'); col = bm.loops.layers.color.new('Color')
    angles = [2 * math.pi * s / segments for s in range(segments)]
    front = int(round((-math.pi / 2 + 0.35) % (2 * math.pi) / (2 * math.pi) * segments)) % segments
    top = np.full(segments, H) - rng.uniform(0, 0.012, segments) * H * (segments > 12)
    for k, drop in NOTCH.items():
        if segments > 12:
            top[(front + k) % segments] -= drop * H

    def quad(verts, uvs):
        f = bm.faces.new(verts)
        for loop, t in zip(f.loops, uvs):
            loop[uv].uv = t; loop[col] = (1.0, 1.0, 1.0, 1.0)
        return f

    def ring(z_of_s, r_of_z):
        return [bm.verts.new((math.cos(a) * r_of_z(z_of_s[s]), math.sin(a) * r_of_z(z_of_s[s]), z_of_s[s]))
                for s, a in enumerate(angles)]
    # outer staves: rings follow the uneven stave tops (each column of quads ends at its stave's top)
    fractions = np.linspace(0, 1, rings)
    outer = [ring(top * f, radius) for f in fractions]
    v_of = lambda z: WOOD_V[0] + (WOOD_V[1] - WOOD_V[0]) * z / H
    for i in range(rings - 1):
        for s in range(segments):
            t = (s + 1) % segments
            a, b, c, d = outer[i][s], outer[i][t], outer[i + 1][t], outer[i + 1][s]
            u0, u1 = s / segments, (s + 1) / segments
            quad((a, b, c, d), ((u0, v_of(a.co.z)), (u1, v_of(b.co.z)), (u1, v_of(c.co.z)), (u0, v_of(d.co.z))))
    # base: a fan under the bottom ring, facing down (closes the shell; seen only from below)
    base_centre = bm.verts.new((0, 0, 0))
    for s in range(segments):
        t = (s + 1) % segments
        f = bm.faces.new((outer[0][t], outer[0][s], base_centre))
        for loop in f.loops:
            p = loop.vert.co
            loop[uv].uv = (0.5 + p.x / R * 0.3, 0.6 + p.y / R * 0.3); loop[col] = (0.4, 0.4, 0.4, 1.0)
    # rim top and inner wall (darkening with depth), floor
    if inner_rings:
        inner_top = ring(top, lambda z: radius(z) - RIM)
        for s in range(segments):
            t = (s + 1) % segments
            quad((outer[-1][s], outer[-1][t], inner_top[t], inner_top[s]),
                 ((s / segments, 0.995), ((s + 1) / segments, 0.995), ((s + 1) / segments, 0.985),
                  (s / segments, 0.985)))
        walls = [inner_top] + [ring(top + (FLOOR - top) * f, lambda z: radius(z) - RIM)
                               for f in np.linspace(0, 1, inner_rings + 1)[1:]]
        shade = lambda z: 0.62 + (0.16 - 0.62) * ((H - z) / (H - FLOOR)) ** 0.7
        for i in range(len(walls) - 1):
            for s in range(segments):
                t = (s + 1) % segments
                a, b, c, d = walls[i][t], walls[i][s], walls[i + 1][s], walls[i + 1][t]
                u0, u1 = (s + 1) / segments, s / segments
                f = bm.faces.new((a, b, c, d))
                for loop, (uu, vert) in zip(f.loops, ((u0, a), (u1, b), (u1, c), (u0, d))):
                    loop[uv].uv = (uu, v_of(vert.co.z) * 0.9)
                    g = shade(vert.co.z); loop[col] = (g, g, g, 1.0)
        floor_ring = walls[-1]
        centre = bm.verts.new((0, 0, FLOOR))
        for s in range(segments):
            t = (s + 1) % segments
            f = bm.faces.new((floor_ring[t], floor_ring[s], centre))
            for loop in f.loops:
                p = loop.vert.co
                loop[uv].uv = (0.5 + p.x / R * 0.3, 0.6 + p.y / R * 0.3); loop[col] = (0.16, 0.16, 0.16, 1.0)
    else:
        centre = bm.verts.new((0, 0, H))
        for s in range(segments):
            t = (s + 1) % segments
            f = bm.faces.new((outer[-1][s], outer[-1][t], centre))
            for loop in f.loops:
                p = loop.vert.co
                loop[uv].uv = (0.5 + p.x / R * 0.3, 0.6 + p.y / R * 0.3); loop[col] = (0.3, 0.3, 0.3, 1.0)
    # hoops: rounded steel bands just outside the staves
    for centre_f, height_f in HOOPS:
        z0, z1 = (centre_f - height_f / 2) * H, (centre_f + height_f / 2) * H
        profile = [(z0 + (z1 - z0) * f, HOOP_OUT * math.sin(math.pi * min(max(f, 0.08), 0.92)) ** 0.5)
                   for f in np.linspace(0, 1, hoop_rings)]
        rows = [[bm.verts.new((math.cos(a) * (radius(z) + o - 0.002), math.sin(a) * (radius(z) + o - 0.002), z))
                 for a in angles] for z, o in profile]
        for i in range(len(rows) - 1):
            for s in range(segments):
                t = (s + 1) % segments
                v0 = HOOP_V[0] + (HOOP_V[1] - HOOP_V[0]) * i / (len(rows) - 1)
                v1 = HOOP_V[0] + (HOOP_V[1] - HOOP_V[0]) * (i + 1) / (len(rows) - 1)
                quad((rows[i][s], rows[i][t], rows[i + 1][t], rows[i + 1][s]),
                     ((s / segments, v0), ((s + 1) / segments, v0), ((s + 1) / segments, v1), (s / segments, v1)))
    bmesh.ops.triangulate(bm, faces=list(bm.faces), quad_method='SHORT_EDGE')
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    obj = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(obj)
    ml.smooth(obj, 45)
    return obj


def main():
    pl.reset()
    mat = ml.material('Barrel', 'barrel', extras={'openyamm_specular': 0.6})
    levels = []
    for k, spec in enumerate(LEVELS):
        obj = build('Barrel' if k == 0 else f'Barrel_LOD{k}', **spec)
        # COLOR_0: corner shading from the build (inner wall, floor) times vertex occlusion (point domain)
        corner = obj.data.color_attributes['Color']
        shade = np.ones(len(obj.data.vertices))
        data = np.empty(len(corner.data) * 4, np.float32); corner.data.foreach_get('color', data)
        data = data.reshape(-1, 4)
        for loop in obj.data.loops:
            shade[loop.vertex_index] = min(shade[loop.vertex_index], data[loop.index, 0])
        obj.data.color_attributes.remove(corner)
        ml.colour(obj, distance=0.25, strength=0.6, power=1.0)
        ml.set_colour(obj, lambda i, co, c: (c[0] * shade[i], c[1] * shade[i], c[2] * shade[i], 1.0))
        obj.data.materials.append(mat)
        levels.append(obj)
    print('LODS', [pl.triangles(o) for o in levels])
    ml.export(levels, 'barrel')


main()
