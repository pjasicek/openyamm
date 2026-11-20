"""Food bowl `foodbowl`: a wide pewter bowl on a low foot ring with a rolled lip (one lathe, outside and inside), heaped
with lumpy green-yellow porridge that rises a little above the rim (a polar grid displaced by noise lumps). Built
40 cm across; the sprite (54 x 32 units) is a high view of a shallow bowl, so bind it by width (see props/README.md).
Writes work/foodbowl_export.glb. Usage: blender --background --python build_foodbowl.py"""
import bpy, bmesh, math, os, sys
from mathutils import Vector, noise
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import props_lib as pl

pl.reset()
mats = {'Pewter': pl.material('Pewter', 'pewter'), 'Food': pl.material('Food', 'porridge')}
# outside from the base centre up to the lip, then the inside back down to the bowl floor
BOWL = [(0.0, 0.0), (0.110, 0.0), (0.122, 0.004), (0.126, 0.014), (0.118, 0.020), (0.140, 0.032), (0.165, 0.052),
        (0.185, 0.078), (0.198, 0.102), (0.204, 0.116), (0.201, 0.124), (0.193, 0.122), (0.186, 0.106),
        (0.168, 0.078), (0.140, 0.054), (0.090, 0.036), (0.0, 0.030)]
FOOD_R = 0.170                      # a heap in the middle: the inner wall shows round it


def food_height(x, y):
    r = math.hypot(x, y) / FOOD_R
    dome = 0.072 + 0.062 * max(0.0, 1 - r * r) ** 0.45
    lumps = (abs(noise.noise(Vector((x * 26, y * 26, 1.3)))) * 0.026
             + noise.noise(Vector((x * 70, y * 70, 4.1))) * 0.006)
    return dome + lumps * min(1.0, (1 - r) * 4)


def build(level):
    seg = (32, 18, 10)[level]
    profile = BOWL if level < 2 else [BOWL[i] for i in (0, 1, 3, 5, 7, 9, 11, 13, 15, 16)]
    if level == 1:
        profile = [BOWL[i] for i in (0, 1, 2, 3, 4, 6, 8, 9, 10, 11, 12, 14, 16)]
    parts = [pl.lathe('bowl', profile, seg, mats['Pewter'], u_repeat=2, v_scale=3)]
    rings, fseg = ((10, 32), (5, 16), (2, 8))[level]
    bm = bmesh.new(); uv = bm.loops.layers.uv.verify()
    centre = bm.verts.new((0, 0, food_height(0, 0)))
    grid = []
    for i in range(1, rings + 1):
        r = FOOD_R * (i / rings) ** 0.85
        row = []
        for s in range(fseg):
            a = 2 * math.pi * s / fseg
            x, y = r * math.cos(a), r * math.sin(a)
            z = food_height(x, y) if i < rings else 0.072
            row.append(bm.verts.new((x, y, z)))
        grid.append(row)
    for s in range(fseg):
        t = (s + 1) % fseg
        bm.faces.new((centre, grid[0][s], grid[0][t]))
        for i in range(rings - 1):
            bm.faces.new((grid[i][s], grid[i + 1][s], grid[i + 1][t], grid[i][t]))
    for f in bm.faces:
        for loop in f.loops:
            loop[uv].uv = (loop.vert.co.x / 0.08 + 0.5, loop.vert.co.y / 0.08 + 0.5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(pl.to_object('food', bm, mats['Food']))
    return pl.join(f'bowl{level}', parts)


lods = []
for level in range(3):
    obj = build(level)
    occl = pl.vertex_occlusion(obj, rays=(48, 24, 12)[level], distance=0.12, strength=0.65)
    obj.name = 'FoodBowl' if level == 0 else f'FoodBowl_LOD{level}'; obj.data.name = obj.name
    print('LEVEL', level, obj.name, 'tris', pl.triangles(obj), 'mean occlusion', round(occl, 3))
    lods.append(obj)
work = os.path.join(pl.PROPS, 'work')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(work, 'foodbowl.blend'))
pl.export(lods, os.path.join(work, 'foodbowl_export.glb'))
