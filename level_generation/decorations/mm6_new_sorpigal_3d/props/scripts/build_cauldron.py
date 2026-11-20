"""Cooking cauldron `ckfyr00`: wooden tripod (three splayed poles under a small cap), an iron kettle hanging on a chain,
a teepee of logs ringed by stones, and the fire as one camera-facing quad (openyamm_billboard) playing the shared
flame flipbook (pl.flame_material: openyamm_flipbook, unlit, blended; its texture coordinates span the frame's lower
80 %, the engine maps them into the current frame). Each LOD is built at its own detail level. Textures
(2026-10-09 rework): graded CC0 Poly Haven sets from props/textures_pbr/ (make_pbr_textures.py): cedar-bark poles
(`Wood`), a coarse cast-iron kettle and chain (`Iron`, partly metallic for a sheen), split logs with glowing split
faces and an ember bed (unlit `Glow`) and charred bark (`Char`), purple-grey boulder-scan stones (`Stone`), the
stones and bark reddened by COLOR_0 where they face the fire. Writes work/cauldron_export.glb.
Usage: blender --background --python build_cauldron.py"""
import bpy, bmesh, math, os, sys
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import props_lib as pl
import fire_parts as fp

pl.reset()
HEIGHT = 1.70                       # apex; native sprite 132 x 222 units -> width / height 0.59
SPREAD = 0.50                       # pole feet radius
KETTLE_Z = 0.84                     # kettle bottom (the sprite's pot hangs at mid height)
LOG_TOP, LOG_RING = 0.28, 0.32
mats = fp.materials()
mats.update({
    'Wood': pl.pbr_material('Wood', 'fire_wood'),
    'Iron': pl.pbr_material('Iron', 'fire_iron'),
    'Fire': pl.flame_material(),
})
apex = Vector((0, 0, HEIGHT))


def build(level):
    sides = (8, 6, 4)[level]
    parts = []
    # tripod poles, feet slightly irregular
    for k in range(3):
        a = math.radians(90 + 120 * k + (7, -5, 3)[k])
        foot = Vector((math.cos(a) * SPREAD, math.sin(a) * SPREAD, 0.0))
        top = apex + (foot - apex).normalized() * -0.08 + Vector((0, 0, 0.02))
        parts.append(pl.tube(f'pole{k}', foot, top, 0.032, 0.024, sides, mats['Wood'], u_repeat=0.25,
                              v_scale=0.625))
    parts.append(pl.box('cap', (0, 0, HEIGHT - 0.01), (0.16, 0.07, 0.05), mats['Wood'], 1.2))
    # chain from the apex to the kettle bail
    chain_top, chain_bottom = HEIGHT - 0.04, KETTLE_Z + 0.46
    links = (8, 5, 1)[level]
    if links == 1:
        parts.append(pl.tube('chain', (0, 0, chain_bottom), (0, 0, chain_top), 0.008, 0.008, 4, mats['Iron'],
                             caps=False))
    else:
        step = (chain_top - chain_bottom) / links
        for i in range(links):
            parts.append(_link(f'link{i}', chain_bottom + (i + 0.5) * step, step * 0.5, (8, 6)[level], i % 2))
    # kettle (open pot with a dark surface inside) and its bail
    seg = (20, 12, 8)[level]
    profile = [(0.0, 0.0), (0.10, 0.0), (0.18, 0.05), (0.21, 0.13), (0.20, 0.21), (0.165, 0.265), (0.15, 0.28),
               (0.17, 0.295), (0.155, 0.305)]
    if level == 2:
        profile = [profile[0], profile[1], profile[3], profile[5], profile[7], profile[8]]
    parts.append(pl.lathe('kettle', profile, seg, mats['Iron'], u_repeat=2.0, v_scale=2.0,
                          centre=(0, 0, KETTLE_Z), cap_top=True))
    if level < 2:
        bail = []
        n = (10, 6)[level]
        for i in range(n + 1):
            t = math.pi * i / n
            bail.append(Vector((math.cos(t) * 0.17, 0, KETTLE_Z + 0.28 + math.sin(t) * 0.18)))
        for i in range(n):
            parts.append(pl.tube(f'bail{i}', bail[i], bail[i + 1], 0.006, 0.006, 4, mats['Iron'], caps=False))
    # split logs in a low teepee (split faces glowing, turned out) on an ember bed, and the stone ring
    log_count = (6, 5, 4)[level]
    glow = []
    for k in range(log_count):
        a = 2 * math.pi * k / log_count + 0.3
        foot = Vector((math.cos(a) * LOG_RING, math.sin(a) * LOG_RING, 0.03))
        tip = Vector((math.cos(a + 0.6) * 0.06, math.sin(a + 0.6) * 0.06, LOG_TOP))
        bark, face = fp.split_log(f'log{k}', foot, tip, 0.055, 0.04, (5, 3, 2)[level], mats, flat=0.3,
                                  roll=0.35 * math.sin(k * 2.3), seed=k)
        parts.append(bark); glow.append(face)
    glow += fp.ember_bed('embers', 0.27, 0.08, (10, 7, 5)[level], mats, coals=(5, 0, 0)[level])
    stones = (9, 8, 6)[level]
    for k in range(stones):
        a = 2 * math.pi * k / stones
        bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=(1, 1, 0)[level], radius=1.0)
        uv = bm.loops.layers.uv.verify()
        for v in bm.verts:
            jitter = 1 + 0.18 * math.sin(v.co.x * 7.1 + k) * math.cos(v.co.y * 5.3 - k)
            v.co = Vector((v.co.x * 0.12 * jitter, v.co.y * 0.10 * jitter, max(v.co.z, -0.4) * 0.09 * jitter))
        fp.box_uv(bm, uv, 2.6, k)
        ob = pl.to_object(f'stone{k}', bm, mats['Stone'])
        ob.location = (math.cos(a) * 0.40, math.sin(a) * 0.40, 0.05); ob.rotation_euler = (0, 0, a)
        bpy.context.view_layer.update()
        bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True); bpy.context.view_layer.objects.active = ob
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        parts.append(ob)
    solid = pl.join(f'solid{level}', parts)
    # fire: one upright quad in the model's x/up plane, bottom on the ground, texture coordinates 0..1
    bm = bmesh.new(); uv = bm.loops.layers.uv.verify()
    w, h = 0.88, 0.86                 # flames lick the kettle bottom (the flame spans 60 % of the card)
    verts = [bm.verts.new(c) for c in ((-w / 2, 0, 0.0), (w / 2, 0, 0.0), (w / 2, 0, h), (-w / 2, 0, h))]
    f = bm.faces.new(verts)
    for loop, coord in zip(f.loops, ((0, 1), (1, 1), (1, 0), (0, 0))):    # glTF v runs down: v = 0 at the top
        loop[uv].uv = (coord[0], (1 - coord[1]) * pl.FLAME_FRAME_TOP)
    fire = pl.to_object(f'fire{level}', bm, mats['Fire'], smooth=False)
    return solid, pl.join(f'glow{level}', glow), fire


