"""Small keg `smlbarel`: a bulging barrel of 24 orange-red staves (`kegwood`: eight staves per texture repeat, dark
gaps, grain along them) with a recessed plank lid behind the top chime, and four riveted pale steel hoops (`hoop`:
eight rivets per repeat, u along the band) at the sprite's heights (0.045 + 0.125, 0.46, 0.79 of the height).
Proportions from the sprite (130 x 178 px: widest 0.72 x the height at mid height, ends 0.55). A procedural lathe
like the New Sorpigal barrel's proxy, not the scan. Writes work/keg_export.glb.
Usage: blender --background --python build_keg.py"""
import bpy, bmesh, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import props_lib as pl

pl.reset()
H = 1.0
R_MID, R_END = 0.36, 0.275
LID_DEPTH = 0.035
HOOPS = (0.045, 0.125, 0.46, 0.79)
HOOP_H = 0.058
mats = {'Wood': pl.material('Wood', 'kegwood'), 'Hoop': pl.material('Hoop', 'hoop')}


def radius(z):
    t = (z / H - 0.5) * 2                     # -1 at the bottom, 1 at the top
    return R_END + (R_MID - R_END) * (1 - t * t)


def build(level):
    seg = (32, 18, 10)[level]
    rings = (14, 8, 4)[level]
    side = [(radius(H * i / rings), H * i / rings) for i in range(rings + 1)]
    # top chime: over the rim and down the inside to the lid
    top = side + [(R_END - 0.018, H), (R_END - 0.020, H - LID_DEPTH)]
    parts = [pl.lathe('staves', [(R_END - 0.02, 0.0)] + top, seg, mats['Wood'], u_repeat=3, v_scale=1.0)]
    # lid and base: flat discs with the stave texture across them (the boards)
    for z, flip in ((H - LID_DEPTH, False), (0.0, True)):
        bm = bmesh.new(); uv = bm.loops.layers.uv.verify()
        r = R_END - 0.02
        verts = [bm.verts.new((r * math.cos(2 * math.pi * s / seg), r * math.sin(2 * math.pi * s / seg), z))
                 for s in range(seg)]
        f = bm.faces.new(list(reversed(verts)) if flip else verts)
        for loop in f.loops:
            loop[uv].uv = (loop.vert.co.x * 1.4 + 0.5, loop.vert.co.y * 1.4 + 0.5)
        parts.append(pl.to_object('lid' if not flip else 'base', bm, mats['Wood'], smooth=False))
    # hoops: bands standing 10 mm proud of the staves, rivets from the texture
    for k, centre in enumerate(HOOPS):
        z0, z1 = (centre - HOOP_H / 2) * H, (centre + HOOP_H / 2) * H
        r0, r1 = radius(z0) - 0.002, radius(z1) - 0.002
        profile = [(r0, z0), (r0 + 0.010, z0), (r1 + 0.010, z1), (r1, z1)]
        length = 0.020 + math.hypot(r1 - r0, z1 - z0)
        repeat = max(1, round(2 * math.pi * (r0 + r1) / 2 / 0.56))
        parts.append(pl.lathe(f'hoop{k}', profile, seg, mats['Hoop'], u_repeat=repeat, v_scale=1 / length))
    return pl.join(f'keg{level}', parts)


lods = []
for level in range(3):
    obj = build(level)
    occl = pl.vertex_occlusion(obj, rays=(48, 24, 12)[level], distance=0.25, strength=0.6)
    obj.name = 'Keg' if level == 0 else f'Keg_LOD{level}'; obj.data.name = obj.name
    print('LEVEL', level, obj.name, 'tris', pl.triangles(obj), 'mean occlusion', round(occl, 3))
    lods.append(obj)
work = os.path.join(pl.PROPS, 'work')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(work, 'keg.blend'))
pl.export(lods, os.path.join(work, 'keg_export.glb'))
