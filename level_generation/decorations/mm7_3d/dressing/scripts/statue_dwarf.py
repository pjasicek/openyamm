"""Dwarf statues 7dec54 (horned helmet, double axe held low behind, stone with gold trim) and 7dec55 (walking, pointed
cap, spiked club): the MM6 dwarf creature (assets_source/worlds/mm6/models/mm6_dwa1.glb, read only) posed into the
sprite pose (five directional views each: a0 front, a1 front three-quarter, a2 side, a3 back three-quarter, a4 back)
and baked static. Before posing, the rest mesh is reshaped toward the sprites: the beard is drawn down to the belt
and widened, the arms thickened. Procedural trim, built in the rest frame of the bone it rides on and moved with it:
7dec54 a gold helmet rim, spike and horns, gold rings on the arms and boots and a double-bladed axe in the right hand;
7dec55 a pointed cap over the head (the helmet spike removed) and the MM6 merchant's club (mm6_mer1_club.glb, read
only) in the right hand.
Stages: --preview (pose renders with the creature's own colours), --stage bake (bakes stone, occlusion and normal-z
of LOD0 into work/<prop>_bake.npy for statue_compose.py), default: build with the composed textures and export
work/<prop>_export.glb.
Usage: blender --background --python statue_dwarf.py -- <7dec54|7dec55> [--preview | --stage bake]"""
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
args = sys.argv[sys.argv.index('--') + 1:]
PROP = args[0]
PREVIEW = '--preview' in args
STAGE = args[args.index('--stage') + 1] if '--stage' in args else 'build'
DWARF = os.path.join(dlib.MODELS_MM6, 'mm6_dwa1.glb')
CLUB = os.path.join(dlib.MODELS_MM6, 'mm6_mer1_club.glb')

# World: the dwarf faces -y, his left (B_L_*) at +x. 'rot' about +x by a positive angle tilts the top forward (-y).
POSES = {
    # Standing square, legs apart, knees a little bent, arms hanging straight and away from the body with clenched
    # fists; the right hand holds the axe low beside the thigh, the haft rising backward to the head behind him.
    '7dec54': [
        ('aim', 'B_L_Thigh', (0.36, -0.16, -1), 1.0),
        ('aim', 'B_L_Calf', (0.1, 0.2, -1), 1.0),
        ('aim', 'B_L_Foot', (0.35, -1, -0.15), 1.0),
        ('aim', 'B_R_Thigh', (-0.36, -0.16, -1), 1.0),
        ('aim', 'B_R_Calf', (-0.1, 0.2, -1), 1.0),
        ('aim', 'B_R_Foot', (-0.35, -1, -0.15), 1.0),
        ('rot', 'B_Spine', (1, 0, 0), 6),
        ('rot', 'B_Spine', (0, 1, 0), -7),
        ('aim', 'B_L_UpperArm', (0.42, 0.06, -1), 1.0, 'B_L_Forearm'),
        ('aim', 'B_L_Forearm', (0.14, -0.22, -1), 1.0, 'B_L_Hand'),
        ('aim', 'B_R_UpperArm', (-0.16, 0.0, -1), 1.0, 'B_R_Forearm'),
        ('aim', 'B_R_Forearm', (-0.08, -0.08, -1), 1.0, 'B_R_Hand'),
        ('rot', 'B_Neck', (0, 1, 0), 7),
        ('rot', 'B_Head', (1, 0, 0), 8),
    ],
    # Mid-stride: right leg forward, left leg back on its toes; the right arm hangs back with the club pointing down,
    # forward and out; the left fist swings forward at belly height; leaning forward.
    '7dec55': [
        ('aim', 'B_R_Thigh', (-0.12, -0.75, -1), 1.0),
        ('aim', 'B_R_Calf', (-0.04, -0.15, -1), 1.0),
        ('aim', 'B_R_Foot', (-0.25, -1, -0.1), 1.0),
        ('aim', 'B_L_Thigh', (0.1, 0.55, -1), 1.0),
        ('aim', 'B_L_Calf', (0.05, 0.95, -1), 1.0),
        ('aim', 'B_L_Foot', (0.15, -0.5, -0.85), 1.0),
        ('rot', 'B_Spine', (1, 0, 0), 8),
        ('rot', 'B_Spine1', (0, 0, 1), -6),
        ('aim', 'B_R_UpperArm', (-0.28, 0.45, -1), 1.0, 'B_R_Forearm'),
        ('aim', 'B_R_Forearm', (-0.2, 0.12, -1), 1.0, 'B_R_Hand'),
        ('aim', 'B_L_UpperArm', (0.25, -0.5, -1), 1.0, 'B_L_Forearm'),
        ('aim', 'B_L_Forearm', (0.05, -1, 0.35), 1.0, 'B_L_Hand'),
        ('rot', 'B_Head', (1, 0, 0), -4),
    ],
}
# Weapon haft direction (world) from the right hand's grip; set by turning the hand about the wrist.
WEAPON = {'7dec54': (-0.04, 1.0, 0.3), '7dec55': (-0.42, -0.5, -1.0)}
# Beard (rest frame): head-weighted vertices in front of the neck below the mouth, drawn down by STRETCH about
# BEARD_TOP, pushed forward and widened toward the tip.
BEARD_TOP, STRETCH, BEARD_FORWARD, BEARD_WIDEN = 1.125, 2.0, 0.11, 0.35
ARM_THICKEN = {'7dec54': 1.22, '7dec55': 1.15}
TORSO_WIDEN = {'7dec54': 1.1, '7dec55': 1.12}     # the sprites' dwarves are stockier than the creature
LEG_THICKEN = 1.1
# Target colours (sRGB) measured on the sprites (all five views; gold: saturated yellow pixels).
TARGETS = {
    '7dec54': {'body': (75, 79, 65), 'gold': (132, 114, 57), 'blade': (150, 156, 140), 'haft': (40, 38, 30),
               'iron': (50, 52, 46)},
    '7dec55': {'body': (70, 75, 62), 'club': (58, 61, 50), 'cap': (82, 87, 72)},
}
LEVELS = {
    # creature LOD mesh, body triangles after decimation, trim detail level
    '7dec54': [(0, 3650, 0), (2, 1300, 1), ('far', 560, 0.014), ('far', 260, 0.014)],
    '7dec55': [(0, 3200, 0), (2, 1450, 1), ('far', 560, 0.014), ('far', 300, 0.014)],
}


