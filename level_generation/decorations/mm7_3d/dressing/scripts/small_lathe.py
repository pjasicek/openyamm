"""Lathe-turned small props, profiles measured on the x2 sprites (small_measure.py; map units, base on the ground):
- `7dec46` gold goblet (46 high): wide foot, knopped stem, a bowl rounded below and straight-walled above a bead,
  open with an inner wall and floor;
- `dec97` vase (66 high): small foot, egg-shaped body widest at 53 %, a narrow neck at 80 % and a flared bell
  mouth, open down into the neck.
Each profile point carries the last LOD that keeps it; segments per LOD. Metal (quality pass, 2026-10-16): the
small_metal.py sets (metallic clean metal, rougher tarnish or rust, varied roughness), u once around and v along the
profile. COLOR_0 = vertex occlusion (crevice grime: inside the cup, under the bead and rim, the foot's joints) x the
tint that brings the DUNGEON display to the sprite's mean: indoor decorations are lit diffuse only (base x
(1 - metallic); fs_model.sc, IndoorRenderer.cpp IndoorDecorationReflection), so the tint is fitted to the effective
albedo base x (1 - metallic), not to the base colour. Writes work/<prop>.blend and
work/<prop>_export.glb. Usage: blender --background --python small_lathe.py -- <prop>"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dlib  # noqa: E402
import numpy as np  # noqa: E402

pl, hl, u = dlib.pl, dlib.hl, dlib.u
PROP = sys.argv[sys.argv.index('--') + 1]

import small_profiles as sp  # noqa: E402

# Dungeon targets: the sprites' mean colours. Textures: small_lathe_compose.py (the sprite's own value ramp baked
# from the profile's convexity, facing and depth; quality pass round 2).
SPECS = {
    '7dec46': {'texture': 'misc_7dec46_baked', 'target': (94, 87, 57), 'segments': (24, 12, 8)},
    'dec97': {'texture': 'misc_dec97_baked', 'target': (84, 81, 66), 'segments': (36, 18, 10)},
}
for _prop, _spec in SPECS.items():
    _spec['profile'] = sp.PROFILES[_prop]
    _spec['neutral'] = True
spec = SPECS[PROP]


def effective_mean(texture):
    """Linear mean of base colour x (1 - metallic) over the texture (small_metal.py writes it): what the dungeon
    shows of the albedo."""
    import json
    return np.array(json.load(open(os.path.join(dlib.TEXTURES, 'misc_metal_means.json')))[texture], np.float32)


def tint_effective(obj, target, texture, report):
    """COLOR_0 = occlusion x linear(target) / effective mean / mean occlusion (clamped at one)."""
    me = obj.data
    colour = me.color_attributes['Color']
    occ = np.empty(len(me.vertices) * 4, np.float32); colour.data.foreach_get('color', occ); occ = occ.reshape(-1, 4)
    lin = np.array([hl.srgb_to_linear(t) for t in target], np.float32)
    factor = lin / effective_mean(texture) / float(occ[:, 0].mean())
    if spec.get('neutral'):
        # one grey factor (the luminance ratio): the texture's metal and tarnish colours carry the hue
        luma = np.array([0.2126, 0.7152, 0.0722], np.float32)
        factor = np.full(3, float(lin @ luma / (effective_mean(texture) @ luma) / occ[:, 0].mean()), np.float32)
    occ[:, :3] = np.clip(occ[:, :3] * factor, 0, 1)
    colour.data.foreach_set('color', occ.ravel())
    print('TINT', report, 'factor', np.round(factor, 3).tolist(), 'clipped', round(float((occ[:, :3] >= 1).mean()), 3))


pl.reset()
mat = dlib.material('Body', spec['texture'], extras={'openyamm_specular': 1.0})


def lathe(name, points, segments, mat):
    """Surface of revolution of points [(radius, z, v), ...] (metres; v the LOD0 arc fraction), u once around."""
    import bmesh
    bm = bmesh.new(); uvl = bm.loops.layers.uv.verify()
    rings = [[bm.verts.new((r * np.cos(2 * np.pi * k / segments), r * np.sin(2 * np.pi * k / segments), z))
              for k in range(segments)] for r, z, _ in points]
    for i in range(len(points) - 1):
        for k in range(segments):
            k2 = (k + 1) % segments
            f = bm.faces.new((rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]))
            for loop, (a, b) in zip(f.loops, ((k, i), (k + 1, i), (k + 1, i + 1), (k, i + 1))):
                loop[uvl].uv = (a / segments, points[b][2])
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    return pl.to_object(name, bm, mat, True)


lods = []
arc, _ = sp.arc_v(spec['profile'])
for level, segments in enumerate(spec['segments']):
    points = [(u(r), u(z), arc[i]) for i, (r, z, keep) in enumerate(spec['profile']) if keep >= level]
    obj = lathe('Base' if level == 0 else f'Base_LOD{level}', points, segments, mat)
    # crevice grime, softer than before: the texture carries the crevices and inner bowl
    pl.vertex_occlusion(obj, rays=(48, 24, 12)[level], distance=u(20), strength=0.45, floor=True)
    tint_effective(obj, spec['target'], spec['texture'], f'{PROP} L{level}')
    lods.append(obj)
dlib.save(PROP, lods)
