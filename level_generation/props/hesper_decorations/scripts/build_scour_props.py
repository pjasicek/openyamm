"""Build the Scour's hard-surface decorations (hes_out2) into work/hard_surface/.

    blender --background --factory-startup --python scripts/build_scour_props.py [-- <name> ...]

The new decorations of design/kreegan_world/zone2/THE_SCOUR.md (section 14, concept z2_05) that primitives can make,
textured with the Kreegan kits K5 (grafted resin, the collar sockets, the vent), K6 (the Ancient pier ceramic, the
belt) and K8 (the swarm ship's bone ribs and hull), in the shared hard-surface kit (build_hard_surface.py:
materials, UV density, export). Sizes are the design's (1 m = 100 world units):

  hes_fire_bowl_out, _off  a resin fire bowl on a stem (burning / cold coals)
  hes_ground_vent          a resin ring in the ground over a glowing fire vent
  hes_survey_marker        a broken Ancient survey post
  hes_conveyor_parts       a white roller and a belt segment lying on the ground
  hes_kcrate_chest         a Kreegan salvage crate (a chest)
  hes_duel_post            a bone post of camp 5's duelling ring
  hes_wreck_plates         white hull plates on bone trestles beside a resin cutting frame (camp 1)
  hes_spoil_heap           a heap of spoil rock and ore

The collar node, the Overseer's perch and the derelict's two hull halves were built here first; they are Meshy models
now (designs.json, the organic route; 2026-10-23, the user's review of the Scour).
"""
import math
import os
import random
import sys

import bpy
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_hard_surface as hs  # noqa: E402
from build_hard_surface import cone, cube, cylinder, faceted_rock  # noqa: E402

KITS = {'k5': os.path.join(hs.ART, 'textures_k5_grafted', 'masters'),
        'k6': os.path.join(hs.ART, 'textures_k6_foundry', 'masters'),
        'k8': os.path.join(hs.ART, 'textures_k8_ship', 'masters')}
for kit, names in {'k5': ['hokspine', 'hokwall', 'hkrib', 'hkvent', 'hkrock', 'hkore', 'hkglow'],
                   'k6': ['hompier', 'hmbelt', 'hmslag', 'hmgantry'],
                   'k8': ['hsrib']}.items():
    for name in names:
        hs.TEXTURES[name] = os.path.join(KITS[kit], name + '.png')
hs.MATERIALS.update({
    'spine': ('hokspine', 0.4, 0.0, 1.4), 'kwall': ('hokwall', 0.45, 0.0, 1.4), 'krib': ('hkrib', 0.4, 0.0, 1.2),
    'vent': ('hkvent', 0.5, 0.0, 1.2), 'rock': ('hkrock', 0.85, 0.0, 1.6), 'ore': ('hkore', 0.85, 0.1, 1.6),
    'pier': ('hompier', 0.55, 0.0, 1.0), 'belt': ('hmbelt', 0.8, 0.2, 1.2), 'slag': ('hmslag', 0.7, 0.2, 1.4),
    'gantry': ('hmgantry', 0.5, 0.4, 1.2),
    # Glowing: the fire's orange, the vent's molten core.
    'fire': ('flat_255_150_50', 0.5, 0.0, 0.0, (1.0, 0.55, 0.15)),
    'coals': ('flat_34_28_26', 0.9, 0.0, 0.0),
    'molten': ('flat_255_120_30', 0.4, 0.0, 0.0, (1.0, 0.45, 0.1)),
    'ivory': ('hsbone', 0.5, 0.0, 1.2),
})
# The swarm ship's bone: the ivory rib band of hsrib's left edge (master columns 8-88), mirrored beside itself so it
# tiles across; the ribs, the duelling posts and the trestles are made of it.
hs.TEXTURES['hsbone'] = os.path.join(hs.DERIVED, 'hsbone.png')


def bone_texture():
    path = hs.TEXTURES['hsbone']
    if os.path.exists(path):
        return
    os.makedirs(hs.DERIVED, exist_ok=True)
    image = bpy.data.images.load(hs.TEXTURES['hsrib'])
    w, h = image.size
    pixels = np.array(image.pixels[:], dtype=np.float32).reshape(h, w, 4)
    band = pixels[:, 8:88]
    tiled = np.concatenate([band, band[:, ::-1]], 1)
    out = bpy.data.images.new('hsbone', tiled.shape[1], h)
    out.pixels[:] = tiled.ravel()
    out.filepath_raw = path
    out.file_format = 'PNG'
    out.save()
    bpy.data.images.remove(image)


bone_texture()


def spine(radius0, radius1, height, location, key='spine', sides=10):
    """A tapering column standing on location."""
    x, y, z = location
    return cone(radius0, radius1, height, (x, y, z + height / 2), key, sides)


def fire_bowl(lit):
    """The perches' fire bowls (two at each perch's foot): a resin bowl on a short stem; burning, or cold coals."""
    cylinder(0.32, 0.08, (0, 0, 0.04), 'krib', 10)
    spine(0.14, 0.11, 0.5, (0, 0, 0.08), 'spine', 8)
    cone(0.16, 0.42, 0.28, (0, 0, 0.72), 'kwall', 12)
    cylinder(0.38, 0.05, (0, 0, 0.83), 'coals', 12)
    if lit:
        for k, (x, y, h) in enumerate([(0, 0, 0.5), (0.13, 0.06, 0.34), (-0.12, 0.08, 0.3), (0.02, -0.14, 0.32)]):
            hs.bipyramid(0.12 - k * 0.015, h, (x, y, 0.85 + h / 2), 'fire', 5)


