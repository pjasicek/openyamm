"""Flag `fla3__01`: a wooden pole at the origin (the sprite's anchor) with a red triangular pennant near its top,
traced from the sprite (250 x 256 units -> 3.9 x 4.0 m). The pennant is a subdivided grid, material Cloth (double-
sided, openyamm_flutter FLUTTER metres): texture coordinate u runs 0 at the pole -> 1 at the tip, and the 'Color'
alpha (glTF COLOR_0.a, the engine's flutter weight) rises from 0 at the pole to 1 at the tip. Writes
work/flag_export.glb.
Variant `flag1` (`fla1__01`, 2026-10-09): the same pole with a blue pennant laced to it through seven steel rings along
its edge (traced from its sprite: same 250 x 256-unit frame). Writes work/flag1_export.glb.
Usage: blender --background --python build_flag.py [-- flag1]"""
import bpy, bmesh, math, os, sys
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import props_lib as pl

VARIANTS = {
    'flag': {'name': 'Flag', 'cloth': 'cloth', 'attach_x': 0.045, 'top': 3.55, 'bottom': 2.35, 'tip': (1.85, 2.80),
             'rings': 0},
    'flag1': {'name': 'Flag1', 'cloth': 'bluecloth', 'attach_x': 0.12, 'top': 3.61, 'bottom': 2.27,
              'tip': (1.95, 2.77), 'rings': 7},
}
variant = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'flag'
spec = VARIANTS[variant]
pl.reset()
FLUTTER = 0.1
POLE_TOP = 4.0
ATTACH_TOP, ATTACH_BOTTOM = spec['top'], spec['bottom']        # pennant along the pole
ATTACH_X = spec['attach_x']
TIP = Vector((spec['tip'][0], 0.0, spec['tip'][1]))
mats = {'Wood': pl.material('Wood', 'wood'),
        'Cloth': pl.material('Cloth', spec['cloth'], extras={'openyamm_flutter': FLUTTER})}
if spec['rings']:
    mats['Steel'] = pl.material('Steel', 'steel'); mats['Leather'] = pl.material('Leather', 'leather')


def pennant(level):
    columns, rows = ((8, 4), (4, 2), (2, 1))[level]
    bm = bmesh.new(); uv = bm.loops.layers.uv.verify()
    grid = []
    for i in range(columns + 1):
        u = i / columns
        row = []
        for j in range(rows + 1):
            w = j / rows
            attach = Vector((ATTACH_X, 0.0, ATTACH_TOP + (ATTACH_BOTTOM - ATTACH_TOP) * w))
            p = attach.lerp(TIP, u)
            p.y += 0.08 * math.sin(u * math.pi * 1.5) * u        # a little resting curl
            row.append((bm.verts.new(p), u, w))
        grid.append(row)
    for i in range(columns):
        for j in range(rows):
            quad = (grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1])
            f = bm.faces.new([q[0] for q in quad])
            for loop, (_, u, w) in zip(f.loops, quad):
                loop[uv].uv = (u, w)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)           # the tip column collapses to one point
    obj = pl.to_object(f'pennant{level}', bm, mats['Cloth'])
    # flutter weight: 0 at the pole (x = 0.045) -> 1 at the tip
    pl.white_colour(obj, alpha=lambda co: max(0.0, min(1.0, (co.x - ATTACH_X) / (TIP.x - ATTACH_X))) ** 0.9)
    return obj


def rings(level):
    """Steel rings through the pennant's edge, each laced to the pole with a leather cord (LOD0 and LOD1 only)."""
    parts = []
    for k in range(spec['rings']):
        z = ATTACH_TOP + (ATTACH_BOTTOM - ATTACH_TOP) * (k + 0.5) / spec['rings']
        segments = (8, 4)[level]
        bm = bmesh.new(); uv = bm.loops.layers.uv.verify()
        grid = []
        for i in range(segments):
            t = 2 * math.pi * i / segments
            centre = Vector((ATTACH_X + math.cos(t) * 0.035, 0.0, z + math.sin(t) * 0.035))
            out = Vector((math.cos(t), 0.0, math.sin(t)))
            grid.append([bm.verts.new(centre + (out * math.cos(2 * math.pi * j / 3)
                                                + Vector((0, 1, 0)) * math.sin(2 * math.pi * j / 3)) * 0.008)
                         for j in range(3)])
        for i in range(segments):
            for j in range(3):
                nxt = grid[(i + 1) % segments]
                f = bm.faces.new((grid[i][j], grid[i][(j + 1) % 3], nxt[(j + 1) % 3], nxt[j]))
                for loop in f.loops:
                    loop[uv].uv = (0.5, 0.5)
        parts.append(pl.to_object(f'ring{k}', bm, mats['Steel']))
        parts.append(pl.tube(f'lace{k}', (ATTACH_X - 0.035, 0.0, z), (0.035, 0.0, z + 0.05), 0.006, 0.006, 4,
                             mats['Leather'], caps=False))
    return parts


lods = []
for level in range(3):
    sides = (8, 6, 4)[level]
    pole = pl.tube('pole', (0, 0, 0), (0, 0, POLE_TOP), 0.045, 0.035, sides, mats['Wood'], v_scale=0.6)
    parts = [pole]
    if level < 2:
        parts.append(pl.tube('knob', (0, 0, POLE_TOP), (0, 0, POLE_TOP + 0.07), 0.05, 0.02, sides, mats['Wood'],
                             v_scale=4))
    if spec['rings'] and level < 2:
        parts.extend(rings(level))
    solid = pl.join(f'solid{level}', parts)
    pl.vertex_occlusion(solid, rays=16, distance=0.2, strength=0.4)
    obj = pl.join(spec['name'] if level == 0 else f"{spec['name']}_LOD{level}", [solid, pennant(level)])
    print('LEVEL', level, obj.name, 'tris', pl.triangles(obj))
    lods.append(obj)
work = os.path.join(pl.PROPS, 'work')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(work, f'{variant}.blend'))
pl.export(lods, os.path.join(work, f'{variant}_export.glb'))
