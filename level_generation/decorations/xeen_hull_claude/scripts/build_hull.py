#!/usr/bin/env python3
"""Build the world rim's hull skirt (U-12, agent xeen-rim, 2026-11-23) straight to GLB: the Ancients' plating that
hangs from the land's edge into the void under every Xeen rim cliff, so the world reads as the ship it is.

One straight piece per width: a riveted plate (the kit's `xahull`, `xahullbn` burnt for D6) from just above the edge
down DEPTH, a coping strip along the top that covers the seam with the terrain, girder ribs, a band of running-light
ports (emissive, slow pulse) and a keel face sloping back under the land at the bottom; darker toward the bottom
(COLOR_0). Static, opaque, no collision; one-sided (only the void side is ever seen).

glTF axes: X across the edge, Y up, Z out over the void. The origin is the top of the plate on the edge line,
mid-width: place the decoration on the edge (the last land node line) at the void's height (0), `turn` so +Z points
over the void (common/rim.py does this: east 270, west 90, north 0, south 180).

Writes work/<name>.glb for every piece and work/report.json (the binding heights).
Usage: build_hull.py"""
import io
import json
import math
import struct
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[2]
TEXTURES = ROOT / 'level_generation/xeen_art/kit_textures/landmarks/finished'
UNITS_PER_METRE = 81.7

# The hull's profile (out over the void, up), from the coping on the land's last row out and down the flare (the deck
# of the ship, sloping 29 degrees so it shows from the cliff top), round the lip and back in under the land: a ship's
# side seen end-on. Each segment: (texture repeat along it, grey at its ends from shade_at).
# D-109 (agent xeen-rim3): the hull stands on the land's edge (the land runs level to it), its coping a kerb 150 proud
# of the grass with a row of running lights on its inland face, the face running on 400 into the ground (so a piece on
# land that falls away along it shows no gap); the deck flares out and down from the kerb's outer face.
PROFILE = [(-160, -400), (-160, 150), (64, 150), (64, -24), (40, -24), (1800, -1000), (1860, -1060), (1860, -1220),
           (1800, -1280), (900, -1980), (0, -2560), (-300, -2700)]
FLARE = 4             # the profile's point where the flare starts (flare_point)
KERB_LIGHT = (-160, 70)   # the inland running lights: on the kerb's inland face at this height
LIGHT_OUT = 1660      # running lights on the flare near its outer lip (seen from the cliff top), every PORT_STEP
TEXEL = 512.0         # units per texture repeat (1,024 px: two pixels a unit)
RIB_WIDTH, RIB_UP = 112, 56
PORT = (64, 40)       # a running-light port, across and along the flare
PORT_STEP = 256
PORT_GLOW = {'factor': [0.45, 0.88, 1.0], 'strength': 3.0, 'pulse': [0.45, 5.0]}
CORNER_STEPS = 6
# D-109/D-114 (agent xeen-rimmap-b, 2026-11-23): two deckless profiles. NOTCH: the kerb, then its face straight down
# (no flare), for the short walls of a notch in the rim (X7's lava cove), whose decks would close the notch. FACE: no
# kerb and no deck, a plain wall from the land's edge down, set back a little behind the edge, under a sand or lava fall
# (decorations pouring from the lip in front of it), so the fall's gap shows hull, not the land's slab and cut ends.
NOTCH_PROFILE = [(-160, -400), (-160, 150), (64, 150), (64, -2400), (0, -2560), (-300, -2700)]
FACE_PROFILE = [(-64, 0), (-16, 0), (-16, -2400), (-80, -2560), (-300, -2700)]
FACE_LIGHT_UP = -220    # a row of running lights on a deckless face, this far under the edge

PIECES = [
    {'name': 'xeen_deco_hull4', 'width': 2048, 'texture': 'xahull', 'ribs': [-512, 512]},
    {'name': 'xeen_deco_hull1', 'width': 512, 'texture': 'xahull', 'ribs': []},
    {'name': 'xeen_deco_hullc', 'corner': True, 'texture': 'xahull'},
    {'name': 'xeen_deco_hull4bn', 'width': 2048, 'texture': 'xahullbn', 'ribs': [-512, 512]},
    {'name': 'xeen_deco_hull1bn', 'width': 512, 'texture': 'xahullbn', 'ribs': []},
    {'name': 'xeen_deco_hullcbn', 'corner': True, 'texture': 'xahullbn'},
    {'name': 'xeen_deco_hull4n', 'width': 2048, 'texture': 'xahull', 'ribs': [-512, 512], 'profile': 'notch'},
    {'name': 'xeen_deco_hull1n', 'width': 512, 'texture': 'xahull', 'ribs': [], 'profile': 'notch'},
    {'name': 'xeen_deco_hullf', 'width': 512, 'texture': 'xahull', 'ribs': [], 'profile': 'face'},
    {'name': 'xeen_deco_hullfbn', 'width': 512, 'texture': 'xahullbn', 'ribs': [], 'profile': 'face'},
]