def ground_vent():
    """A resin fire vent in the ground: a low ribbed ring round a glowing molten throat."""
    for k in range(10):
        a = k * 2 * math.pi / 10
        cone(0.2, 0.06, 0.55, (math.cos(a) * 0.62, math.sin(a) * 0.62, 0.2), 'spine', 6,
             rotation=(0, 0.45, a))
    hs.open_tube(0.62, 0.32, (0, 0, 0.16), 'vent', 14, bottom=False, thickness=0.12)
    cylinder(0.52, 0.04, (0, 0, 0.08), 'molten', 14)


def survey_marker():
    """A broken Ancient survey post: a white square post snapped off and leaning, its gold band and glyph plate."""
    cube((0.42, 0.42, 0.12), (0, 0, 0.06), 'ceramic')
    cube((0.24, 0.24, 0.95), (0, 0, 0.6), 'ceramic')
    cube((0.27, 0.27, 0.06), (0, 0, 0.8), 'trim')
    cube((0.16, 0.02, 0.2), (0, -0.13, 0.55), 'sign')
    cube((0.22, 0.22, 0.5), (0.18, 0.12, 0.2), 'ceramic', rotation=(0.0, 1.25, 0.4))


def conveyor_parts():
    """A white pier roller and a length of belt fallen off the conveyor."""
    cylinder(0.32, 1.7, (0, 0.55, 0.32), 'ceramic', 14, rotation=(0, math.pi / 2, 0.15))
    for side in (-0.88, 0.88):
        cylinder(0.12, 0.08, (side * math.cos(0.15), 0.55 + side * math.sin(0.15), 0.32), 'trim', 10,
                 rotation=(0, math.pi / 2, 0.15))
    cube((1.9, 0.75, 0.08), (0.1, -0.45, 0.04), 'belt', rotation=(0, 0, -0.1))
    cube((0.8, 0.75, 0.08), (0.95, -0.4, 0.22), 'belt', rotation=(0, -0.45, -0.1))


def kcrate_chest():
    """A Kreegan salvage crate (the depot's chests): resin-plated sides, bone bands, ore heaped in its open top."""
    cube((1.3, 0.85, 0.66), (0, 0, 0.33), 'kwall')
    for x in (-0.66, 0.66):
        cube((0.06, 0.9, 0.72), (x, 0, 0.36), 'krib')
    for x in (-0.3, 0.3):
        cube((0.1, 0.9, 0.7), (x, 0, 0.35), 'krib')
    faceted_rock(0.3, (-0.25, 0.05, 0.68), 'ore', 3, stretch=(1.3, 1.0, 0.5))
    faceted_rock(0.24, (0.3, -0.05, 0.66), 'ore', 5, stretch=(1.2, 1.0, 0.5))


def duel_post():
    """A bone post of the duelling ring: a long rib bone stood upright, a cross bone near its top."""
    cylinder(0.24, 0.1, (0, 0, 0.05), 'krib', 8)
    spine(0.13, 0.08, 2.1, (0, 0, 0.1), 'ivory', 8)
    cube((0.7, 0.11, 0.11), (0, 0, 1.85), 'ivory', rotation=(0.0, 0.12, 0.0))
    cone(0.09, 0.0, 0.28, (0, 0, 2.34), 'ivory', 8)


def wreck_plates():
    """Camp 1's cutting yard: white hull plates stacked on two bone trestles, and a resin cutting frame holding a
    plate half cut through."""
    for x in (-0.95, 0.95):
        for y in (-0.55, 0.55):
            cube((0.1, 0.1, 0.9), (x, y, 0.45), 'ivory')
        cube((0.12, 1.3, 0.1), (x, 0, 0.85), 'ivory')
    for k in range(4):
        cube((2.5 - 0.1 * k, 1.35, 0.07), (0.04 * k, 0.03 * k, 0.94 + 0.075 * k), 'hull', rotation=(0, 0, 0.03 * k))
    for x in (1.95, 3.25):
        spine(0.11, 0.08, 2.3, (x, 0, 0), 'spine', 8)
    cube((1.5, 0.12, 0.12), (2.6, 0, 2.25), 'krib')
    cube((1.1, 0.06, 1.5), (2.55, 0, 1.15), 'hull', rotation=(0, 0.08, 0))
    cube((0.3, 0.07, 1.6), (2.15, 0, 1.15), 'molten')


def spoil_heap():
    """A heap of crushed spoil and ore dumped by the carts: a low rounded mound of faceted rock."""
    rnd = random.Random(17)
    faceted_rock(1.5, (0, 0, 0.35), 'rock', 2, stretch=(1.25, 1.0, 0.55), subdivisions=2)
    for k in range(9):
        a = k * 2 * math.pi / 9 + rnd.uniform(-0.2, 0.2)
        r = rnd.uniform(1.1, 1.7)
        faceted_rock(rnd.uniform(0.35, 0.6), (math.cos(a) * r, math.sin(a) * r * 0.8, 0.1), 'ore' if k % 3 else 'rock',
                     11 + k, stretch=(1.2, 1.0, 0.6))


MODELS = {
    'hes_fire_bowl_out': lambda: fire_bowl(True), 'hes_fire_bowl_out_off': lambda: fire_bowl(False),
    'hes_ground_vent': ground_vent, 'hes_survey_marker': survey_marker, 'hes_conveyor_parts': conveyor_parts,
    'hes_kcrate_chest': kcrate_chest, 'hes_duel_post': duel_post, 'hes_wreck_plates': wreck_plates,
    'hes_spoil_heap': spoil_heap,
}

if __name__ == '__main__':
    hs.MODELS.update(MODELS)
    names = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else list(MODELS)
    for model in names:
        hs.build(model)
