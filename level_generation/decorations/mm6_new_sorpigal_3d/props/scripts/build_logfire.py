"""Log-pile fire `dec04` (dungeons): a low, sprawling heap of broken planks and split logs lying flat and crossed, a
burning wooden structure rather than a teepee, with no stone ring. Traced from the sprite (art 104 x 116 units: heap
about 44 units tall across the full width, a ragged fire from its centre and grey smoke rising to the top).

- Charred planks and split-log bark: `Char` (lit PBR fire_char, faint flickering ember emission in finish.py).
- Ember glints: `Embers` (unlit logfire_embers: near-black char with orange only deep in the scan's cracks) on the
  upward faces of the planks near the fire, the split logs' split faces and the end grain of the front logs.
- Two or three bigger, lighter-brown logs in front: `Wood` (lit PBR logfire_wood, rough weathered grain).
- Glowing bed under the flame: `Glow` (unlit fire_glow, as the campfire).
- Fire: one broad camera-facing card on the shared Flame02 (pl.flame_material), centred on the heap, recoloured
  deep orange through its COLOR_0 (fire_colour). Smoke: one camera-facing card from
  45 units to the top on a procedural grey smoke flipbook (`Smoke`, logfire_smoke, 8 x 4 frames at 10 fps,
  blended, unlit), submitted before the flame so it stays behind it.
COLOR_0: vertex occlusion, reddened where faces look at the fire (fire_parts.fire_lit); the glow bed hottest low.
Writes work/logfire_export.glb. Usage: blender --background --python build_logfire.py"""
import bpy, bmesh, math, os, sys
import numpy as np
from mathutils import Vector, Matrix, Euler
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import props_lib as pl
import fire_parts as fp

pl.reset()
U = 81.7                            # map units per metre
TOTAL = 116 / U                     # smoke top: the binding height
HEAP = 44 / U                       # heap top
FLAME_TOP = 93 / U
mats = fp.materials()
mats.update({
    'Wood': pl.pbr_material('Wood', 'logfire_wood'),
    'Embers': pl.pbr_material('Embers', 'logfire_embers'),
    'Fire': pl.flame_material(),
    'Smoke': pl.pbr_material('Smoke', 'logfire_smoke', alpha=True,
                             extras={'openyamm_billboard': True, 'openyamm_flipbook': [8, 4, 10],
                                     'openyamm_specular': 0.0}),
})
split_mats = {'Char': mats['Char'], 'Glow': mats['Embers']}     # split faces: charred with glints, not glowing plates
TILE = 1 / 0.55                     # wood texture tiles per metre
SPREAD = 0.84                       # the heap's layout below spans 1.52 m; the sprite's 104 units are 1.27 m

# planks: (centre, (length, width, thickness), (roll, pitch, yaw) degrees, minimum level of detail)
PLANKS = [
    ((0.00, 0.30, 0.15), (0.95, 0.18, 0.05), (0, 6, 8), 2),
    ((-0.38, 0.00, 0.10), (0.62, 0.17, 0.045), (4, 12, 70), 2),
    ((0.40, 0.02, 0.11), (0.60, 0.16, 0.045), (-5, -14, -65), 2),
    ((-0.24, -0.17, 0.23), (0.70, 0.15, 0.04), (10, 22, -30), 1),
    ((0.26, -0.15, 0.25), (0.65, 0.15, 0.04), (-8, -25, 35), 1),
    ((0.05, 0.12, 0.39), (0.75, 0.14, 0.04), (6, 18, 95), 1),
    ((-0.50, 0.24, 0.05), (0.50, 0.15, 0.04), (0, 3, 20), 0),
    ((0.52, -0.10, 0.05), (0.45, 0.14, 0.04), (0, -4, -10), 0),
    ((-0.10, 0.36, 0.34), (0.55, 0.13, 0.04), (-12, -20, 140), 0),
    ((0.15, -0.36, 0.06), (0.36, 0.12, 0.035), (0, 8, 60), 0),          # broken pieces and chunks
    ((-0.20, -0.42, 0.04), (0.28, 0.11, 0.035), (0, -6, -40), 0),
    ((0.48, 0.30, 0.10), (0.40, 0.13, 0.04), (14, -18, 50), 1),
    ((-0.42, 0.40, 0.12), (0.42, 0.12, 0.04), (-10, 16, -55), 1),
    ((0.10, -0.05, 0.47), (0.40, 0.12, 0.035), (20, -10, 30), 0),
]
# lighter front logs: (foot, tip, radius foot, radius tip, minimum level of detail); the foot faces the viewer
FRONT_LOGS = [
    ((0.02, -0.56, 0.13), (-0.02, 0.15, 0.36), 0.13, 0.11, 2),
    ((0.33, -0.42, 0.08), (0.03, 0.06, 0.30), 0.085, 0.07, 1),
    ((-0.37, -0.40, 0.08), (-0.03, 0.10, 0.28), 0.08, 0.065, 1),
]
# charred split logs lying across the heap, split face up: (foot, tip, radius foot, radius tip, minimum level)
SPLIT_LOGS = [
    ((-0.62, 0.25, 0.07), (0.10, -0.05, 0.30), 0.07, 0.06, 2),
    ((0.62, 0.30, 0.07), (-0.05, 0.00, 0.33), 0.07, 0.06, 2),
    ((-0.56, -0.24, 0.06), (0.12, 0.26, 0.13), 0.06, 0.05, 0),
    ((0.25, 0.48, 0.06), (0.30, -0.22, 0.18), 0.055, 0.05, 0),
]