# ---------------------------------------------------------------- rest-mesh reshaping
def rest_bone(arm, name):
    b = arm.data.bones[name]
    return arm.matrix_world @ b.head_local, arm.matrix_world @ b.tail_local


def reshape_rest(arm, body):
    """Beard down to the belt, thicker arms; applied to the rest mesh, so the armature carries it into the pose."""
    co = sl.coords(body)
    names = np.array(cp.strongest_bone(body))
    beard = (names == 'B_Head') & (co[:, 2] < BEARD_TOP) & (co[:, 1] < -0.03)
    t = (BEARD_TOP - co[beard, 2])                               # depth below the beard top
    new_t = t * STRETCH
    co[beard, 2] = BEARD_TOP - new_t
    frac = np.clip(new_t / (new_t.max() + 1e-6), 0, 1)
    co[beard, 1] -= BEARD_FORWARD * frac ** 1.3
    co[beard, 0] *= 1 + BEARD_WIDEN * frac
    print('BEARD verts', int(beard.sum()), 'bottom', round(float(co[beard, 2].min()), 3))
    factor = ARM_THICKEN[PROP]
    segments = {'B_L_UpperArm': ('B_L_UpperArm', 'B_L_Forearm'), 'B_L_UpperArmTwist': ('B_L_UpperArm', 'B_L_Forearm'),
                'B_L_Forearm': ('B_L_Forearm', 'B_L_Hand'), 'B_L_ForearmTwist': ('B_L_Forearm', 'B_L_Hand')}
    segments.update({k.replace('_L_', '_R_'): (a.replace('_L_', '_R_'), b.replace('_L_', '_R_'))
                     for k, (a, b) in list(segments.items())})
    for bone, (a, b) in segments.items():
        mask = names == bone
        if not mask.any():
            continue
        h = np.array(rest_bone(arm, a)[0]); e = np.array(rest_bone(arm, b)[0])
        axis = (e - h) / np.linalg.norm(e - h)
        d = co[mask] - h
        along = (d @ axis)[:, None] * axis
        co[mask] = h + along + (d - along) * factor
    torso = np.isin(names, ['B_Pelvis', 'B_Spine', 'B_Spine1', 'B_Spine2', 'B_L_Clavicle', 'B_R_Clavicle'])
    co[torso, 0] *= TORSO_WIDEN[PROP]
    co[torso, 1] = -0.018 + (co[torso, 1] + 0.018) * TORSO_WIDEN[PROP]
    for side in ('L', 'R'):
        for bone, child in ((f'B_{side}_Thigh', f'B_{side}_Calf'), (f'B_{side}_Calf', f'B_{side}_Foot')):
            mask = names == bone
            h = np.array(rest_bone(arm, bone)[0]); e = np.array(rest_bone(arm, child)[0])
            axis = (e - h) / np.linalg.norm(e - h)
            d = co[mask] - h
            along = (d @ axis)[:, None] * axis
            co[mask] = h + along + (d - along) * LEG_THICKEN
    if PROP == '7dec55':
        spike = (names == 'B_Head') & (co[:, 2] > 1.30)
        sl.set_coords(body, co)
        sl.delete_verts(body, spike)
        return
    sl.set_coords(body, co)


