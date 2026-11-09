"""Burned-out fire dec24x (7dec24x, outdoor, still): a stack of five unburnt-looking logs, as the native frame shows it
(no ash, no embers): two long logs lying across, a shorter one in front, one behind on the right and one on top
crossing them, its near end showing the cut end grain. Traced from the restored native frame (x2 pixels at 0.5
units: 64 wide, 28 tall). Writes work/burnedfire_export.glb.
Variant `lit`: the lit signal fire v77dec24 (7dec24a-g, which the 7out02 Signal Fire Pit events switch dec24x to):
the same logs, byte for byte the same geometry and colours, plus a glowing ember bed (openyamm_flicker) between
them, a centre card of the shared flame02 flipbook sized like the sprite's flame (x -23..15, base about 11, tips up
to 51 units), two off-axis cards (openyamm_billboard "card", other flipbook frames) for a fuller fire and a soft
additive halo. Writes work/litfire_export.glb.
Usage: blender --background --python build_burnedfire.py [-- lit]"""
import math
import os
import random
import sys

import bmesh
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import firelib as fl  # noqa: E402

pl = fl.pl
LIT = '--' in sys.argv and sys.argv[sys.argv.index('--') + 1:][:1] == ['lit']
pl.reset()
bark = fl.material('Bark', 'bark', extras={'openyamm_specular': 0.3})
end = fl.material('End', 'endgrain', extras={'openyamm_specular': 0.2})

# (centre x, y, z, length, radius, yaw degrees, pitch degrees) in units; x across the view, y away from it.
LOGS = [(-7.0, -3.0, 6.2, 50.0, 6.2, 2.0, 0.0),        # long front-left log
        (12.0, -13.0, 5.4, 34.0, 5.4, -4.0, 3.0),      # front log, low
        (18.5, 7.0, 5.8, 29.0, 5.8, 8.0, 0.0),         # back right log (end grain to the right)
        (-23.0, 10.0, 9.0, 22.0, 6.0, 80.0, -8.0),     # back left log, end toward the viewer
        (-4.0, 0.5, 17.0, 42.0, 6.3, 22.0, -4.0)]      # top log across them (near-left end grain)


def log(index, spec, level):
    cx, cy, cz, length, radius, yaw, pitch = spec
    sides = (12, 7, 5)[level]
    rings = (4, 2, 2)[level]
    rng = random.Random(index * 7 + 1)
    wobble = [1.0 + rng.uniform(-0.08, 0.08) for _ in range(sides)]
    bm = bmesh.new()
    uv = bm.loops.layers.uv.verify()
    grid = []
    for j in range(rings):
        t = j / (rings - 1)
        x = (t - 0.5) * length
        sag = math.sin(t * math.pi) * radius * 0.06 * (1 if index % 2 else -1)
        ring = []
        for i in range(sides):
            a = 2 * math.pi * i / sides
            r = radius * wobble[i] * (1.0 - 0.06 * abs(t - 0.5))
            ring.append(bm.verts.new((fl.u(x), fl.u(r * math.cos(a) + sag), fl.u(r * math.sin(a)))))
        grid.append(ring)
    circumference = 2 * math.pi * fl.u(radius)
    for j in range(rings - 1):
        for i in range(sides):
            i2 = (i + 1) % sides
            face = bm.faces.new((grid[j][i], grid[j][i2], grid[j + 1][i2], grid[j + 1][i]))
            face.material_index = 0
            for loop, (s, k) in zip(face.loops, ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))):
                # Bark grain runs along the log (texture v); u wraps the circumference at the texture's density.
                loop[uv].uv = (s / sides * circumference * 2.0, k / (rings - 1) * fl.u(length) * 2.0)
    for j, flip in ((0, True), (rings - 1, False)):
        ring = list(reversed(grid[j])) if flip else grid[j]
        face = bm.faces.new(ring)
        face.material_index = 1
        for loop in face.loops:
            co = loop.vert.co
            loop[uv].uv = (0.5 + co.y / fl.u(radius) * 0.5 * (-1 if flip else 1), 0.5 + co.z / fl.u(radius) * 0.5)
    rotation = Matrix.Rotation(math.radians(yaw), 4, 'Z') @ Matrix.Rotation(math.radians(pitch), 4, 'Y')
    bmesh.ops.transform(bm, matrix=Matrix.Translation(Vector([fl.u(cx), fl.u(cy), fl.u(cz)])) @ rotation,
                        verts=bm.verts)
    obj = pl.to_object(f'log{index}', bm, bark, smooth=True)
    obj.data.materials.append(end)
    return obj


if LIT:
    flame = fl.flame_material('Flame', 'orange')
    cards = {name: fl.flame_card_material(name, 'orange') for name in ('FlameA', 'FlameB')}
    halo = fl.halo_material('Halo')
    glow = fl.glow_material('Glow', 'ember_orange', (170, 72, 22), extras={'openyamm_flicker': [0.4, 7.0]})
# Ember bed under the top log, centred on the native flame (x -4).
BED = [(12, 5.0), (9, 8.5), (5, 10.5), (0, 11.2)]


def build(level):
    logs = [log(i, spec, level) for i, spec in enumerate(LOGS)]
    if not LIT:
        return logs, []
    bed = fl.lathe('bed', BED, (12, 8, 6)[level], glow, u_repeat=2, v_scale=4)
    bed.location.x = fl.u(-4.0)
    whites = fl.apply([bed])
    whites.append(fl.glow_card('halo', halo, 32.0, 72.0, 38.0, x=-4.0))
    whites.append(fl.flame_card('flame', flame, 10.5, 51.0, 50.0, x=-4.0))
    if level < 2:
        whites.append(fl.flame_card('flamea', cards['FlameA'], 11.0, 42.0, 34.0, x=-9.0, y=-5.0, mirrored=True,
                                    shift=6))
        whites.append(fl.flame_card('flameb', cards['FlameB'], 11.5, 45.0, 32.0, x=2.0, y=5.0, shift=11))
    return logs, whites


# Native colours (7dec24x): dark brown bark with pale grey-tan patches, red-orange end grain.
colours = {'Bark': lambda co, n: (102, 64, 32) if n.z > -0.3 else (56, 35, 19), 'End': (150, 66, 34)}
if LIT:
    # The native flame is a deeper orange than the torch flame (linear 1 : 0.24 : 0.02 against 1 : 0.49 : 0.05);
    # a gentler shift keeps its bright core.
    colours['Flame'] = colours['FlameA'] = colours['FlameB'] = ('mul', (0.95, 0.6, 0.55))
    colours['Halo'] = ('mul', (0.5, 0.2, 0.05))
fl.build_lods('LitFire' if LIT else 'BurnedFire', 'litfire' if LIT else 'burnedfire', build, colours,
              rays=(32, 20, 12), distance=10.0, strength=0.6, sharp=50,
              last=('Glow', 'Halo', 'Flame', 'FlameA', 'FlameB') if LIT else ())
