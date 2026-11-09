"""MM6 cave stalagmites `stlmite1` (101 x 208), `stlmite2` (89 x 190) and `stlmite3` (137 x 210): limestone spires lathed
on the native silhouette. Each spire samples the sprite's opaque span row by row inside a column window (its centre
line and half width; the depth is 0.85 of the width), so the front view keeps the sprite's outline, lean and ledges;
smaller side spires come from their own windows. The surface is displaced by noise and by flowstone ledges that
bulge at the foot of every band, then cut at the ground. Texture: textures/dripstone (banded flowstone, drip
streaks), tinted to the native mean. LOD1 and LOD2 are collapse-decimated from LOD0.
Writes work/<prop>_export.glb. Usage: blender --background --python build_stalagmite.py -- stlmite1|2|3"""
import math
import os
import sys

import bmesh
from mathutils import Vector, noise

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crystals_lib as cl  # noqa: E402

pl = cl.pl
u = cl.u
PROP = sys.argv[sys.argv.index('--') + 1]

# Per sprite: native file, mean colour (sRGB), main spire as [(h from, h to, x2 column window)] and side spires as
# (h from, h to, window, depth offset y); heights in logical pixels, windows in x2 columns of the sprite.
SPIRES = {
    'stlmite1': {'file': 'stlmite1_p142.png', 'colour': (131.9, 110.8, 100.1),
                 'main': [(0, 208, (0, 202))], 'side': []},
    'stlmite2': {'file': 'stlmite2_p142.png', 'colour': (157.5, 130.2, 116.3),
                 'main': [(0, 54, (0, 178)), (56, 186, (66, 146))],
                 'side': [(48, 102, (28, 66), 10.0), (48, 78, (144, 172), -8.0), (100, 134, (120, 141), 6.0)]},
    'stlmite3': {'file': 'stlmite3_p142.png', 'colour': (130.8, 110.4, 100.0),
                 'main': [(0, 18, (0, 274)), (20, 78, (0, 234)), (80, 210, (76, 202))],
                 'side': [(12, 38, (234, 274), -6.0), (72, 98, (36, 76), 8.0)]},
}
DEPTH = 0.85
SEGMENTS = 26
UV_AROUND, UV_ALONG = 2.0, 1.5       # texture repeats around and per metre up the spire


def spire(name, samples, mat, y_offset, segments, seed):
    """Lathe through the sampled rings (centre x, half width), closed at the top by an apex."""
    bm = bmesh.new()
    uv = bm.loops.layers.uv.verify()
    bottom_h = samples[0][0]
    # Sink the foot below its first sample (the ground cut removes what is under z = 0).
    samples = [(bottom_h - 4, samples[0][1], samples[0][2] * 1.03)] + samples
    rings = []
    length = 0.0
    lengths = []
    previous = None
    for h, cx, hw in samples:
        centre = Vector((cx, y_offset, h))
        if previous is not None:
            length += (centre - previous).length
        previous = centre
        lengths.append(length)
        frac = (h / 7.0 + 0.37 * seed + 0.3 * noise.noise(Vector((h * 0.05, seed, 0.5)))) % 1.0
        ledge = 0.13 * (1 - frac) ** 3
        ring = []
        for s in range(segments):
            a = 2 * math.pi * s / segments
            n = noise.noise(Vector((math.cos(a) * 1.4 + seed, math.sin(a) * 1.4, h * 0.07)))
            n2 = noise.noise(Vector((math.cos(a) * 4.0 + seed, math.sin(a) * 4.0, h * 0.2)))
            ribs = 0.05 * math.sin(a * 9 + 2.0 * n + seed)         # drip columns down the flanks
            r = hw * (1 + 0.13 * n + 0.07 * n2 + ribs + ledge)
            ring.append(bm.verts.new((u(cx + r * math.cos(a)), u(y_offset + r * DEPTH * math.sin(a)), u(h))))
        rings.append(ring)
    top = samples[-1]
    apex = bm.verts.new((u(top[1]), u(y_offset), u(top[0] + max(1.5, top[2] * 0.6))))
    for i in range(len(rings) - 1):
        for s in range(segments):
            s2 = (s + 1) % segments
            f = bm.faces.new((rings[i][s], rings[i][s2], rings[i + 1][s2], rings[i + 1][s]))
            for loop, (a, b) in zip(f.loops, ((s, i), (s + 1, i), (s + 1, i + 1), (s, i + 1))):
                loop[uv].uv = (a / segments * UV_AROUND, u(lengths[b]) * UV_ALONG)
    for s in range(segments):
        s2 = (s + 1) % segments
        f = bm.faces.new((rings[-1][s], rings[-1][s2], apex))
        for loop, (a, b) in zip(f.loops, ((s / segments * UV_AROUND, u(lengths[-1]) * UV_ALONG),
                                          (s2 / segments * UV_AROUND, u(lengths[-1]) * UV_ALONG),
                                          ((s + 0.5) / segments * UV_AROUND, u(lengths[-1] + 2) * UV_ALONG))):
            loop[uv].uv = (a, b)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return cl.bright(pl.to_object(name, bm, mat, smooth=True))


def patches(co, name):
    """Large light and dark patches (the sprite's pale calcite faces and deep shadowed crevices)."""
    n = noise.noise(Vector((co.x * 9.0, co.y * 9.0, co.z * 5.0)))
    return max(0.2, 1.0 + 0.9 * n)


def main():
    pl.reset()
    spec = SPIRES[PROP]
    mat = cl.material('Dripstone', 'dripstone', extras={'openyamm_specular': 0.3})
    tints = {'Dripstone': cl.tint_for(mat, spec['colour'])}
    print('TINTS', tints)
    alpha = cl.sprite_alpha(spec['file'])
    parts = []
    samples = []
    for h0, h1, window in spec['main']:
        samples += cl.silhouette(alpha, window, h0, h1, 5)
    parts.append(spire('main', samples, mat, 0.0, SEGMENTS, 0))
    for i, (h0, h1, window, y) in enumerate(spec['side']):
        parts.append(spire(f'side{i}', cl.silhouette(alpha, window, h0, h1, 4), mat, y, 12, i + 1))
    base = pl.join('base', parts)
    cl.clip_ground(base)
    lods = []
    for level, target in enumerate((None, 1000, 300)):
        obj = base.copy()
        obj.data = base.data.copy()
        obj.parent = None
        base.users_collection[0].objects.link(obj)
        if target:
            pl.decimate_to(obj, target)
        name = PROP.capitalize() if level == 0 else f'{PROP.capitalize()}_LOD{level}'
        lods.append(cl.finish_lod(obj, name, (40, 24, 12)[level], u(18), 0.55, tints, patches, floor=True))
    base.users_collection[0].objects.unlink(base)
    cl.save_and_export(PROP, lods)


main()
