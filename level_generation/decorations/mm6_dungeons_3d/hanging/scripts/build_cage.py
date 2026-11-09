"""MM6 dungeon cages, measured on the restored x2 sprites (world units; the sprite height is the cage height):
- `hngncge2` (133 x 249): an iron cage of 12 flat bars between a top and a bottom band, four riveted hoops, a
  prisoner's skeleton hanging inside by its wrists from short chains under the top band, knees bent, feet just above
  the cage floor.
- `empty` (133 x 249): the same kind of cage, wider bands with inner lips, 16 bars, six plain hoops, no prisoner.
- `bonecage` (141 x 250): a standing (never hanging: every placement is on the floor) cage of 20 thin bars, riveted
  bands with front strap plates and four riveted hoops, a lidded top, a skeleton sitting huddled on its floor.
The hanging cages hang from two crossed straps and a chain whose top link's upper end is the bounds top (the swing
pivot): the cage stays 249 units tall and the chain reaches TOP units, so a binding of height TOP keeps the cage at
its native size. The `_long` variants hang from a longer chain for the two placements under a high ceiling.
The prisoners are the bones batch's Meshy skeleton (../../bones/: Codex HD masters, Meshy Smart Topology and
retexture, its Meshy skull grafted on), posed rigidly by ../../bones/scripts/pose_skeleton.py into
../../bones/work/skeleton_<pose>.blend (LOD objects Skel_<pose>_L0..L3, cage-local metres, own textured materials);
run that first. The shackles hang at the posed wrists (skeleton_<pose>.json).
Writes work/<prop>_export.glb. Usage: blender --background --python build_cage.py -- <prop>"""
import math
import os
import sys

import json

import bmesh
import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hanging_lib as hl  # noqa: E402

pl = hl.pl
u = hl.u
PROP = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'hngncge2'

BONES = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'bones', 'work')

# Cage specs in map units: bands (r_in, r_out, z0, z1), lips (inner rings), hoops (z0, z1) at hoop_r, bars (count,
# angle offset degrees, centre radius, tangential width, radial depth), floor slab top, rivets, top (straps + chain
# reaching TOP, or a lid), native target colours (sRGB, measure.py).
SPECS = {
    'hngncge2': {
        'top_band': (50.0, 58.5, 219, 247), 'bottom_band': (50.0, 58.5, 0, 30), 'lips': [],
        'hoops': [(198, 204), (145, 152), (98, 104), (49, 56)], 'hoop_r': (50.5, 55.5),
        'bars': (12, 15.0, 52.0, 5.0, 3.0), 'floor': 22, 'hoop_rivets': 1, 'band_rivets': 0, 'plates': None,
        'top': 'straps', 'TOP': 321, 'skeleton': 'hanging', 'shackles': True,
        'colours': {'bars': (33, 27, 24), 'bands': (52, 45, 41), 'bone': (127, 97, 74)},
    },
    'empty': {
        'top_band': (59.0, 66.5, 219, 247), 'bottom_band': (59.0, 66.5, 0, 31),
        'lips': [(59.0, 63.5, 211, 219), (59.0, 63.5, 31, 39)],
        'hoops': [(197, 202), (186, 191), (144, 153), (98, 106), (61, 65), (50, 55)], 'hoop_r': (59.5, 64.0),
        'bars': (16, 5.0, 61.5, 4.0, 3.0), 'floor': 24, 'hoop_rivets': 0, 'band_rivets': 0, 'plates': None,
        'top': 'straps', 'TOP': 321, 'skeleton': None, 'shackles': False,
        'colours': {'bars': (25, 23, 20), 'bands': (51, 47, 41)},
    },
    'bonecage': {
        'top_band': (61.0, 69.25, 220, 247), 'bottom_band': (61.0, 69.25, 0, 28), 'lips': [],
        'hoops': [(189, 199), (144, 151), (97, 104), (49, 60)], 'hoop_r': (61.5, 66.5),
        'bars': (20, 9.0, 63.0, 3.5, 3.0), 'floor': 24, 'hoop_rivets': 2, 'band_rivets': 8,
        'plates': [(25.0, 220, 247), (19.0, 0, 28)],
        'top': 'lid', 'TOP': 247, 'skeleton': 'sitting', 'shackles': False,
        'colours': {'bars': (19, 18, 20), 'bands': (23, 22, 25), 'bone': (82, 79, 76)},     # below the measured (94, 91, 88): the smooth Meshy bones read white at that mean
    },
}
# Long-chain variants for the placements under high ceilings (per-map bindings): 6d20's hngncge2 (ceiling 1152
# above its floor; the chain top 7 above it) and 6t8's empty cage (hung 192 above a pit floor, the ceiling 640 above
# its base; the chain top 64 above it, like the standard cages' chains in their low rooms).
# Their many links are coarser: (path points, sides) at LOD0 and LOD1 (LOD1 links are diamonds).
SPECS['hngncge2_long'] = dict(SPECS['hngncge2'], TOP=1160, chain_link=(24.0, 13.0, 2.4),
                              chain_detail=((8, 3), (4, 3)))
