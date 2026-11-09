"""Blender: builds each Arena prop's decoration GLB (work/<prop>_export.glb, LOD objects <Prop>, <Prop>_LOD1,
...) and work/<prop>_meta.json with the Anskram Keep's build (../mm9_anskramkeep_claude/scripts/build.py, run here
with its paths pointed at this project and this project's PROPS): the isle's blib (asset frame = the raw import
mirrored in X, clean, faces wound to the ABC's authored normals, open pieces on a double-sided copy of the material,
smooth within 40 degrees, COLOR_0 occlusion, base centre at the origin), LODs from 1000 triangles (native ABC LOD when
its count is near, else a collapse decimation), flame cards of the shared CC0 flipbook.

Additions over the Anskram build, kept here: the tilted book has its placement pitch baked in (decorations turn about
z only; the isle's tilt_matrix), and a flame spec may name its own seat ('rim': the bowl's rim, for the hanging bowls,
whose top is the hook) instead of the top 12 % of the model; hung props (tapestries, hanging bowls) get their
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
exec(compile(source.rstrip()[:-len('main()')], ANSKRAM_BUILD, 'exec'), ns)
blib = ns['blib']
assert blib.HERE == str(props_table.HERE)

# Flame cards: (x offset, width, bottom, top, mirrored) in metres of the model before its placement scale, from the
# seat (the Anskram torch's cards for the floor brazier's small bowl; MM9 gives every brazier and torch the same
# FireScale 1 fire; the hanging bowls are placed at 0.75, so their cards are 1/0.75 larger and three across).
TORCH_FLAME = [(-0.03, 0.30, -0.05, 0.42, False), (0.04, 0.26, -0.05, 0.34, True)]
BOWL_FLAME = [(-0.09, 0.40, -0.05, 0.56, False), (0.10, 0.36, -0.05, 0.48, True), (0.0, 0.44, -0.05, 0.66, False)]
# The chandelier's four candles: MM9's Flame sockets (CHANDELIER3.abc nodes Flame..Flame4, LT from the model origin;
# raw GLB units (ABC x 2.56); the mesh spans y -1.44..57.36, x -67.18..66.35, z +-67.56), small cards on each wick.
CANDLE_FLAME = [(-0.015, 0.16, -0.02, 0.26, False), (0.02, 0.13, -0.02, 0.21, True)]
CHANDELIER_SOCKETS_LT = [(-50.86, 6.15, 0.0), (50.31, 6.15, 0.0), (-0.12, 10.16, 52.28), (-0.12, 10.16, -50.34)]
CHANDELIER_BOUNDS_LT = ((-67.18, -1.44, -67.56), (66.35, 57.36, 67.56))
LT_TO_M = 1 / 81.7          # the raw GLB holds the ABC model space x 2.56 (native units)
PROPS = {prop: {} for prop in props_table.built_props()}
PROPS['torchrust'] = {'flame': TORCH_FLAME, 'hung': True}    # the Ruined Temple's torchmetal (same torch2 ABC)
PROPS['tapestry_banner6'] = {'hung': True, 'alpha': True}     # Banner6's ragged edge is a cut-out
ns['PROPS'] = PROPS


def tilt_matrix(pitch, roll):
    """The transcoder's object rotation (about OpenYAMM x by pitch, then y by roll) in the asset frame, which is
    OpenYAMM turned half round z: D R D with D = diag(-1, -1, 1) (the isle's build)."""
    r = Matrix.Rotation(roll, 3, 'Y') @ Matrix.Rotation(pitch, 3, 'X')
    d = Matrix.Diagonal((-1, -1, 1))
    return (d @ r @ d).to_4x4()


_import_raw = blib.import_raw


def import_raw(path, name, origin, apply_armature=False, pose=None):
    obj = _import_raw(path, name, origin, apply_armature=apply_armature, pose=pose)
    prop = os.path.basename(os.path.dirname(path))
    prop = prop if prop in PROPS else os.path.basename(os.path.dirname(os.path.dirname(path)))   # lod<n>/
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


def socket_seats():
    """The chandelier's candle wicks in the asset frame (metres, base centre at the origin, z up): the sockets' LT
    offsets from the mesh's bounding-box centre (they sit symmetrically, so the frame's mirror and half turn do not
    move them by more than a few millimetres), heights above the mesh's lowest point."""
    lo, hi = np.array(CHANDELIER_BOUNDS_LT[0]), np.array(CHANDELIER_BOUNDS_LT[1])
    centre = (lo + hi) / 2
    return [((x - centre[0]) * LT_TO_M, (z - centre[2]) * LT_TO_M, (y - lo[1]) * LT_TO_M)
            for x, y, z in CHANDELIER_SOCKETS_LT]


def flame_cards(cards, head, uv_name):
    """The Anskram flame cards; a 'rim' seat is taken once from LOD0 (still named lod0 when its cards are made);
    'sockets' puts one set of cards on each candle (the chandelier)."""
    seat = PROPS[current['prop']].get('seat')
    if seat == 'rim':
        import bpy
        head = current.setdefault('seat', rim_seat(bpy.data.objects['lod0']))
    if seat == 'sockets':
        # MM9's sockets sit in the candle cups: each flame stands on the top of the candle above its socket (the
        # highest LOD0 vertex within 5 native units of the socket across).
        import bpy
        if 'seats' not in current:
            pts = np.array([v.co[:] for v in bpy.data.objects['lod0'].data.vertices])
            seats = []
            for x, y, _ in socket_seats():
                near = pts[np.hypot(pts[:, 0] - x, pts[:, 1] - y) < 5 * LT_TO_M]
                near = near[np.hypot(near[:, 0] - near[:, 0].mean(), near[:, 1] - near[:, 1].mean()) < 5 * LT_TO_M]
                seats.append((float(near[:, 0].mean()), float(near[:, 1].mean()), float(near[:, 2].max())))
            current['seats'] = seats
            print('CANDLE SEATS', [tuple(round(v * 81.7, 1) for v in s) for s in seats])
        parts = [_flame_cards(cards, h, uv_name) for h in current['seats']]
        return ns['join'](parts, 'Fire') if len(parts) > 1 else parts[0]
    return _flame_cards(cards, head, uv_name)


def occlusion(obj, distance, strength=0.6):
    blib.pl.vertex_occlusion(obj, rays=48, distance=distance, strength=strength,
                             floor=not PROPS[current['prop']].get('hung'))


def build(prop):
    current.clear()
    current['prop'] = prop
    return _build(prop)


def fix_closed_parts(obj):
    """Reverse the closed pieces whose volume is negative (the coffins' lid pins, a bone of the bone pile: the ABC's
    authored normals point in; check_winding.py refuses them)."""
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bm.faces.ensure_lookup_table()
    seen = set()
    for face in bm.faces:
        if face.index in seen:
            continue
        stack, piece = [face], []
        seen.add(face.index)
        while stack:
            current = stack.pop()
            piece.append(current)
            for edge in current.edges:
                for other in edge.link_faces:
                    if other.index not in seen:
                        seen.add(other.index)
                        stack.append(other)
        if any(len(e.link_faces) != 2 for f in piece for e in f.edges):
            continue
        volume = 0.0
        for f in piece:
            verts = [v.co for v in f.verts]
            for k in range(1, len(verts) - 1):
                volume += verts[0].dot(verts[k].cross(verts[k + 1]))
        if volume < 0.0:
            bmesh.ops.reverse_faces(bm, faces=piece)
    bm.to_mesh(obj.data)
    bm.free()


_smooth = blib.smooth


def smooth(obj, angle):
    fix_closed_parts(obj)
    return _smooth(obj, angle)


blib.smooth = smooth
ns['flame_cards'] = flame_cards
ns['build'] = build
blib.occlusion = occlusion
ns['main']()