def plank(name, centre, size, angles, level):
    size = (size[0], size[1] * 1.3, size[2] * 1.7)              # chunky boards and beams, like the sprite's heap
    ob = pl.box(name, (0, 0, 0), size, mats['Char'], TILE)
    rot = Euler([math.radians(a) for a in angles], 'XYZ').to_matrix().to_4x4()
    ob.data.transform(Matrix.Translation(Vector(centre)) @ rot)
    ob.data.materials.append(mats['Embers'])
    hot = Vector(centre).xy.length < 0.45
    for p in ob.data.polygons:
        if hot and p.normal.z > 0.6:
            p.material_index = 1
    return ob


def front_log(name, foot, tip, ra, rb, sides):
    ob = pl.tube(name, foot, tip, ra, rb, sides, mats['Wood'], u_repeat=1.0, v_scale=TILE)
    ob.data.materials.append(mats['Embers'])
    axis = (Vector(tip) - Vector(foot)).normalized()
    for p in ob.data.polygons:
        if abs(p.normal.dot(axis)) > 0.9:                   # end grain: charred, with glints
            p.material_index = 1
    return ob


def build(level):
    parts, glow = [], []
    for k, (c, size, angles, need) in enumerate(PLANKS):
        if level <= need:
            parts.append(plank(f'plank{k}', c, size, angles, level))
    for k, (a, b, ra, rb, need) in enumerate(FRONT_LOGS):
        if level <= need:
            parts.append(front_log(f'front{k}', a, b, ra, rb, (12, 7, 5)[level]))
    for k, (a, b, ra, rb, need) in enumerate(SPLIT_LOGS):
        if level <= need:
            bark, face = fp.split_log(f'split{k}', a, b, ra, rb, (6, 3, 2)[level], split_mats, flat=0.3,
                                      seed=k + 3, face=(0, 0, 1))
            parts.append(bark); parts.append(face)
    solid = pl.join(f'solid{level}', parts)
    solid.data.transform(Matrix.Diagonal((SPREAD, SPREAD, 1.0, 1.0)))
    glow += fp.ember_bed('bed', 0.30, 0.20, (10, 7, 5)[level], mats, coals=(5, 0, 0)[level], seed=0.7)
    # fire: (centre x, width, bottom, top, mirrored) on the shared flame (its lower 80 % per card); smoke above
    # one broad fire centred on the heap: the flame spans 60 % of the card, so a 1.6 m card gives a flame about
    # 0.95 m wide, 75 % of the heap's 1.27 m
    cards = [(0.0, 1.6, 0.14, FLAME_TOP, False)]
    bm = bmesh.new(); uv = bm.loops.layers.uv.verify()
    for cx, w, lo, hi, mirrored in cards:
        verts = [bm.verts.new(c) for c in ((cx - w / 2, 0, lo), (cx + w / 2, 0, lo), (cx + w / 2, 0, hi),
                                           (cx - w / 2, 0, hi))]
        f = bm.faces.new(verts)
        for loop, (u, v) in zip(f.loops, ((0, 1), (1, 1), (1, 0), (0, 0))):
            loop[uv].uv = (1 - u if mirrored else u, (1 - v) * pl.FLAME_FRAME_TOP)
    fire = pl.to_object(f'fire{level}', bm, mats['Fire'], smooth=False)
    bm = bmesh.new(); uv = bm.loops.layers.uv.verify()
    cx, w, lo = -0.03, 1.10, 45 / U       # 60 % of the heap's width at the top, merging into the flame
    verts = [bm.verts.new(c) for c in ((cx - w / 2, 0, lo), (cx + w / 2, 0, lo), (cx + w / 2, 0, TOTAL),
                                       (cx - w / 2, 0, TOTAL))]
    f = bm.faces.new(verts)
    for loop, (u, v) in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
        loop[uv].uv = (u, v)
    smoke = pl.to_object(f'smoke{level}', bm, mats['Smoke'], smooth=False)
    return solid, pl.join(f'glow{level}', glow), fire, smoke