# ---------------------------------------------------------------- pose
def aim_socket(arm, hand, socket, direction):
    """Turn the hand about the wrist so its weapon socket bone (the creature's 'Axe' bone, along the haft) points
    along the world direction."""
    bones = arm.pose.bones
    head = arm.matrix_world @ bones[socket].head; tail = arm.matrix_world @ bones[socket].tail
    q = (tail - head).normalized().rotation_difference(Vector(direction).normalized())
    cp._apply(arm, bones[hand], q.to_matrix(), arm.matrix_world @ bones[hand].head)


def build_pose(level, name):
    """Posed static dwarf at creature LOD `level`; deform: bone -> 4x4 rest-to-pose world matrix; socket: grip
    point and haft direction."""
    for o in list(bpy.data.objects):
        if o.type == 'ARMATURE' or (o.parent and o.parent.type == 'ARMATURE'):
            bpy.data.objects.remove(o)
    arm, body = sl.load(DWARF, level)
    reshape_rest(arm, body)
    cp.pose(arm, POSES[PROP])
    aim_socket(arm, 'B_R_Hand', 'Axe', WEAPON[PROP])
    deform = {pb.name: arm.matrix_world @ pb.matrix @ arm.data.bones[pb.name].matrix_local.inverted()
              @ arm.matrix_world.inverted() for pb in arm.pose.bones}
    socket = (arm.matrix_world @ arm.pose.bones['Axe'].head,
              (arm.matrix_world @ arm.pose.bones['Axe'].tail - arm.matrix_world @ arm.pose.bones['Axe'].head)
              .normalized())
    rest = {b.name: arm.matrix_world @ arm.pose.bones[b.name].head for b in arm.data.bones}   # posed heads
    static = cp.bake(arm, body, name)
    static['bone_names'] = list(cp.strongest_bone(static))
    static.vertex_groups.clear()
    for key in ('rest', 'custom_normal'):
        if key in static.data.attributes:
            static.data.attributes.remove(static.data.attributes[key])
    for o in (arm, body):
        bpy.data.objects.remove(o)
    return static, deform, socket, rest


