"""Campfire `cmpfyr00`: a teepee of logs on a glowing ember bed, ringed by five warm grey stones, with the fire as
three camera-facing cards playing the shared flame flipbook (pl.flame_material, openyamm_billboard, openyamm_flipbook,
unlit, blended; the flame spans 60 % of a card; the engine maps the texture coordinates into the current frame). The
billboard keeps each vertex's offset across the model, so the cards stay side by side facing the camera: a tall
central flame as wide as the teepee and two lower side flames, mirrored so they do not repeat it. Proportions from
the sprite (106 x 121 units: the flame dominates, rising to about 1.6 x the teepee's height). Textures (2026-10-09
rework): graded CC0 Poly Haven sets from props/textures_pbr/ (make_pbr_textures.py). The logs are split logs
(fire_parts.split_log): their flat faces, turned outward, and the ember bed glow (unlit `Glow`, alligatored char with
red-orange plates, COLOR_0 hottest low in the fire), their bark is charred (`Char`, lit, faint flickering ember
emission in finish.py); the stones are a purple-grey boulder scan (`Stone`) reddened by COLOR_0 where they face the
fire. Writes work/campfire_export.glb. Usage: blender --background --python build_campfire.py"""
import bpy, bmesh, math, os, sys
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import props_lib as pl
import fire_parts as fp

pl.reset()
HEIGHT = 1.48                       # flame top: 121 units at 81.7 units/m
LOG_TOP = 0.84
RING = 0.46                         # stone ring radius (the sprite's 106-unit width)
mats = fp.materials()
mats['Fire'] = pl.flame_material()


def stone(name, centre, size, seed, level):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=(2, 1, 0)[level], radius=1.0)
    uv = bm.loops.layers.uv.verify()
    for v in bm.verts:
        jitter = 1 + 0.2 * math.sin(v.co.x * 6.3 + seed) * math.cos(v.co.y * 4.7 - seed * 1.3)
        v.co = Vector((v.co.x * size[0] * jitter, v.co.y * size[1] * jitter,
                       max(v.co.z, -0.35) * size[2] * jitter)) + Vector(centre)
    fp.box_uv(bm, uv, 2.6, seed)
    return pl.to_object(name, bm, mats['Stone'])


def build(level):
    sides = (7, 5, 4)[level]
    parts = []
    # five big rounded stones around the fire
    count = (5, 5, 4)[level]
    for k in range(count):
        a = 2 * math.pi * k / count + 0.35
        size = (0.23 + 0.03 * math.sin(k * 2.1), 0.19, 0.17 + 0.03 * math.cos(k * 1.7))
        parts.append(stone(f'stone{k}', (math.cos(a) * RING, math.sin(a) * RING, size[2] * 0.45), size, k, level))
        ob = parts[-1]
        ob.rotation_euler = (0, 0, a); bpy.context.view_layer.update()
    for ob in parts:
        bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True); bpy.context.view_layer.objects.active = ob
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    # teepee of split logs leaning together, split faces turned out (toward the viewer)
    logs = (7, 5, 4)[level]
    glow = []
    for k in range(logs):
        a = 2 * math.pi * k / logs
        foot = Vector((math.cos(a) * 0.36, math.sin(a) * 0.36, 0.05))
        tip = Vector((math.cos(a + 0.5) * 0.05, math.sin(a + 0.5) * 0.05, LOG_TOP))
        bark, face = fp.split_log(f'log{k}', foot, tip, 0.095, 0.05, (5, 3, 2)[level], mats, flat=0.3,
                                  roll=0.35 * math.sin(k * 2.3), seed=k)
        parts.append(bark); glow.append(face)
    solid = pl.join(f'solid{level}', parts)
    # glowing ember bed inside the teepee, with coals heaped on it at LOD0
    glow += fp.ember_bed('embers', 0.34, 0.11, (12, 8, 6)[level], mats, coals=(7, 0, 0)[level])
    # fire: upright cards in the model's x/up plane, (centre x, width, bottom, top, mirrored). Blender v runs up (the
    # glTF export flips it); the cards show the shared flame frame's lower 80 % (pl.FLAME_FRAME_TOP).
    cards = [(0.0, 1.6, 0.02, HEIGHT, False), (-0.26, 0.95, 0.02, 1.15, True), (0.27, 0.9, 0.02, 1.05, True)]
    bm = bmesh.new(); uv = bm.loops.layers.uv.verify()
    for cx, w, lo, hi, mirrored in cards[:(3, 3, 1)[level]]:
        verts = [bm.verts.new(c) for c in ((cx - w / 2, 0, lo), (cx + w / 2, 0, lo), (cx + w / 2, 0, hi),
                                           (cx - w / 2, 0, hi))]
        f = bm.faces.new(verts)
        for loop, (u, v) in zip(f.loops, ((0, 1), (1, 1), (1, 0), (0, 0))):
            loop[uv].uv = (1 - u if mirrored else u, (1 - v) * pl.FLAME_FRAME_TOP)
    fire = pl.to_object(f'fire{level}', bm, mats['Fire'], smooth=False)
    return solid, pl.join(f'bed{level}', glow), fire


lods = []
for level in range(3):
    solid, bed, fire = build(level)
    occl = pl.vertex_occlusion(solid, rays=(40, 24, 12)[level], distance=0.3, strength=0.6)
    fp.fire_lit(solid, Vector((0.0, 0.0, 0.35)))
    fp.glow_colour(bed, LOG_TOP, 0.36)
    pl.white_colour(fire)
    name = 'Campfire' if level == 0 else f'Campfire_LOD{level}'
    obj = pl.join(name, [solid, bed, fire])
    print('LEVEL', level, name, 'tris', pl.triangles(obj), 'mean occlusion', round(occl, 3))
    lods.append(obj)
work = os.path.join(pl.PROPS, 'work'); os.makedirs(work, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(work, 'campfire.blend'))
pl.export(lods, os.path.join(work, 'campfire_export.glb'))
