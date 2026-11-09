"""dec95: a small statue of a knight in plate armour resting his right hand on the pommel of a sword whose point stands
on the plinth, on a sloped granite plinth (outdoor, out14, one placement). The MM6 knight creature
(assets_source/worlds/mm6/models/mm6_kni.glb, read only) is posed and baked static with its crest plume cut away;
the sword (a straight cross-hilted longsword, as the sprite's, not the creature's curved blade) and the plinth are
procedural. Surfaces: the knight's own atlas recoloured to the sprite's metal ramp (statue_compose.py), a light
CC0 rock tile on the sword and a CC0 rock_surface tile on the plinth, graded under outdoor review light.
Stages as statue_dwarf.py: --preview, --stage bake, default build (work/dec95_export.glb).
Usage: blender --background --python statue_knight.py -- [--preview | --stage bake]"""
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import statue_lib as sl  # noqa: E402

dlib, pl, hl, cp = sl.dlib, sl.pl, sl.hl, sl.cp
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
PROP = 'dec95'
PREVIEW = '--preview' in args
STAGE = args[args.index('--stage') + 1] if '--stage' in args else 'build'
KNIGHT = os.path.join(dlib.MODELS_MM6, 'mm6_kni.glb')

# Standing straight; the right arm out to the side with the elbow bent, the hand resting on the pommel beside the
# right hip; the left arm hanging. The knight faces -y (his right at -x).
POSE = [
    ('aim', 'B_L_Thigh', (0.08, 0.0, -1), 1.0),
    ('aim', 'B_L_Calf', (0.02, 0.04, -1), 1.0),
    ('aim', 'B_R_Thigh', (-0.08, 0.0, -1), 1.0),
    ('aim', 'B_R_Calf', (-0.02, 0.04, -1), 1.0),
    ('aim', 'B_R_UpperArm', (-0.75, 0.2, -0.6), 1.0, 'B_R_Forearm'),
    ('aim', 'B_R_Forearm', (0.15, -0.7, 0.45), 1.0, 'B_R_Hand'),
    ('aim', 'B_L_UpperArm', (0.22, 0.02, -1), 1.0, 'B_L_Forearm'),
    ('aim', 'B_L_Forearm', (0.1, -0.12, -1), 1.0, 'B_L_Hand'),
]
LEVELS = [(0, 3200, 0), (2, 1300, 1), ('far', 470, 0.012), ('far', 250, 0.012)]
# Plinth (metres, knight scale): a top slab and a sloped body, centred under the knight and the sword.
PLINTH = {'bottom': (1.36, 1.12), 'top': (0.98, 0.8), 'height': 0.3, 'slab': 0.04}
# Sprite means (sRGB): the figure rows and the plinth rows of dec95_p2.
TARGETS = {'metal': (106, 101, 88), 'sword': (128, 122, 108), 'plinth': (147, 138, 122)}
# Outdoor grade: albedo = target x gain, so the model under the outdoor review light shows about the sprite's mean.
GAIN = (0.88, 0.85, 0.8)        # per channel: the bluish sky greys the warm metal
BULK = 1.14
GRIPS = []              # the sword grip per built level (before the plinth-centring shift)


def aim_socket(arm, hand, socket, direction):
    bones = arm.pose.bones
    head = arm.matrix_world @ bones[socket].head; tail = arm.matrix_world @ bones[socket].tail
    q = (tail - head).normalized().rotation_difference(Vector(direction).normalized())
    cp._apply(arm, bones[hand], q.to_matrix(), arm.matrix_world @ bones[hand].head)


