"""Blender: builds each Verhoffin Ruins prop's decoration GLB (work/<prop>_export.glb, LOD objects <Prop>, <Prop>_LOD1,
...) and work/<prop>_meta.json with the Anskram Keep's build (../mm9_anskramkeep_claude/scripts/build.py, run here
with its paths pointed at this project and this project's PROPS): the isle's blib (asset frame = the raw import
mirrored in X, clean, faces wound to the ABC's authored normals, open pieces on a double-sided copy of the material,
smooth within 40 degrees, COLOR_0 occlusion, base centre at the origin), LODs from 1000 triangles (native ABC LOD when
its count is near, else a collapse decimation), flame cards of the shared CC0 flipbook.

Additions over the Anskram build, kept here: the tilted book has its placement pitch baked in (decorations turn about
z only; the isle's tilt_matrix), and a flame spec may name its own seat ('rim': the bowl's rim, for the hanging bowls,
whose top is the hook; or a point: the sconce's crown) instead of the top 12 % of the model; hung props (tapestries, hanging bowls) get their
vertex occlusion without blib's floor.
Usage: blender --background --python build.py -- [prop ...]"""
import math
import os
import sys

import numpy as np
from mathutils import Matrix

SCRIPTS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPTS)
import props_table  # noqa: E402

ANSKRAM_BUILD = os.path.join(str(props_table.ANSKRAM), 'scripts', 'build.py')
with open(ANSKRAM_BUILD) as stream:
    source = stream.read()
assert source.rstrip().endswith('\nmain()')
ns = {'__file__': os.path.join(SCRIPTS, 'build.py'), '__name__': 'anskram_build'}
# A flame spec may name its own flipbook texture (the pentagram's coloured fires).
source = source.replace("blib.texture_material('Fire', 'flame02_basecolor.png', alpha=True)",
                        "blib.texture_material('Fire', spec.get('texture', 'flame02_basecolor.png'), alpha=True)")
exec(compile(source.rstrip()[:-len('main()')], ANSKRAM_BUILD, 'exec'), ns)
blib = ns['blib']
assert blib.HERE == str(props_table.HERE)

# Flame cards: (x offset, width, bottom, top, mirrored) in metres of the model before its placement scale, from the
# seat (the Anskram torch's cards; MM9 gives every torch the same FireScale 1 fire).
TORCH_FLAME = [(-0.03, 0.30, -0.05, 0.42, False), (0.04, 0.26, -0.05, 0.34, True)]
BOWL_FLAME = [(-0.09, 0.40, -0.05, 0.56, False), (0.10, 0.36, -0.05, 0.48, True), (0.0, 0.44, -0.05, 0.66, False)]
PROPS = {prop: {} for prop in props_table.built_props()}
# The torture chamber's two wall sconces (MM9 Torch objects, Fire 1, FireScale 1): the Anskram torch's flame cards on
# the head (the top 12 % of the model unless build_check below finds otherwise).
PROPS['sconce1'] = {'flame': TORCH_FLAME, 'hung': True}
PROPS['minelantern'] = {'hung': True}
# The pentagram's five fires (MM9 Fire objects PentaFire1-5, FireScale 2, off until the puzzle starts): flame cards
# only, standing on the floor, each in its FireColor1 (scripts/pentafire_textures.py); their colours spell the order.
PENTA_FLAME = [(-0.05, 0.36, 0.0, 0.55, False), (0.06, 0.30, 0.0, 0.45, True)]
for colour in props_table.PENTAFIRES:
    PROPS[f'pentafire_{colour}'] = {'flame_only': True, 'flame': PENTA_FLAME, 'texture': f'flame_{colour}_basecolor.png'}
PROPS['manacles'] = {'hung': True, 'lods': False}   # its decimated LOD2 loses the plate
PROPS['skeletondebris03'] = {'lods': False}   # its decimated LOD chain inverts a closed part (check_winding)
ns['PROPS'] = PROPS


def tilt_matrix(pitch, roll):
    """The transcoder's object rotation (about OpenYAMM x by pitch, then y by roll) in the asset frame, which is
    OpenYAMM turned half round z: D R D with D = diag(-1, -1, 1) (the isle's build)."""
    r = Matrix.Rotation(roll, 3, 'Y') @ Matrix.Rotation(pitch, 3, 'X')
    d = Matrix.Diagonal((-1, -1, 1))
    return (d @ r @ d).to_4x4()


_import_raw = blib.import_raw


def import_raw(path, name, origin, apply_armature=False, pose=None):
    prop = os.path.basename(os.path.dirname(path))
    prop = prop if prop in PROPS else os.path.basename(os.path.dirname(os.path.dirname(path)))   # lod<n>/
    if prop in props_table.POSES:
        apply_armature, pose = True, props_table.POSES[prop]
    obj = _import_raw(path, name, origin, apply_armature=apply_armature, pose=pose)
    if prop in props_table.BOOK_TILT:
        obj.data.transform(tilt_matrix(*props_table.BOOK_TILT[prop]))
    return obj


blib.import_raw = import_raw
# deforming pieces (work/raw/<prop>/mode.txt 'full': the book) are baked in their bind pose
for name in PROPS:
    mode = os.path.join(blib.WORK, 'raw', name, 'mode.txt')
    if os.path.exists(mode) and open(mode).read().strip() == 'full':
        PROPS[name]['armature'] = True

_flame_cards = ns['flame_cards']
_build = ns['build']
current = {}


def rim_seat(obj):
    """The bowl's rim: centre of the footprint, height of the widest ring of vertices (asset frame, metres)."""
    pts = np.array([v.co[:] for v in obj.data.vertices])
    centre = (pts[:, :2].min(0) + pts[:, :2].max(0)) / 2
    radial = np.linalg.norm(pts[:, :2] - centre, axis=1)
    ring = pts[radial >= 0.92 * radial.max()]
    return float(centre[0]), float(centre[1]), float(ring[:, 2].mean())


def flame_cards(cards, head, uv_name):
    """The Anskram flame cards on the seat: an explicit point, or a 'rim' taken once from LOD0 (still named lod0 when
    its cards are made)."""
    seat = PROPS[current['prop']].get('seat')
    if seat == 'rim':
        import bpy
        head = current.setdefault('seat', rim_seat(bpy.data.objects['lod0']))
    elif seat is not None:
        head = seat
    return _flame_cards(cards, head, uv_name)


def occlusion(obj, distance, strength=0.6):
    blib.pl.vertex_occlusion(obj, rays=48, distance=distance, strength=strength,
                             floor=not PROPS[current['prop']].get('hung'))


def build(prop):
    current.clear()
    current['prop'] = prop
    return _build(prop)


ns['flame_cards'] = flame_cards
ns['build'] = build
blib.occlusion = occlusion
ns['main']()