# ---------------------------------------------------------------- trim parts
def loft(name, centres, radii, segments, mat, tip=True):
    """Closed loft of ellipses (rx, ry) around a centreline in the yz plane (x across); u around, v along."""
    bm = bmesh.new(); uv = bm.loops.layers.uv.verify()
    rings = []
    for i, (c, (rx, ry)) in enumerate(zip(centres, radii)):
        c = Vector(c)
        t = (Vector(centres[min(i + 1, len(centres) - 1)]) - Vector(centres[max(i - 1, 0)])).normalized()
        xa = Vector((1, 0, 0)); ya = t.cross(xa).normalized()
        rings.append([bm.verts.new(c + xa * math.cos(a) * rx + ya * math.sin(a) * ry)
                      for a in (2 * math.pi * s / segments for s in range(segments))])
    for i in range(len(rings) - 1):
        for s in range(segments):
            s2 = (s + 1) % segments
            f = bm.faces.new((rings[i][s], rings[i][s2], rings[i + 1][s2], rings[i + 1][s]))
            for loop, (a, b) in zip(f.loops, ((s, i), (s + 1, i), (s + 1, i + 1), (s, i + 1))):
                loop[uv].uv = (a / segments * 2, b * 0.25)
    if tip:
        end = bm.verts.new(Vector(centres[-1]) + (Vector(centres[-1]) - Vector(centres[-2])).normalized() * 0.01)
        for s in range(segments):
            f = bm.faces.new((rings[-1][s], rings[-1][(s + 1) % segments], end))
            for loop in f.loops:
                loop[uv].uv = (0.5, 0.5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return pl.to_object(name, bm, mat, True)


def transform(obj, matrix):
    obj.data.transform(matrix); obj.data.update()
    return obj


def cap(detail, mat):
    """7dec55's pointed cap (rest frame of the head): a rolled band at the brow, the crown rising over the helmet dome
    and its tip flopping forward."""
    seg = (16, 10, 6, 5)[detail]
    centres = [(0, 0.0, 1.185), (0, 0.0, 1.205), (0, 0.0, 1.228), (0, 0.004, 1.236), (0, 0.01, 1.275),
               (0, 0.006, 1.31), (0, -0.01, 1.34), (0, -0.045, 1.36), (0, -0.085, 1.357), (0, -0.118, 1.335)]
    radii = [(0.126, 0.15), (0.136, 0.16), (0.132, 0.156), (0.12, 0.143), (0.108, 0.126), (0.088, 0.098),
             (0.062, 0.066), (0.044, 0.044), (0.032, 0.032), (0.022, 0.022)]
    if detail >= 2:
        keep = [0, 2, 4, 6, 8, 9]
        centres = [centres[k] for k in keep]; radii = [radii[k] for k in keep]
    return loft('Cap', centres, radii, seg, mat)


def ring_on(head, end, t, width, thick, segments, mat, limb_co, pad=-0.002):
    """A ring around a posed limb at fraction t from the posed bone head to the child's head: axis along the bone,
    radius fitted to the limb's vertices in a thin slice there (70th percentile, so flares and pads do not widen it)."""
    head, end = np.array(head), np.array(end)
    ax = (end - head) / np.linalg.norm(end - head)
    c = head + (end - head) * t
    d = limb_co - c
    along = d @ ax
    radial = np.linalg.norm(d - along[:, None] * ax, axis=1)
    near = (np.abs(along) < 0.012) & (radial < 0.16)
    if near.sum() < 6:
        return None
    r = float(np.percentile(radial[near], 55)) + pad
    return sl.ring_around(f'Ring{t}', Vector(c), Vector(ax), r, width, thick, segments, mat)


def smooth_path(points, count):
    """Catmull-Rom resampling of a polyline to `count` points (ends kept)."""
    pts = [Vector(p) for p in points]
    ext = [pts[0] * 2 - pts[1]] + pts + [pts[-1] * 2 - pts[-2]]
    out = []
    for i in range(count):
        t = i / (count - 1) * (len(pts) - 1)
        k = min(int(t), len(pts) - 2); u = t - k
        p0, p1, p2, p3 = ext[k], ext[k + 1], ext[k + 2], ext[k + 3]
        out.append(0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u +
                          (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3))
    return out


# Horn centreline (x out, y back, z up; rest frame of the head), traced on 7dec54a0 and a2: from the dome's side out
# and up, the tip turning upward and leaning a little back.
HORN = [(0.092, 0.0, 1.298), (0.135, 0.004, 1.315), (0.168, 0.01, 1.345), (0.184, 0.018, 1.385),
        (0.186, 0.026, 1.425), (0.18, 0.033, 1.46), (0.171, 0.038, 1.484)]
HORN_BASE = 0.027


def horned_helmet(detail, mats):
    """7dec54 (rest frame of the head): a dark iron dome over the creature's helmet, a gold rim band, a gold spike
    on top and two round, tapering, curved gold horns with collars at their roots."""
    parts = []
    seg = (20, 12, 8, 6)[detail]
    dome = pl.lathe('Dome', [(0.113, 1.236), (0.11, 1.27), (0.1, 1.3), (0.082, 1.325), (0.052, 1.343), (0.02, 1.352),
                             (0.0, 1.353)], seg, mats['Iron'], u_repeat=2.0, v_scale=6.0)
    dome.scale = (1.0, 1.15, 1.0); dlib.apply(dome)
    parts.append(dome)
    rim = sl.ring_around('Rim', (0.0, 0.0, 1.238), (0, 0, 1), 0.117, 0.03, 0.011, seg, mats['Gold'])
    rim.scale = (1.0, 1.12, 1.0); dlib.apply(rim)
    parts.append(rim)
    if detail < 3:
        parts.append(sl.sweep_m('Spike', [(0, 0.0, 1.335), (0, 0.0, 1.37), (0, 0.0, 1.46)], [0.026, 0.018, 0.003],
                                (8, 6, 5)[detail], mats['Gold']))
    hseg = (10, 8, 5, 4)[detail]
    steps = (10, 7, 5, 4)[detail]
    for sign in (1, -1):
        path = smooth_path([(sign * x, y, z) for x, y, z in HORN], steps)
        rad = [HORN_BASE * (1 - k / (steps - 1)) ** 0.85 + 0.002 for k in range(steps)]
        parts.append(sl.sweep_m(f'Horn{sign}', path, rad, hseg, mats['Gold']))
        if detail < 2:
            axis = (path[1] - path[0]).normalized()
            parts.append(sl.ring_around(f'Collar{sign}', path[0] + axis * 0.012, axis, HORN_BASE * 0.95, 0.014,
                                        0.006, hseg + 2, mats['Gold']))
    return parts


def blade(name, s0, s1, reach, thick, detail, mat):
    """One crescent axe blade in the (s, t) plane: s along the haft, t away from it; its edge is an arc from s0-0.04
    to s1+0.04 at `reach`; the top and bottom outlines are concave."""
    n_a = (9, 6, 4, 3)[detail]; n_b = (4, 3, 2, 1)[detail]
    bm = bmesh.new(); uv = bm.loops.layers.uv.verify()
    grid = []
    mid = (s0 + s1) / 2; half = (s1 - s0) / 2
    for j in range(n_b + 1):
        b = j / n_b
        row = []
        for i in range(n_a + 1):
            a = -1 + 2 * i / n_a
            # haft side: half width `half`; edge: wider (flared tips), bulging outward at the centre
            width = half * (1 + 0.9 * b ** 1.6)
            s = mid + a * width
            t = reach * b * (1 - 0.1 * a * a * b) + 0.025 * b * (1 - a * a)
            th = thick * (1 - 0.75 * b)
            row.append(((s, t), th, (i / n_a, b)))
        grid.append(row)
    verts = {}
    for side in (1, -1):
        for j, row in enumerate(grid):
            for i, ((s, t), th, _) in enumerate(row):
                verts[(side, j, i)] = bm.verts.new((s, t, side * th / 2))
    for side in (1, -1):
        for j in range(n_b):
            for i in range(n_a):
                quad = [(side, j, i), (side, j, i + 1), (side, j + 1, i + 1), (side, j + 1, i)]
                if side < 0:
                    quad.reverse()
                f = bm.faces.new([verts[q] for q in quad])
                for loop, q in zip(f.loops, quad):
                    loop[uv].uv = grid[q[1]][q[2]][2]
    # rim faces round the outline (the haft side stays open inside the haft)
    outline = [(n_b, i) for i in range(n_a + 1)] + [(j, n_a) for j in range(n_b - 1, -1, -1)]
    outline = [(j, 0) for j in range(0, n_b + 1)] + [(n_b, i) for i in range(1, n_a + 1)] + \
        [(j, n_a) for j in range(n_b - 1, -1, -1)]
    for (j0, i0), (j1, i1) in zip(outline, outline[1:]):
        f = bm.faces.new([verts[(1, j0, i0)], verts[(1, j1, i1)], verts[(-1, j1, i1)], verts[(-1, j0, i0)]])
        for loop in f.loops:
            loop[uv].uv = (0.5, 0.5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return pl.to_object(name, bm, mat, False)


def axe(detail, mats, grip, haft):
    """7dec54's double axe in world space: dark haft from a gold butt knob just ahead of the hand, gold rings, a
    double crescent head in the vertical plane through the haft."""
    haft = Vector(haft).normalized()
    up = Vector((0, 0, 1)); up = (up - haft * up.dot(haft)).normalized()
    across = haft.cross(up)
    frame = Matrix((haft, up, across)).transposed()             # columns: s, t, thickness
    to_world = Matrix.Translation(grip) @ frame.to_4x4()
    sides = (8, 6, 4, 3)[detail]
    parts = [sl.sweep_m('Haft', [grip - haft * 0.07, grip + haft * 0.68], 0.017, sides, mats['Haft'])]
    if detail < 3:
        parts.append(sl.sweep_m('Knob', [grip - haft * 0.1, grip - haft * 0.075, grip - haft * 0.06],
                                [0.012, 0.03, 0.022], sides, mats['Gold']))
        for k, s in enumerate((0.07, 0.24, 0.40) if detail < 2 else (0.24,)):
            parts.append(sl.ring_around(f'HaftRing{k}', grip + haft * s, haft, 0.017, 0.022, 0.008, sides,
                                        mats['Gold']))
        parts.append(sl.sweep_m('Cap', [grip + haft * 0.66, grip + haft * 0.70], [0.022, 0.012], sides, mats['Gold']))
    for sign in (1, -1):
        b = blade(f'Blade{sign}', 0.46, 0.60, 0.20, 0.03, detail, mats['Blade'])
        if sign < 0:
            transform(b, Matrix.Scale(-1, 4, Vector((0, 1, 0))))
            bm = bmesh.new(); bm.from_mesh(b.data); bmesh.ops.reverse_faces(bm, faces=bm.faces)
            bm.to_mesh(b.data); bm.free()
        parts.append(transform(b, to_world))
    return parts


def cudgel(detail, mat, grip, haft):
    """7dec55's club: a gnarled cudgel swept along the haft (a short butt behind the fist, a thin grip swelling to
    a heavy rounded head), with knobs on the head."""
    profile = [(-0.07, 0.016), (-0.06, 0.024), (0.0, 0.024), (0.12, 0.028), (0.26, 0.042), (0.4, 0.06),
               (0.5, 0.068), (0.57, 0.062), (0.61, 0.04), (0.625, 0.012)]
    if detail >= 2:
        profile = profile[1::2] + [profile[-1]]
    pts = [grip + haft * s for s, _ in profile]
    obj = sl.sweep_m('Cudgel', pts, [r for _, r in profile], (10, 7, 5, 4)[detail], mat)
    parts = [obj]
    if detail < 2:
        parts += club_knobs(obj, grip, haft, (16, 9)[detail], mat)
    return parts


def club_knobs(obj, base, axis, count, mat):
    """Knobs on the club's head (outer 45 % of its length), cast outward from the axis onto the surface."""
    from mathutils.bvhtree import BVHTree
    bvh = BVHTree.FromObject(obj, bpy.context.evaluated_depsgraph_get())
    co = sl.coords(obj); along = (co - np.array(base)) @ np.array(axis)
    length = float(along.max())
    side = axis.orthogonal().normalized(); other = axis.cross(side)
    rng = np.random.default_rng(7)
    knobs = []
    for k in range(count):
        t = 0.5 + 0.42 * (k + 0.5) / count
        a = 2.4 * k + rng.uniform(-0.3, 0.3)
        d = (side * math.cos(a) + other * math.sin(a)).normalized()
        origin = base + axis * (length * t)
        hit = bvh.ray_cast(origin + d * 0.3, -d, 0.6)
        if hit[0] is None:
            continue
        knobs.append(hl.rivet(f'Knob{k}', hit[0] * dlib.UNITS_PER_METRE, hit[1], 2.2, mat))
    return knobs


def club_meshes():
    """The club GLB's four LOD meshes (1122 / 290 / 252 / 200 triangles), each imported through a copy whose node
    shows it."""
    meshes = []
    for index in range(4):
        before_meshes = set(bpy.data.meshes); before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=sl.level_glb(CLUB, index))
        for o in [o for o in bpy.data.objects if o not in before]:
            bpy.data.objects.remove(o)
        meshes.append(next(m for m in bpy.data.meshes if m not in before_meshes))
    return meshes


# ---------------------------------------------------------------- materials and build
def materials(stage):
    if stage == 'bake':
        m = bpy.data.materials.new('Plain')
        return {k: m for k in ('Gold', 'Haft', 'Blade', 'Club', 'Cap', 'Body', 'Iron')}
    tile = 'statue_stone'
    return {'Body': dlib.material('Stone', f'statue_{PROP}', extras={'openyamm_specular': 0.35}),
            'Gold': dlib.material('Gold', 'gold', extras={'openyamm_specular': 0.8}),
            'Haft': dlib.material('Haft', tile, extras={'openyamm_specular': 0.3}),
            'Blade': dlib.material('Blade', 'statue_stonelight', extras={'openyamm_specular': 0.4}),
            'Club': dlib.material('Club', tile, extras={'openyamm_specular': 0.3}),
            'Cap': dlib.material('Cap', tile, extras={'openyamm_specular': 0.3}),
            'Iron': dlib.material('Iron', tile, extras={'openyamm_specular': 0.7})}


def level(index, mats, clubs):
    src, body_tris, detail = LEVELS[PROP][index]
    name = 'Statue' if index == 0 else f'Statue_LOD{index}'
    body, deform, (grip, haft), posed_joints = build_pose(src, f'Body{index}')
    SOCKET.append((grip, haft))
    sl.single_material(body, mats['Body'])
    body_co, body_names = sl.coords(body), np.array(body['bone_names'])
    del body['bone_names']
    sl.decimate(body, body_tris)
    groups = {'body': [body]}
    head = deform['B_Head']
    if PROP == '7dec54':
        head_rims.append((head @ Vector((0, 0, 1.226)), (head.to_3x3() @ Vector((0, 0, 1))).normalized()))
        helmet = horned_helmet(detail, mats)
        for p in helmet:
            transform(p, head)
        groups['gold'] = helmet
        # Rings on the arms and boots, fitted to the posed body.
        seg = (14, 10, 7, 5)[detail]
        rings = []
        if detail < 3:
            for side in ('L', 'R'):
                specs = [(f'B_{side}_Forearm', f'B_{side}_Hand', 0.12, 0.03),
                         (f'B_{side}_Forearm', f'B_{side}_Hand', 0.7, 0.026),
                         (f'B_{side}_UpperArm', f'B_{side}_Forearm', 0.8, 0.026),
                         (f'B_{side}_Calf', f'B_{side}_Foot', 0.22, 0.03)]
                if detail >= 1:
                    specs = specs[0::3] if detail == 2 else specs[:2] + specs[3:]
                for bone, child, t, width in specs:
                    limb = np.isin(body_names, [bone, bone + 'Twist'])
                    r = ring_on(posed_joints[bone], posed_joints[child], t, width, 0.012, seg, mats['Gold'],
                                body_co[limb])
                    if r is not None:
                        rings.append(r)
        groups['gold'] += rings
        weapon = axe(detail, mats, grip, haft)
        groups['blade'] = [p for p in weapon if p.name.startswith('Blade')]
        groups['haft'] = [p for p in weapon if p.name.startswith('Haft') and not p.name.startswith('HaftRing')]
        groups['gold'] += [p for p in weapon if p not in groups['blade'] and p not in groups['haft']]
    else:
        c = cap(detail, mats['Cap'])
        groups['cap'] = [transform(c, head)]
        groups['club'] = cudgel(detail, mats['Club'], grip, Vector(haft).normalized())
    return name, groups


head_rims = []           # (rim centre, head up) per level, posed world, before the ground shift


def helmet_iron(obj, rim, dark=0.35):
    """7dec54's helmet dome is dark iron in the sprite: darken the body above the gold rim inside the helmet."""
    centre, up = rim
    centre = centre + SHIFT[0]
    me = obj.data
    colour = me.color_attributes['Color']
    c = np.empty(len(me.vertices) * 4, np.float32); colour.data.foreach_get('color', c); c = c.reshape(-1, 4)
    index = [m.name for m in me.materials].index('Stone')
    stone = np.zeros(len(me.vertices), bool)
    for polygon in me.polygons:
        if polygon.material_index == index:
            stone[list(polygon.vertices)] = True
    d = sl.coords(obj) - np.array(centre)
    w = stone & (d @ np.array(up) > 0.008) & (np.linalg.norm(d, axis=1) < 0.2)
    c[w, :3] *= dark
    print('HELMET darkened', int(w.sum()), 'of', len(w))
    colour.data.foreach_set('color', c.ravel())


SHIFT = [Vector()]
SOCKET = []              # (grip, haft) per built level
BOOTS = {'7dec54': (0.27, 0.33, 0.55), '7dec55': (0.25, 0.31, 0.45)}   # z ramp (m) and the boots' darkening


def boots(obj):
    """The sprites' boots are darker than the clothes: darken the body's COLOR_0 below the boot tops."""
    z0, z1, dark = BOOTS[PROP]
    me = obj.data
    colour = me.color_attributes['Color']
    c = np.empty(len(me.vertices) * 4, np.float32); colour.data.foreach_get('color', c); c = c.reshape(-1, 4)
    stone = np.zeros(len(me.vertices), bool)
    index = [m.name for m in me.materials].index('Stone')
    for polygon in me.polygons:
        if polygon.material_index == index:
            stone[list(polygon.vertices)] = True
    z = sl.coords(obj)[:, 2]
    w = np.clip((z1 - z) / (z1 - z0), 0, 1) * stone
    c[:, :3] *= (1 - (1 - dark) * w)[:, None]
    colour.data.foreach_set('color', c.ravel())


def tint_table():
    import json
    t = TARGETS[PROP]
    exposed = json.load(open(os.path.join(dlib.WORK, f'{PROP}_texture.json')))['exposed_mean']
    table = {'Stone': (t['body'], exposed)}
    for key, mat in (('iron', 'Iron'), ('gold', 'Gold'), ('blade', 'Blade'), ('haft', 'Haft'), ('club', 'Club'), ('cap', 'Cap')):
        if key in t:
            table[mat] = (t[key], None)
    return table


def main():
    pl.reset()
    mats = materials(STAGE)
    clubs = []
    count = 1 if STAGE == 'bake' else len([lv for lv in LEVELS[PROP] if lv[0] != 'far'])
    built = []
    for index in range(count):
        built.append(level(index, mats, clubs))
    # Ground: lowest point of LOD0 on z = 0 for every level, centred on the feet (x, y of the body's base).
    body0 = built[0][1]['body'][0]
    co = sl.coords(body0)
    low = co[co[:, 2] < co[:, 2].min() + 0.08]
    shift = Vector((-float(low[:, 0].mean()), -float(low[:, 1].mean()), -float(co[:, 2].min())))
    SHIFT[0] = shift
    if STAGE == 'bake':
        bake_size = (1040, 512)
        for group in built[0][1].values():
            for p in group:
                transform(p, Matrix.Translation(shift))
        sl.smooth(body0, 70)                              # shading normals as exported (flat faces bake facets)
        sl.stone_bake(body0, os.path.join(dlib.WORK, f'{PROP}_bake.npy'), bake_size)
        return
    t = TARGETS[PROP]
    lods = []
    for name, groups in built:
        parts = []
        for key, objs in groups.items():
            for p in objs:
                transform(p, Matrix.Translation(shift))
            parts += objs
        joined = pl.join(name, parts)
        sl.smooth(joined, 70)
        pl.vertex_occlusion(joined, rays=(32, 20, 12, 8)[len(lods)], distance=0.12, strength=0.55, floor=True)
        sl.tint_groups(joined, tint_table(), keep={'Stone': 0.35})
        boots(joined)
        lods.append(joined)
    far_mat = dlib.material('StoneFar', 'statue_stone', extras={'openyamm_specular': 0.3})
    for index, (kind, target, voxel) in enumerate(LEVELS[PROP]):
        if kind == 'far':
            far = sl.far_lod(lods[1], f'Statue_LOD{index}', target, voxel, far_mat)
            if PROP == '7dec54':
                # the thin axe vanishes in the remesh: add its coarsest build (haft strip and two blades)
                grip, haft = SOCKET[0]
                parts = axe(3, mats, grip + SHIFT[0], haft)
                tool = pl.join(f'Axe{index}', parts)
                pl.vertex_occlusion(tool, rays=8, distance=0.12, strength=0.55, floor=True)
                sl.tint_groups(tool, tint_table())
                far = pl.join(far.name, [far, tool])
            lods.append(far)
    # every level on the ground (LOD0's lowest point at zero; coarser levels follow their own lowest point)
    for o in lods[1:]:
        low = min(v.co.z for v in o.data.vertices)
        o.data.transform(Matrix.Translation((0, 0, -low)))
    dlib.save(PROP, lods)


if __name__ == '__main__':
    if PREVIEW:
        pl.reset()
        static, deform, (grip, haft), rest = build_pose(0, 'Pose')
        lo, hi = pl.bounds([static])
        print('POSED', [round(v, 3) for v in lo], [round(v, 3) for v in hi], 'grip', grip, 'haft', haft)
        marker = sl.sweep_m('Haft', [grip - haft * 0.1, grip + haft * 0.7], 0.015, 6, None)
        pl.setup_render((400, 600))
        out = os.path.join(dlib.REVIEW, PROP, 'pose'); os.makedirs(out, exist_ok=True)
        pl.render_views([static, marker], out, 'pose', views=tuple((y, 6) for y in range(0, 360, 45)))
    else:
        main()