def build_pose(level, name):
    for o in list(bpy.data.objects):
        if o.type == 'ARMATURE' or (o.parent and o.parent.type == 'ARMATURE'):
            bpy.data.objects.remove(o)
    arm, body = sl.load(KNIGHT, level)
    co = sl.coords(body)
    names = np.array(cp.strongest_bone(body))
    # the crest plume: from the helmet top back down the spine, a narrow sheet behind the armour
    plume = ((names == 'B_Head') & (((co[:, 2] > 1.69) & (np.abs(co[:, 0]) < 0.05)) | (co[:, 2] > 1.73) |
                                     ((co[:, 2] > 1.64) & (co[:, 1] > 0.04)))) | \
        (np.isin(names, ['B_Head', 'B_Neck']) & (np.abs(co[:, 0]) > 0.105) & (co[:, 2] > 1.55)) | ((co[:, 1] > 0.11) & (np.abs(co[:, 0]) < 0.13) &
                                                          (co[:, 2] > 0.95))
    sl.delete_verts(body, plume)
    # small loose ornaments on the helmet (side rings, studs) and the spikes on the shoulders
    print('ORNAMENTS dropped', sl.drop_pieces(body, lambda n, c, lo, hi: n < 45 and (
        c[2] > 1.55 or (c[2] > 1.42 and abs(c[0]) > 0.15) or (c[2] > 1.35 and c[1] > 0.08))))
    # the sprite's knight is stockier than the creature: widen it (not taller)
    co = sl.coords(body)
    co[:, 0] = co[:, 0] * BULK
    co[:, 1] = -0.03 + (co[:, 1] + 0.03) * BULK
    sl.set_coords(body, co)
    cp.pose(arm, POSE)
    aim_socket(arm, 'B_R_Hand', 'Sword', (0, 0.0, -1))
    static = cp.bake(arm, body, name)
    # the pommel sits under the palm: the sword axis through the posed hand's centroid (hand and finger vertices)
    hand = np.array([n == 'B_R_Hand' or n.startswith('B_R_Finger') for n in cp.strongest_bone(static)])
    hco = sl.coords(static)[hand]
    grip = Vector((float(hco[:, 0].mean()), float(hco[:, 1].mean()), float(hco[:, 2].min()) - 0.1))
    static.vertex_groups.clear()
    for key in ('rest', 'custom_normal'):
        if key in static.data.attributes:
            static.data.attributes.remove(static.data.attributes[key])
    for o in (arm, body):
        bpy.data.objects.remove(o)
    return static, grip