class Mesh:
    """Triangles with flat normals and per-vertex grey (COLOR_0)."""

    def __init__(self):
        self.positions, self.normals, self.uvs, self.colours, self.indices = [], [], [], [], []

    def poly(self, corners, uvs, greys, normal=None):
        """A convex polygon, corners counter-clockwise seen from its front (the normal from the first three when not
        given)."""
        corners = [np.array(c, np.float64) for c in corners]
        if normal is None:
            normal = np.cross(corners[1] - corners[0], corners[2] - corners[0])
        normal = np.array(normal, np.float64)
        normal = normal / np.linalg.norm(normal)
        base = len(self.positions)
        for corner, uv, grey in zip(corners, uvs, greys):
            self.positions.append(tuple(corner))
            self.normals.append(tuple(normal))
            self.uvs.append(uv)
            self.colours.append((grey, grey, grey, 1.0))
        for i in range(1, len(corners) - 1):
            self.indices.append((base, base + i, base + i + 1))

    def arrays(self):
        return (np.array(self.positions, np.float32), np.array(self.normals, np.float32),
                np.array(self.uvs, np.float32), np.array(self.colours, np.float32), np.array(self.indices))


def shade_at(y):
    """Lighter at the top (the deck in daylight), dark under the lip and the keel."""
    share = min(max(-y / 2600.0, 0.0), 1.0)
    return 1.0 - 0.6 * share


def profile_lengths(profile):
    lengths = [0.0]
    for a, b in zip(profile, profile[1:]):
        lengths.append(lengths[-1] + math.dist(a, b))
    return lengths


def flare_point(out):
    """(out, up) on the flare at this distance out, and the flare's unit normal (out, up)."""
    (o0, u0), (o1, u1) = PROFILE[FLARE], PROFILE[FLARE + 1]
    share = (out - o0) / (o1 - o0)
    d = np.array([o1 - o0, u1 - u0], np.float64)
    d /= np.linalg.norm(d)
    return (o0 + (o1 - o0) * share, u0 + (u1 - u0) * share), (-d[1], d[0]), d