def fire_colour(obj):
    """COLOR_0 of this model's flame card only (the shared Flame02 texture is untouched): a linear multiplier taking
    the torch-yellow flame (core 254, 228, 88) to the sprite's deep orange fireball (core about 240, 110, 30), redder
    toward the cards' tops."""
    me = obj.data
    top = max(v.co.z for v in me.vertices)
    colours = []
    for v in me.vertices:
        t = v.co.z / top
        colours.append((0.92 - 0.14 * t, 0.29 - 0.08 * t, 0.18 - 0.05 * t, 1.0))
    attr = me.color_attributes.new('Color', 'FLOAT_COLOR', 'POINT')
    attr.data.foreach_set('color', np.array(colours, np.float32).ravel())
    me.color_attributes.active_color = attr


def char_tint(obj):
    """Per-material COLOR_0 tint on the occlusion: the sprite's char is a near-neutral black-brown (18, 13, 9 in the
    gaps, 44, 30, 17 over the heap), darker and less red than fire_char; its front logs are a shaded mid brown."""
    me = obj.data
    names = [m.name for m in me.materials]
    tint = {'Char': (0.55, 0.62, 0.66), 'Wood': (0.5, 0.5, 0.48), 'Embers': (1.0, 1.0, 1.0)}
    attr = me.color_attributes['Color']
    done = set()
    for p in me.polygons:
        t = tint.get(names[p.material_index], (1, 1, 1))
        for i in p.vertices:
            if i in done:
                continue
            done.add(i)
            c = attr.data[i].color
            attr.data[i].color = (c[0] * t[0], c[1] * t[1], c[2] * t[2], c[3])


lods = []
for level in range(3):
    solid, glow, fire, smoke = build(level)
    if level == 0:
        lo, hi = pl.bounds([solid])
        print('HEAP', [round(v, 3) for v in lo], [round(v, 3) for v in hi], 'target top', round(HEAP, 3),
              'width', round(104 / U, 3))
    occl = pl.vertex_occlusion(solid, rays=(40, 24, 12)[level], distance=0.3, strength=0.65)
    char_tint(solid)
    fp.fire_lit(solid, Vector((0.0, 0.0, 0.3)), strength=0.3, stone_low=0)
    fp.glow_colour(glow, 0.3, 0.3)
    fire_colour(fire); pl.white_colour(smoke)
    name = 'LogFire' if level == 0 else f'LogFire_LOD{level}'
    # Smoke before Fire: blended static primitives are submitted in primitive order to the sequential transparent
    # view, and the billboards share one plane, so the order puts the smoke behind the flame where they overlap.
    obj = pl.join(name, [solid, glow, smoke, fire])
    slots = [m.name for m in obj.data.materials]                  # join orders slots by object name: move Smoke up
    obj.active_material_index = slots.index('Smoke')
    for _ in range(slots.index('Smoke') - slots.index('Fire')):
        bpy.ops.object.material_slot_move(direction='UP')
    print('LEVEL', level, name, 'tris', pl.triangles(obj), 'mean occlusion', round(occl, 3))
    lods.append(obj)
work = os.path.join(pl.PROPS, 'work'); os.makedirs(work, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(work, 'logfire.blend'))
pl.export(lods, os.path.join(work, 'logfire_export.glb'))
