"""MM7 hanging cages 7dec05 (empty), 7dec06 (a huddled skeleton) and 7dec07 (a living prisoner gripping the bars),
adapted from the MM6 hanging batch's build_cage.py (../../../mm6_dungeons_3d/hanging/scripts/, read only; its
hanging_lib is imported through dlib). Shape measured on the x2 sprites (scripts/cage_measure.py, row scans; map units,
cage bottom at z = 0, front toward -y): a cylinder 158 units tall, a 14-unit lid disc (radius 47) on top, a 19-unit
bottom band (radius 46.5) round a floor slab, 16 flat bars (radius 44) and six hoops (two pairs and two singles), and
a chain of three big links from the lid to the pivot TOP. In 7d27 every cage hangs with its entity 378 above the floor
and 180 below the ceiling, so the chain shows the sprite's 45 units and enters the ceiling by 2 (binding z_offset -23,
see cage_placements.py and the README).
Figures: 7dec06's skeleton is the MM6 bones batch's Meshy skeleton posed by cage_pose_skeleton.py (cage_huddle)
into work/skeleton_cage_huddle.blend; 7dec07's prisoner is the MM6 native male posed by cage_prisoner.py into
work/prisoner.blend. Run those first.
COLOR_0 = vertex occlusion x a tint per part group toward the sprite's measured mean (hanging_lib.tag/tint).
Writes work/<prop>.blend and work/<prop>_export.glb. Usage: blender --background --python cage_build.py -- <prop>"""
import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dlib  # noqa: E402

hl = dlib.hl
pl = dlib.pl
u = dlib.u
PROP = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else '7dec05'

CAGE = {
    'bottom_band': (42.0, 46.5, 0.0, 19.0), 'floor': 12.0,
    'lid': (47.0, 144.0, 158.0),
    'hoops': [(31.0, 33.5), (37.5, 40.0), (65.0, 69.5), (96.0, 100.5), (124.0, 126.5), (130.5, 133.0)],
    'hoop_r': (42.6, 45.6),
    'bars': (16, 11.25, 44.0, 4.5, 2.5), 'bar_z': (17.0, 146.0),
    'TOP': 205.0, 'link': (24.0, 14.0, 2.8),
}
# Native targets (sRGB, cage_measure.py): chain, lid, bars and hoops, bottom band and floor, figure.
SPECS = {
    '7dec05': {'figure': None,
               'colours': {'chain': (20, 14, 9), 'lid': (17, 8, 5), 'bars': (16, 10, 7), 'bands': (36, 22, 16)}},
    '7dec06': {'figure': 'skeleton',
               'colours': {'chain': (20, 13, 9), 'lid': (19, 10, 7), 'bars': (17, 10, 7), 'bands': (48, 33, 26),
                           'figure': (98, 64, 42)}},
    '7dec07': {'figure': 'prisoner',
               'colours': {'chain': (21, 14, 12), 'lid': (18, 9, 6), 'bars': (22, 13, 10), 'bands': (45, 30, 24),
                           'figure': (114, 49, 30)}},
}
spec = SPECS[PROP]

pl.reset()
mats = {'Iron': dlib.material('Iron', 'cage_iron')}
_figures = {}


def figure(level):
    """The posed figure's LOD (all four loaded together so they share one material and image)."""
    if not _figures:
        if spec['figure'] == 'skeleton':
            path, names = os.path.join(dlib.WORK, 'skeleton_cage_huddle.blend'), \
                [f'Skel_cage_huddle_L{k}' for k in range(4)]
        else:
            path, names = os.path.join(dlib.WORK, 'prisoner.blend'), [f'Prisoner_L{k}' for k in range(4)]
        with bpy.data.libraries.load(path) as (src, dst):
            dst.objects = names
        for k, obj in enumerate(dst.objects):
            _figures[k] = obj
    obj = _figures[level]
    bpy.context.scene.collection.objects.link(obj)
    return obj


def bar(name, angle, radius, z0, z1, width, depth, mat):
    """An upright flat bar (four sides; its ends hide in the bottom band and the lid)."""
    radial = Vector((math.cos(angle), math.sin(angle), 0)); tangent = Vector((-math.sin(angle), math.cos(angle), 0))
    centre = radial * u(radius)
    corners = [centre + radial * u(depth / 2) * a + tangent * u(width / 2) * b
               for a, b in ((1, -1), (1, 1), (-1, 1), (-1, -1))]
    bm = bmesh.new(); uv = bm.loops.layers.uv.verify()
    low = [bm.verts.new(c + Vector((0, 0, u(z0)))) for c in corners]
    high = [bm.verts.new(c + Vector((0, 0, u(z1)))) for c in corners]
    for k in range(4):
        k2 = (k + 1) % 4
        f = bm.faces.new((low[k], low[k2], high[k2], high[k]))
        for loop, (s, t) in zip(f.loops, ((k * 0.25, 0), ((k + 1) * 0.25, 0), ((k + 1) * 0.25, 1), (k * 0.25, 1))):
            loop[uv].uv = (s * 0.3 + angle, t * u(z1 - z0) * 4)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return pl.to_object(name, bm, mat, False)