def build_straight(piece, plate, ports):
    half = piece['width'] / 2.0
    lengths = profile_lengths(PROFILE)
    for (a, b), la, lb in zip(zip(PROFILE, PROFILE[1:]), lengths, lengths[1:]):
        # glTF: x across, y up, z out; corners counter-clockwise seen from the outer side.
        corners = [(half, a[1], a[0]), (-half, a[1], a[0]), (-half, b[1], b[0]), (half, b[1], b[0])]
        uvs = [(half / TEXEL, la / TEXEL), (-half / TEXEL, la / TEXEL), (-half / TEXEL, lb / TEXEL),
               (half / TEXEL, lb / TEXEL)]
        plate.poly(corners, uvs, [shade_at(a[1]), shade_at(a[1]), shade_at(b[1]), shade_at(b[1])])
    # End caps (the piece's cut ends, seen in a fall's gap): a fan from inside the profile.
    centre = (500, -1100)
    for side in (-1, 1):
        x = half * side
        ring = PROFILE + [PROFILE[0]]
        for a, b in zip(ring, ring[1:]):
            tri = [(x, centre[1], centre[0]), (x, a[1], a[0]), (x, b[1], b[0])]
            if side < 0:
                tri = [tri[0], tri[2], tri[1]]
            uvs = [(t[2] / TEXEL, -t[1] / TEXEL) for t in tri]
            plate.poly(tri, uvs, [0.4] * 3, normal=(side, 0, 0))
    # Ribs down the flare, raised RIB_UP over it.
    for rib in piece['ribs']:
        l, r = rib - RIB_WIDTH / 2, rib + RIB_WIDTH / 2
        (o0, u0), n, d = flare_point(PROFILE[FLARE][0] + 40)
        (o1, u1), _, _ = flare_point(PROFILE[FLARE + 1][0] - 30)
        lift = (n[0] * RIB_UP, n[1] * RIB_UP)
        top0, top1 = (o0 + lift[0], u0 + lift[1]), (o1 + lift[0], u1 + lift[1])
        g0, g1 = shade_at(u0) * 0.8, shade_at(u1) * 0.8
        length = math.dist((o0, u0), (o1, u1)) / TEXEL
        plate.poly([(r, top0[1], top0[0]), (l, top0[1], top0[0]), (l, top1[1], top1[0]), (r, top1[1], top1[0])],
                   [(r / TEXEL, 0), (l / TEXEL, 0), (l / TEXEL, length), (r / TEXEL, length)], [g0, g0, g1, g1])
        for x, sign in ((r, 1), (l, -1)):
            quad = [(x, u0, o0), (x, top0[1], top0[0]), (x, top1[1], top1[0]), (x, u1, o1)]
            if sign < 0:
                quad = quad[::-1]
            plate.poly(quad, [(0, 0), (0.1, 0), (0.1, length), (0, length)], [g0 * 0.8, g0 * 0.8, g1 * 0.8, g1 * 0.8],
                       normal=(sign, 0, 0))
    # Running lights on the flare near its lip.
    (o, u), n, d = flare_point(LIGHT_OUT)
    for x in np.arange(-half + PORT_STEP / 2, half, PORT_STEP):
        if any(abs(x - rib) < RIB_WIDTH for rib in piece['ribs']):
            continue
        px, pd = PORT[0] / 2, PORT[1] / 2
        lift = 3.0
        pts = []
        for ax, ad in ((px, -pd), (-px, -pd), (-px, pd), (px, pd)):
            pts.append((x + ax, u + d[1] * ad + n[1] * lift, o + d[0] * ad + n[0] * lift))
        ports.poly(pts, [(0, 0)] * 4, [1.0] * 4)
    # Running lights on the kerb's inland face, toward the land (seen from the grass).
    for x in np.arange(-half + PORT_STEP / 2, half, PORT_STEP):
        px, pd = PORT[0] / 2, PORT[1] / 2
        out, up = KERB_LIGHT[0] - 3.0, KERB_LIGHT[1]
        ports.poly([(x + ax, up + ad, out) for ax, ad in ((px, -pd), (-px, -pd), (-px, pd), (px, pd))],
                   [(0, 0)] * 4, [1.0] * 4, normal=(0, 0, -1))


def build_corner(piece, plate, ports):
    """The profile turned a quarter round the corner's vertical axis, centred on +Z (from -45 to +45 degrees): it fills
    the wedge between two straight runs meeting at a land corner. The inland part of the profile is clipped to the
    axis."""
    profile = [(max(o, 0.0), u) for o, u in PROFILE]
    lengths = profile_lengths(profile)
    angles = [math.radians(-45 + 90 * k / CORNER_STEPS) for k in range(CORNER_STEPS + 1)]

    def at(point, angle):
        r, up = point
        return (r * math.sin(angle), up, r * math.cos(angle))

    for a0, a1 in zip(angles, angles[1:]):
        for (a, b), la, lb in zip(zip(profile, profile[1:]), lengths, lengths[1:]):
            corners = [at(a, a0), at(a, a1), at(b, a1), at(b, a0)]
            if a[0] <= 0.0 and b[0] <= 0.0:
                continue
            if a[0] <= 0.0:
                corners = [corners[0], corners[2], corners[3]]
            elif b[0] <= 0.0:
                corners = corners[:3]
            arc0, arc1 = a0 * 1024 / TEXEL, a1 * 1024 / TEXEL
            uvs = [(arc0, la / TEXEL), (arc1, la / TEXEL), (arc1, lb / TEXEL), (arc0, lb / TEXEL)][:len(corners)]
            greys = [shade_at(c[1]) for c in corners]
            # counter-clockwise from outside: against the arc's direction (as the straight runs go toward -x)
            plate.poly(corners[::-1], uvs[::-1], greys[::-1])
    (o, u), n, d = flare_point(LIGHT_OUT)
    for k in range(3):
        angle = math.radians(-30 + 30 * k)
        px, pd = PORT[0] / 2, PORT[1] / 2
        pts = []
        for ax, ad in ((px, -pd), (-px, -pd), (-px, pd), (px, pd)):
            r = o + d[0] * ad + n[0] * 3.0
            up = u + d[1] * ad + n[1] * 3.0
            pts.append((r * math.sin(angle) + ax * math.cos(angle), up, r * math.cos(angle) - ax * math.sin(angle)))
        ports.poly(pts, [(0, 0)] * 4, [1.0] * 4)