SPECS['empty_long'] = dict(SPECS['empty'], TOP=705, chain_link=(20.0, 11.0, 2.0), chain_detail=((8, 3), (4, 3)))
spec = SPECS[PROP]
LONG = PROP.endswith('_long')

pl.reset()
mats = {'Iron': hl.material('Iron', 'iron')}


_prisoners = {}


def prisoner(level):
    """The posed Meshy skeleton's LOD from the bones batch. All four levels are loaded together, so they share one
    Bone and one Skull material (and their images) in the export."""
    if not _prisoners:
        path = os.path.join(BONES, f"skeleton_{spec['skeleton']}.blend")
        names = [f"Skel_{spec['skeleton']}_L{k}" for k in range(4)]
        with bpy.data.libraries.load(path) as (src, dst):
            dst.objects = names
        for k, obj in enumerate(dst.objects):
            _prisoners[k] = obj
    obj = _prisoners[level]
    bpy.context.scene.collection.objects.link(obj)
    return obj


def wrists():
    """Posed wrist positions (map units) of the hanging prisoner, for the shackles."""
    posed = json.load(open(os.path.join(BONES, f"skeleton_{spec['skeleton']}.json")))
    return {'hand_l': posed['wrist_l'], 'hand_r': posed['wrist_r']}


def bar(name, angle, radius, z0, z1, width, depth, mat):
    """An upright flat bar (four sides, its ends hidden in the bands) at angle (radians) around the axis."""
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
            loop[uv].uv = (s, t * u(z1 - z0) * 4)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return pl.to_object(name, bm, mat, False)


def two_face_ring(name, r_in, r_out, z0, z1, segments, mat):
    """Distant hoop or band: only its outer and inner faces."""
    a = pl.lathe(name + 'o', [(u(r_out), u(z0)), (u(r_out), u(z1))], segments, mat, u_repeat=4.0, v_scale=6.0,
                 smooth=False)
    b = pl.lathe(name + 'i', [(u(r_in), u(z1)), (u(r_in), u(z0))], segments, mat, u_repeat=4.0, v_scale=6.0,
                 smooth=False)
    return [a, b]