def two_face_ring(name, r_in, r_out, z0, z1, segments, mat):
    a = pl.lathe(name + 'o', [(u(r_out), u(z0)), (u(r_out), u(z1))], segments, mat, u_repeat=4.0, v_scale=6.0,
                 smooth=False)
    b = pl.lathe(name + 'i', [(u(r_in), u(z1)), (u(r_in), u(z0))], segments, mat, u_repeat=4.0, v_scale=6.0,
                 smooth=False)
    return [a, b]


def cage(level):
    """Cage parts by colour group."""
    iron = mats['Iron']
    seg_band = (28, 18, 10, 8)[level]
    seg_hoop = (22, 16, 9, 8)[level]
    groups = {'bars': [], 'bands': [], 'floor': [], 'lid': [], 'chain': []}
    r_in, r_out, z0, z1 = CAGE['bottom_band']
    if level < 2:     # a rounded tub foot: chamfered lower and upper outer edges
        groups['bands'].append(pl.lathe('band', [(u(r_in), u(z1)), (u(r_in), u(z0)), (u(r_out - 2), u(z0)),
                                                 (u(r_out), u(z0 + 2.5)), (u(r_out), u(z1 - 1.5)),
                                                 (u(r_out - 1.2), u(z1)), (u(r_in), u(z1))][::-1],
                                         seg_band, iron, u_repeat=4.0, v_scale=6.0, smooth=False))
    else:
        groups['bands'].append(pl.lathe('band', [(u(r_out), u(z0)), (u(r_out), u(z1)), (u(r_in), u(z1))],
                                         seg_band, iron, u_repeat=4.0, v_scale=6.0, smooth=False))
    floor_r = r_in + 0.5
    # a closed slab: the cages hang overhead, so the party sees their undersides
    groups['floor'].append(pl.lathe('floor', [(0.0, u(0.5)), (u(floor_r), u(0.5)), (u(floor_r), u(CAGE['floor'])),
                                              (0.0, u(CAGE['floor']))], seg_band, iron, u_repeat=2.0, v_scale=6.0,
                                     smooth=False))
    radius, z_bottom, z_top = CAGE['lid']
    if level < 2:
        profile = [(0.0, z_bottom), (radius - 1.5, z_bottom), (radius, z_bottom + 1.5), (radius, z_top - 2.5),
                   (radius - 2.0, z_top), (0.0, z_top)]
    else:
        profile = [(0.0, z_bottom), (radius, z_bottom), (radius, z_top), (0.0, z_top)]
    groups['lid'].append(pl.lathe('lid', [(u(r), u(z)) for r, z in profile], seg_band, iron, u_repeat=4.0,
                                  v_scale=6.0, smooth=False))
    hoops = CAGE['hoops'] if level < 2 else CAGE['hoops'][2:4] + CAGE['hoops'][::5] if level == 2 else \
        CAGE['hoops'][2:4]
    h_in, h_out = CAGE['hoop_r']
    for k, (a, b) in enumerate(hoops):
        if level < 2:
            groups['bars'].append(hl.ring(f'hoop{k}', h_in, h_out, a, b, seg_hoop, iron))
        else:
            groups['bars'] += two_face_ring(f'hoop{k}', h_in, h_out, a, b, seg_hoop, iron)
    count, offset, bar_r, width, depth = CAGE['bars']
    z_low, z_high = CAGE['bar_z']
    keep = (1, 1, 2, 2)[level]
    for k in range(count):
        if k % keep:
            continue
        a = math.radians(offset) + 2 * math.pi * k / count
        groups['bars'].append(bar(f'bar{k}', a, bar_r, z_low, z_high, width * (1 + 0.3 * (keep - 1)), depth, iron))
    length, link_w, wire = CAGE['link']
    if level < 2:
        path, sides = ((10, 4), (6, 3))[level]
        links, _ = hl.chain('link', z_top, CAGE['TOP'], length, link_w, wire, path, sides, iron)
        groups['chain'] += links
    else:             # the far chain: one flat strap
        groups['chain'].append(hl.sweep('chain', [(0, 0, z_top - 1), (0, 0, CAGE['TOP'])], link_w * 0.3, 4, iron,
                                        flat=0.5))
    return groups


lods = []
for level in range(4):
    groups = cage(level)
    parts = []
    for key, objs in groups.items():
        hl.tag(objs, spec['colours']['bars' if key == 'floor' else key])   # the floor is seen dark between the bars
        parts += objs
    if spec['figure']:
        body = [figure(level)]
        hl.tag(body, spec['colours']['figure'])
        parts += body
    for obj in parts:
        hl.apply(obj)
    name = 'Cage' if level == 0 else f'Cage_LOD{level}'
    solid = pl.join(name, parts)
    occlusion = pl.vertex_occlusion(solid, rays=(32, 20, 12, 8)[level], distance=u(30), strength=0.55, floor=False)
    hl.tint(solid, report=f'{PROP} L{level}')
    print('LEVEL', level, name, 'tris', pl.triangles(solid), 'mean occlusion', round(occlusion, 3))
    lods.append(solid)
dlib.save(PROP, lods)