def _link(name, z, size, segments, turn):
    """One oval chain link: a torus of `segments` x 4 around the vertical."""
    bm = bmesh.new(); uv = bm.loops.layers.uv.verify()
    rings = []
    for i in range(segments):
        t = 2 * math.pi * i / segments
        centre = Vector((math.cos(t) * size * 0.45, 0, math.sin(t) * size))
        tangent = Vector((-math.sin(t) * size * 0.45, 0, math.cos(t) * size)).normalized()
        out = tangent.cross(Vector((0, 1, 0))).normalized()
        ring = []
        for j in range(4):
            u = 2 * math.pi * j / 4
            ring.append(bm.verts.new(centre + (out * math.cos(u) + Vector((0, 1, 0)) * math.sin(u)) * 0.006))
        rings.append(ring)
    for i in range(segments):
        for j in range(4):
            following = rings[(i + 1) % segments]
            q = (rings[i][j], rings[i][(j + 1) % 4], following[(j + 1) % 4], following[j])
            face = bm.faces.new(q)
            for loop in face.loops:
                loop[uv].uv = (0.5, 0.5)
    rot = Matrix.Rotation(math.pi / 2 * turn, 4, 'Z')
    for v in bm.verts:
        v.co = rot @ v.co + Vector((0, 0, z))
    return pl.to_object(name, bm, mats['Iron'])


lods = []
for level in range(3):
    solid, glow, fire = build(level)
    occl = pl.vertex_occlusion(solid, rays=(40, 24, 12)[level], distance=0.35, strength=0.7)
    fp.fire_lit(solid, Vector((0.0, 0.0, 0.15)), stone_low=0.12)
    fp.glow_colour(glow, LOG_TOP, LOG_RING)
    pl.white_colour(fire)
    name = 'Cauldron' if level == 0 else f'Cauldron_LOD{level}'
    obj = pl.join(name, [solid, glow, fire])
    print('LEVEL', level, name, 'tris', pl.triangles(obj), 'mean occlusion', round(occl, 3))
    lods.append(obj)
work = os.path.join(pl.PROPS, 'work'); os.makedirs(work, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(work, 'cauldron.blend'))
pl.export(lods, os.path.join(work, 'cauldron_export.glb'))