def cage(level):
    """The iron cage, by part group: {'bars': [...], 'bands': [...]}."""
    seg_band = (24, 16, 8, 6)[level]
    seg_hoop = (20, 14, 8, 6)[level]
    groups = {'bars': [], 'bands': []}
    for key in ('top_band', 'bottom_band'):
        r_in, r_out, z0, z1 = spec[key]
        if level < 2:
            groups['bands'].append(hl.ring(key, r_in, r_out, z0, z1, seg_band, mats['Iron']))
        elif level == 3:
            groups['bands'].append(pl.lathe(key, [(u(r_out), u(z0)), (u(r_out), u(z1))], seg_band, mats['Iron'],
                                            u_repeat=4.0, v_scale=6.0, smooth=False))
        else:
            groups['bands'] += two_face_ring(key, r_in, r_out, z0, z1, seg_band, mats['Iron'])
            cap_z = z1 if key == 'top_band' else z0
            groups['bands'].append(pl.lathe(key + 'cap', [(u(r_in), u(cap_z)), (u(r_out), u(cap_z))][::(
                -1 if key == 'top_band' else 1)], seg_band, mats['Iron'], smooth=False))
    if level < 2:
        for k, (r_in, r_out, z0, z1) in enumerate(spec['lips']):
            groups['bands'].append(hl.ring(f'lip{k}', r_in, r_out, z0, z1, seg_band, mats['Iron']))
    hoops = spec['hoops'] if level < 2 else spec['hoops'][1::2] if level == 2 else []
    h_in, h_out = spec['hoop_r']
    for k, (z0, z1) in enumerate(hoops):
        if level < 2:
            groups['bars'].append(hl.ring(f'hoop{k}', h_in, h_out, z0, z1, seg_hoop, mats['Iron']))
        else:
            groups['bars'] += two_face_ring(f'hoop{k}', h_in, h_out, z0, z1, seg_hoop, mats['Iron'])
    count, offset, radius, width, depth = spec['bars']
    z_low, z_high = spec['bottom_band'][3] - 2, spec['top_band'][2] + 2
    angles = [math.radians(offset) + 2 * math.pi * k / count for k in range(count)]
    for k, a in enumerate(angles):
        keep = 1 if level < 2 or count <= 8 else 2 if level == 2 and count > 12 else 3 if level == 3 else 1
        if k % keep:
            continue                        # the far cage keeps every second or third bar, a little wider
        groups['bars'].append(bar(f'bar{k}', a, radius, z_low, z_high, width * (1 + 0.4 * (keep - 1)), depth,
                                  mats['Iron']))
    floor_r = spec['bottom_band'][0] + 0.5
    if level < 2:
        groups['bands'].append(hl.disc('floor', floor_r, 1, spec['floor'], seg_band, mats['Iron']))
    else:                                   # the far floor: its top only
        groups['bands'].append(pl.lathe('floor', [(u(floor_r), u(spec['floor'])), (0.0, u(spec['floor']))],
                                        seg_band, mats['Iron'], smooth=False))
    if level == 0:
        for k, (z0, z1) in enumerate(spec['hoops']):
            step = spec['hoop_rivets']
            if not step:
                continue
            for i, a in enumerate(angles):
                if i % step:
                    continue
                d = Vector((math.cos(a), math.sin(a), 0))
                groups['bars'].append(hl.rivet(f'hr{k}_{i}', d * h_out + Vector((0, 0, (z0 + z1) / 2)), d, 1.8,
                                               mats['Iron']))
        if spec['band_rivets']:
            for key in ('top_band', 'bottom_band'):
                r_in, r_out, z0, z1 = spec[key]
                for i in range(spec['band_rivets']):
                    a = 2 * math.pi * (i + 0.5) / spec['band_rivets'] - math.pi / 2
                    d = Vector((math.cos(a), math.sin(a), 0))
                    groups['bands'].append(hl.rivet(f'br{key}{i}', d * r_out + Vector((0, 0, (z0 + z1) / 2)), d,
                                                    2.6, mats['Iron']))
    if spec['plates'] and level < 2:
        r_out = spec['top_band'][1]
        for k, (half, z0, z1) in enumerate(spec['plates']):
            # A strap plate over the band's front (-y), slightly proud of it.
            depth_y = -(r_out + 0.2)
            plate = pl.box(f'plate{k}', (0, u(depth_y), u((z0 + z1) / 2)), (u(half * 2), u(3.0), u(z1 - z0)),
                           mats['Iron'], uv_scale=3.0)
            groups['bands'].append(plate)
            if level == 0:
                groups['bands'].append(hl.rivet(f'pr{k}', (0, depth_y - 1.5, (z0 + z1) / 2), (0, -1, 0), 3.2,
                                                mats['Iron']))
    top = spec['top_band'][3]
    if spec['top'] == 'lid':
        if level < 2:
            groups['bands'].append(hl.disc('lid', spec['top_band'][0] + 0.5, top - 4, top, seg_band, mats['Iron']))
        else:
            groups['bands'].append(pl.lathe('lid', [(u(spec['top_band'][1]), u(top)), (0.0, u(top))], seg_band,
                                            mats['Iron'], smooth=False))
    return groups