def build_deckless(piece, plate, ports):
    """A straight piece on NOTCH_PROFILE or FACE_PROFILE: the plate, end caps, ribs down the face, running lights on
    the face (and on a notch piece's kerb, toward the land)."""
    profile = NOTCH_PROFILE if piece['profile'] == 'notch' else FACE_PROFILE
    half = piece['width'] / 2.0
    lengths = profile_lengths(profile)
    for (a, b), la, lb in zip(zip(profile, profile[1:]), lengths, lengths[1:]):
        corners = [(half, a[1], a[0]), (-half, a[1], a[0]), (-half, b[1], b[0]), (half, b[1], b[0])]
        uvs = [(half / TEXEL, la / TEXEL), (-half / TEXEL, la / TEXEL), (-half / TEXEL, lb / TEXEL),
               (half / TEXEL, lb / TEXEL)]
        plate.poly(corners, uvs, [shade_at(a[1]), shade_at(a[1]), shade_at(b[1]), shade_at(b[1])])
    centre = (-150, -1200)
    for side in (-1, 1):
        x = half * side
        ring = profile + [profile[0]]
        for a, b in zip(ring, ring[1:]):
            tri = [(x, centre[1], centre[0]), (x, a[1], a[0]), (x, b[1], b[0])]
            if side < 0:
                tri = [tri[0], tri[2], tri[1]]
            plate.poly(tri, [(t[2] / TEXEL, -t[1] / TEXEL) for t in tri], [0.4] * 3, normal=(side, 0, 0))
    face_out = max(o for o, _ in profile)
    top = -24 if piece['profile'] == 'notch' else -40
    for rib in piece['ribs']:
        l, r = rib - RIB_WIDTH / 2, rib + RIB_WIDTH / 2
        o, u0, u1 = face_out + RIB_UP, top, -2000
        length = (u0 - u1) / TEXEL
        plate.poly([(r, u0, o), (l, u0, o), (l, u1, o), (r, u1, o)],
                   [(r / TEXEL, 0), (l / TEXEL, 0), (l / TEXEL, length), (r / TEXEL, length)],
                   [shade_at(u0) * 0.8] * 2 + [shade_at(u1) * 0.8] * 2)
        for x, sign in ((r, 1), (l, -1)):
            quad = [(x, u0, face_out), (x, u0, o), (x, u1, o), (x, u1, face_out)]
            if sign < 0:
                quad = quad[::-1]
            plate.poly(quad, [(0, 0), (0.1, 0), (0.1, length), (0, length)], [0.5] * 4, normal=(sign, 0, 0))
    for x in np.arange(-half + PORT_STEP / 2, half, PORT_STEP):
        if any(abs(x - rib) < RIB_WIDTH for rib in piece['ribs']):
            continue
        px, pd = PORT[0] / 2, PORT[1] / 2
        ports.poly([(x + ax, FACE_LIGHT_UP + ad, face_out + 3.0) for ax, ad in ((-px, -pd), (px, -pd), (px, pd), (-px, pd))],
                   [(0, 0)] * 4, [1.0] * 4, normal=(0, 0, 1))
        if piece['profile'] == 'notch':
            out, up = KERB_LIGHT[0] - 3.0, KERB_LIGHT[1]
            ports.poly([(x + ax, up + ad, out) for ax, ad in ((px, -pd), (-px, -pd), (-px, pd), (px, pd))],
                       [(0, 0)] * 4, [1.0] * 4, normal=(0, 0, -1))


def build_piece(piece):
    plate, ports = Mesh(), Mesh()
    if piece.get('profile'):
        build_deckless(piece, plate, ports)
    elif piece.get('corner'):
        build_corner(piece, plate, ports)
    else:
        build_straight(piece, plate, ports)
    return plate, ports