def box_frustum(name, bottom, top, z0, z1, centre, mat, uv_scale=2.0):
    """A closed truncated box: bottom (w, d) at z0, top (w, d) at z1 around centre (x, y)."""
    bm = bmesh.new(); uv = bm.loops.layers.uv.verify()
    cx, cy = centre
    ring = []
    for (w, d), z in ((bottom, z0), (top, z1)):
        ring.append([bm.verts.new((cx + sx * w / 2, cy + sy * d / 2, z))
                     for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
    for k in range(4):
        k2 = (k + 1) % 4
        bm.faces.new((ring[0][k], ring[0][k2], ring[1][k2], ring[1][k]))
    bm.faces.new(ring[1]); bm.faces.new(list(reversed(ring[0])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        n = f.normal
        for loop in f.loops:
            c = loop.vert.co
            if abs(n.z) > 0.7:
                loop[uv].uv = (c.x * uv_scale, c.y * uv_scale)
            elif abs(n.x) > abs(n.y):
                loop[uv].uv = (c.y * uv_scale, c.z * uv_scale)
            else:
                loop[uv].uv = (c.x * uv_scale, c.z * uv_scale)
    return pl.to_object(name, bm, mat, False)


def plinth(mat, centre, detail):
    p = PLINTH
    parts = [box_frustum('PlinthBody', p['bottom'], p['top'], 0.0, p['height'] - p['slab'], centre, mat)]
    w, d = p['top']
    parts.append(box_frustum('PlinthSlab', (w + 0.04, d + 0.04), (w + 0.02, d + 0.02), p['height'] - p['slab'],
                             p['height'], centre, mat))
    return parts


def sword(grip, base_z, detail, mat):
    """A straight longsword point down: pommel above the grip, crossguard below the hand, the blade to the plinth."""
    x, y = grip.x, grip.y
    sides = (6, 4, 4, 3)[detail]
    guard_z = grip.z - 0.11
    parts = [
        sl.sweep_m('Pommel', [(x, y, grip.z + 0.07), (x, y, grip.z + 0.11), (x, y, grip.z + 0.15)],
                   [0.025, 0.05, 0.02], sides, mat),
        sl.sweep_m('Grip', [(x, y, guard_z), (x, y, grip.z + 0.08)], 0.024, sides, mat),
        sl.sweep_m('Guard', [(x - 0.2, y, guard_z), (x + 0.2, y, guard_z)], 0.03, 4, mat, flat=0.7),
        # the blade: a flat diamond section tapering to the point on the plinth
        sl.sweep_m('Blade', [(x, y, guard_z - 0.01), (x, y, base_z + 0.12), (x, y, base_z)], [0.07, 0.055, 0.006],
                   4, mat, flat=0.25, phase=math.pi / 4 * 0 + math.pi / 2),
    ]
    return parts


def great_helm(detail, mat, slit_mat, lift):
    """The sprite's great helm (the head is not posed, so it stays in the rest frame, widened by BULK): a rounded
    bucket over the creature's helmet, a slight brow ridge, a domed top, and a narrow eye slit recessed into the front
    (its faces on the dark Slit material)."""
    seg = (16, 12, 8, 6)[detail]
    cy = -0.041
    # (z, rx, ry, slit band below this ring); the slit sits under the brow ridge
    rings = [(1.49, 0.105, 0.122, False), (1.53, 0.124, 0.145, False), (1.58, 0.132, 0.155, False),
             (1.607, 0.134, 0.157, False), (1.637, 0.134, 0.157, True), (1.65, 0.142, 0.167, False),
             (1.662, 0.133, 0.156, False), (1.69, 0.124, 0.145, False), (1.718, 0.108, 0.126, False),
             (1.74, 0.082, 0.096, False), (1.757, 0.05, 0.058, False), (1.766, 0.02, 0.023, False)]
    if detail >= 2:
        rings = [r for k, r in enumerate(rings) if k in (0, 2, 3, 4, 5, 7, 9, 11)]
    front = lambda a: math.sin(a) < -0.55                                       # noqa: E731 (faces -y)
    bm = bmesh.new(); uv = bm.loops.layers.uv.verify()
    angles = [2 * math.pi * k / seg for k in range(seg)]
    loops = []
    for i, (z, rx, ry, _) in enumerate(rings):
        inset = 0.0
        loop = []
        for a in angles:
            # the two rings bounding the slit are pulled in on the front, so the slit is cut into the surface
            slit_edge = (i + 1 < len(rings) and rings[i + 1][3]) or rings[i][3]
            d = 0.02 if slit_edge and front(a) and detail < 3 else 0.0
            loop.append(bm.verts.new(((rx - d) * math.cos(a), cy + (ry - d) * math.sin(a), z + lift)))
        loops.append(loop)
    for i in range(len(loops) - 1):
        for k in range(seg):
            k2 = (k + 1) % seg
            f = bm.faces.new((loops[i][k], loops[i][k2], loops[i + 1][k2], loops[i + 1][k]))
            if rings[i + 1][3] and front(angles[k]) and front(angles[k2]) and detail < 3:
                f.material_index = 1
            for loop, (a, b) in zip(f.loops, ((k, i), (k + 1, i), (k + 1, i + 1), (k, i + 1))):
                loop[uv].uv = (a / seg, b * 0.2)
    top = bm.verts.new((0.0, cy, rings[-1][0] + 0.006 + lift))
    for k in range(seg):
        f = bm.faces.new((loops[-1][k], loops[-1][(k + 1) % seg], top))
        for loop in f.loops:
            loop[uv].uv = (0.5, 0.5)
    # the bottom is open, so orient every face outward from the helm's axis explicitly
    axis = Vector((0.0, cy, 0.0))
    for f in bm.faces:
        c = f.calc_center_median()
        out = Vector((c.x - axis.x, c.y - axis.y, max(0.0, c.z - (1.70 + lift)) * 2.0))
        if f.normal.dot(out) < 0:
            f.normal_flip()
    helm = pl.to_object('Helm', bm, mat, True)
    helm.data.materials.append(slit_mat)
    return [helm]


def materials(stage):
    if stage == 'bake':
        m = bpy.data.materials.new('Plain'); return {k: m for k in ('Body', 'Sword', 'Plinth', 'Slit', 'Helm')}
    return {'Body': dlib.material('Metal', 'statue_dec95', extras={'openyamm_specular': 0.6}),
            'Sword': dlib.material('Sword', 'statue_stonelight', extras={'openyamm_specular': 0.7}),
            'Plinth': dlib.material('Plinth', 'statue_granite', extras={'openyamm_specular': 0.3}),
            'Slit': dlib.material('Slit', 'statue_stone', extras={'openyamm_specular': 0.1}),
            'Helm': dlib.material('Helm', 'statue_stonelight', extras={'openyamm_specular': 0.6})}


def darken_slit(obj):
    """The visor slit reads black in the sprite: darken the slit box's vertices (the thin box in front of the helm)."""
    me = obj.data
    colour = me.color_attributes['Color']
    c = np.empty(len(me.vertices) * 4, np.float32); colour.data.foreach_get('color', c); c = c.reshape(-1, 4)
    co = sl.coords(obj)
    z0 = 1.635 + PLINTH['height']
    w = (np.abs(co[:, 2] - z0 - 0.01) < 0.0125) & (co[:, 1] < -0.18) & (np.abs(co[:, 0]) < 0.09)
    c[w, :3] *= 0.15
    colour.data.foreach_set('color', c.ravel())


def tint_table():
    import json
    exposed = json.load(open(os.path.join(dlib.WORK, f'{PROP}_texture.json')))['exposed_mean']
    g = lambda c: tuple(v * k for v, k in zip(c, GAIN))                         # noqa: E731
    return {'Metal': (g(TARGETS['metal']), exposed), 'Sword': (g(TARGETS['sword']), None),
            'Plinth': (g(TARGETS['plinth']), None), 'Slit': ((14, 13, 12), None),
            'Helm': (g((150, 143, 126)), None)}     # the helm reads brighter than the body's mean (highlights)


def level(index, mats):
    src, body_tris, detail = LEVELS[index]
    name = 'Statue' if index == 0 else f'Statue_LOD{index}'
    body, grip = build_pose(src, f'Body{index}')
    sl.single_material(body, mats['Body'])
    sl.decimate(body, body_tris)
    # stand the knight on the plinth: his lowest point on its top
    co = sl.coords(body)
    lift = PLINTH['height'] - float(co[:, 2].min())
    feet = co[co[:, 2] < co[:, 2].min() + 0.08]
    body.data.transform(Matrix.Translation((0, 0, lift)))
    grip = grip + Vector((0, 0, lift))
    blade = sword(grip, PLINTH['height'], detail, mats['Sword'])
    GRIPS.append(grip.copy())
    centre = ((float(feet[:, 0].mean()) + grip.x) / 2, float(feet[:, 1].mean()))
    base = plinth(mats['Plinth'], centre, detail)
    helm = great_helm(detail, mats['Helm'], mats['Slit'], lift)
    return name, {'body': [body], 'sword': blade + helm, 'plinth': base}, centre


def main():
    pl.reset()
    mats = materials(STAGE)
    count = 1 if STAGE == 'bake' else len([lv for lv in LEVELS if lv[0] != 'far'])
    built = [level(i, mats) for i in range(count)]
    cx, cy = built[0][2]
    shift = Matrix.Translation((-cx, -cy, 0))
    for _, groups, _ in built:
        for objs in groups.values():
            for p in objs:
                p.data.transform(shift)
    if STAGE == 'bake':
        body0 = built[0][1]['body'][0]
        sl.smooth(body0, 70)
        sl.stone_bake(body0, os.path.join(dlib.WORK, f'{PROP}_bake.npy'), (1024, 1024), stone='rock_01')
        return
    lods = []
    for name, groups, _ in built:
        parts = [p for objs in groups.values() for p in objs]
        joined = pl.join(name, parts)
        sl.smooth(joined, 60)
        pl.vertex_occlusion(joined, rays=(32, 20, 12, 8)[len(lods)], distance=0.12, strength=0.55, floor=True)
        sl.tint_groups(joined, tint_table(), keep={'Metal': 0.35, 'Helm': 0.3})
        lods.append(joined)
    far_mat = dlib.material('StoneFar', 'statue_stone', extras={'openyamm_specular': 0.4})
    for index, (kind, target, voxel) in enumerate(LEVELS):
        if kind == 'far':
            # the figure alone is remeshed; the plinth stays a plain box (remeshing it wastes the budget)
            figure = sl.duplicate(lods[1], f'Figure{index}')
            plinth_slot = [m.name for m in figure.data.materials].index('Plinth')
            bm = bmesh.new(); bm.from_mesh(figure.data)
            bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index == plinth_slot], context='FACES')
            bm.to_mesh(figure.data); bm.free()
            far = sl.far_lod(figure, f'Statue_LOD{index}', target, voxel, far_mat)
            bpy.data.objects.remove(figure)
            g = GRIPS[0] - Vector((cx, cy, 0))
            base = pl.join(f'Base{index}', plinth(mats['Plinth'], (0.0, 0.0), 3) +
                           sword(g, PLINTH['height'], 3, mats['Sword']))
            pl.vertex_occlusion(base, rays=8, distance=0.12, strength=0.55, floor=True)
            sl.tint_groups(base, tint_table())
            lods.append(pl.join(far.name, [far, base]))
    dlib.save(PROP, lods)


if __name__ == '__main__':
    if PREVIEW:
        pl.reset()
        static, grip = build_pose(0, 'Pose')
        print('POSED', [round(v, 3) for v in pl.bounds([static])[0]], [round(v, 3) for v in pl.bounds([static])[1]],
              'grip', grip)
        marker = sl.sweep_m('Sword', [grip, (grip.x, grip.y, 0.0)], 0.015, 6, None)
        pl.setup_render((400, 600))
        out = os.path.join(dlib.REVIEW, PROP, 'pose'); os.makedirs(out, exist_ok=True)
        pl.render_views([static, marker], out, 'pose', views=((0, 10), (90, 6), (180, 6)))
    else:
        main()