def hanger(level):
    """Two crossed straps over the top meeting at an eye, then the chain up to TOP (the pivot)."""
    top = spec['top_band'][3]
    r = spec['top_band'][0] + 3
    apex = top + 11
    parts = []
    for k, a in enumerate((math.pi / 4, -math.pi / 4)):
        d = Vector((math.cos(a), math.sin(a), 0))
        pts = []
        steps = (7, 5, 3, 3)[level]
        for s in range(steps):
            t = -1 + 2 * s / (steps - 1)
            pts.append(d * (r * t) + Vector((0, 0, top - 1 + (apex - top + 1) * (1 - t * t) ** 0.6)))
        parts.append(hl.sweep(f'strap{k}', pts, 2.2, (4, 4, 3, 3)[level], mats['Iron'], caps=level < 2, flat=0.55,
                              phase=math.pi / 4))
    length, width, wire = spec.get('chain_link', (16.0, 9.0, 1.7))
    if level < 2:
        path, sides = spec.get('chain_detail', ((10, 4), (8, 3)))[level]
        links, bottom = hl.chain('link', apex - 2, spec['TOP'], length, width, wire, path, sides, mats['Iron'])
        parts += links
        if bottom > apex:
            parts.append(hl.sweep('eye', [(0, 0, apex - 1), (0, 0, bottom + 3)], wire * 1.2, 4, mats['Iron']))
    else:
        parts.append(hl.sweep('chain', [(0, 0, apex - 1), (0, 0, spec['TOP'])], width * 0.3, 4, mats['Iron'],
                              flat=0.5))
    return parts


def shackles(level):
    """Short chains from the top band's underside to iron cuffs on the prisoner's wrists."""
    parts = []
    if level >= 2:
        return parts
    joints = wrists()
    for side in ('l', 'r'):
        hand = Vector(joints[f'hand_{side}'])
        anchor = Vector((hand.x, hand.y, spec['top_band'][2] + 1))
        if level == 0:
            links, _ = hl.chain(f'shackle{side}', hand.z + 4, anchor.z, 9.0, 5.5, 1.1, 8, 3, mats['Iron'])
            for obj in links:
                obj.location = (u(hand.x), u(hand.y), 0); hl.apply(obj)
            parts += links
        else:
            parts.append(hl.sweep(f'shackle{side}', [hand + Vector((0, 0, 4)), anchor], 1.2, 3, mats['Iron']))
        cuff = [hand + Vector((math.cos(a) * 3.4, math.sin(a) * 3.4, 2)) for a in
                (2 * math.pi * k / 8 for k in range(8))]
        parts.append(hl.sweep(f'cuff{side}', cuff, 1.4, (4, 3)[level], mats['Iron'], closed=True, up=(0, 0, 1),
                              flat=1.6))
    return parts


lods = []
levels = 4
for level in range(levels):
    groups = cage(level)
    hl.tag(groups['bars'], spec['colours']['bars'])
    hl.tag(groups['bands'], spec['colours']['bands'])
    parts = groups['bars'] + groups['bands']
    if spec['top'] == 'straps':
        extra = hanger(level)
        hl.tag(extra, spec['colours']['bars'])
        parts += extra
    if spec['skeleton']:
        bones = [prisoner(level)]
        hl.tag(bones, spec['colours']['bone'])
        parts += bones
        if spec['shackles']:
            chains = shackles(level)
            hl.tag(chains, spec['colours']['bars'])
            parts += chains
    for obj in parts:
        hl.apply(obj)
    name = PROP.capitalize() if level == 0 else f'{PROP.capitalize()}_LOD{level}'
    solid = pl.join(name, parts)
    occlusion = pl.vertex_occlusion(solid, rays=(32, 20, 12, 8)[level], distance=u(30), strength=0.55, floor=False)
    hl.tint(solid, report=f'{PROP} L{level}')
    print('LEVEL', level, name, 'tris', pl.triangles(solid), 'mean occlusion', round(occlusion, 3))
    lods.append(solid)
lo, hi = pl.bounds(lods[:1])
print('BOUNDS', PROP, [round(v * hl.dl.UNITS_PER_METRE, 1) for v in lo], [round(v * hl.dl.UNITS_PER_METRE, 1)
                                                                         for v in hi])
os.makedirs(hl.WORK, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(hl.WORK, f'{PROP}.blend'))
pl.export(lods, os.path.join(hl.WORK, f'{PROP}_export.glb'))