class GlbWriter:
    def __init__(self):
        self.doc = {'asset': {'version': '2.0', 'generator': 'xeen_hull_claude build_hull.py'},
                    'buffers': [{'byteLength': 0}], 'bufferViews': [], 'accessors': [], 'images': [],
                    'textures': [], 'samplers': [], 'materials': [], 'meshes': [], 'nodes': [],
                    'scenes': [{'nodes': [0]}], 'scene': 0}
        self.binary = bytearray()

    def view(self, data, target=None):
        self.binary += b'\0' * (-len(self.binary) % 4)
        view = {'buffer': 0, 'byteOffset': len(self.binary), 'byteLength': len(data)}
        if target:
            view['target'] = target
        self.binary += data
        self.doc['bufferViews'].append(view)
        return len(self.doc['bufferViews']) - 1

    def accessor(self, array, kind, component, target, bounds=False):
        accessor = {'bufferView': self.view(np.ascontiguousarray(array).tobytes(), target),
                    'componentType': component, 'count': int(array.shape[0]), 'type': kind}
        if bounds:
            accessor['min'] = array.min(axis=0).tolist()
            accessor['max'] = array.max(axis=0).tolist()
        self.doc['accessors'].append(accessor)
        return len(self.doc['accessors']) - 1

    def texture(self, image):
        buffer = io.BytesIO()
        image.save(buffer, 'PNG', optimize=True)
        self.doc['images'].append({'bufferView': self.view(buffer.getvalue()), 'mimeType': 'image/png'})
        self.doc['samplers'].append({'magFilter': 9729, 'minFilter': 9987, 'wrapS': 10497, 'wrapT': 10497})
        self.doc['textures'].append({'source': len(self.doc['images']) - 1,
                                     'sampler': len(self.doc['samplers']) - 1})
        return len(self.doc['textures']) - 1

    def material(self, material):
        self.doc['materials'].append(material)
        return len(self.doc['materials']) - 1

    def primitive(self, mesh, material):
        positions, normals, uvs, colours, indices = mesh.arrays()
        return {'attributes': {
            'POSITION': self.accessor(positions / UNITS_PER_METRE, 'VEC3', 5126, 34962, bounds=True),
            'NORMAL': self.accessor(normals, 'VEC3', 5126, 34962),
            'TEXCOORD_0': self.accessor(uvs, 'VEC2', 5126, 34962),
            'COLOR_0': self.accessor(colours, 'VEC4', 5126, 34962)},
            'indices': self.accessor(indices.astype(np.uint16).ravel(), 'SCALAR', 5123, 34963),
            'material': material}

    def write(self, path, name, primitives):
        self.doc['meshes'].append({'name': name, 'primitives': primitives})
        self.doc['nodes'].append({'name': name, 'mesh': 0})
        self.binary += b'\0' * (-len(self.binary) % 4)
        self.doc['buffers'][0]['byteLength'] = len(self.binary)
        encoded = json.dumps(self.doc, separators=(',', ':')).encode()
        encoded += b' ' * (-len(encoded) % 4)
        path.write_bytes(struct.pack('<III', 0x46546c67, 2, 28 + len(encoded) + len(self.binary))
                         + struct.pack('<II', len(encoded), 0x4e4f534a) + encoded
                         + struct.pack('<II', len(self.binary), 0x004e4942) + bytes(self.binary))


def main():
    out = HERE / 'work'
    out.mkdir(parents=True, exist_ok=True)
    report = {}
    for piece in PIECES:
        plate, ports = build_piece(piece)
        writer = GlbWriter()
        image = Image.open(TEXTURES / (piece['texture'] + '.png')).convert('RGB')
        hull = writer.material({
            'name': 'Hull', 'pbrMetallicRoughness': {
                'baseColorTexture': {'index': writer.texture(image)}, 'baseColorFactor': [1, 1, 1, 1],
                'metallicFactor': 0.0, 'roughnessFactor': 0.6},
            'extras': {'openyamm_specular': 0.35}})
        glow = writer.material({
            'name': 'RunningLights', 'pbrMetallicRoughness': {
                'baseColorFactor': [0.08, 0.14, 0.16, 1], 'metallicFactor': 0.0, 'roughnessFactor': 0.4},
            'emissiveFactor': PORT_GLOW['factor'],
            'extensions': {'KHR_materials_emissive_strength': {'emissiveStrength': PORT_GLOW['strength']}},
            'extras': {'openyamm_pulse': PORT_GLOW['pulse']}})
        writer.doc['extensionsUsed'] = ['KHR_materials_emissive_strength']
        primitives = [writer.primitive(plate, hull)]
        if ports.indices:
            primitives.append(writer.primitive(ports, glow))
        else:
            writer.doc['materials'].pop()
        path = out / (piece['name'] + '.glb')
        writer.write(path, piece['name'], primitives)
        everything = np.concatenate([plate.arrays()[0]] + ([ports.arrays()[0]] if ports.indices else []))
        lo, hi = everything.min(axis=0), everything.max(axis=0)
        report[piece['name']] = {
            'width': piece.get('width', 'corner'), 'texture': piece['texture'], 'height_units': round(float(hi[1] - lo[1]), 2),
            'triangles': len(plate.indices) + len(ports.indices), 'path': str(path)}
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
