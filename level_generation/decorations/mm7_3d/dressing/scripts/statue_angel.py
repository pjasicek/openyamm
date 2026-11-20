"""dec94: a weathered stone statue of a winged woman on a two-tier plinth (outdoor, 7out06, one placement). The sprite
shows her in three-quarter view facing right, hands on her hips, head turned up, two feathered wings spread up and
back. The figure is an MPFB2 (MakeHuman) female base mesh (CC0), made headless with MPFB's Mixamo rig. That rig's arms rest in a T-pose while the basemesh's
arms hang in an A-pose, so the arm bones' rest is first refitted to the mesh (joints at the weight boundaries), posed with
world-space bone operations and baked static, with a hair cap and bun. Wings and plinth are procedural: each wing a
tapered arm with rows of flat feather slabs (coverts, secondaries, long splayed primaries).
Surfaces: the body baked (occlusion, up, box-projected Poly Haven rock_surface grain, CC0) and recoloured through the
sprite's figure ramp (statue_compose.py); wings, hair and plinth use the CC0 rock tiles, tinted.
Stages: --preview, --stage bake, default build (work/dec94_export.glb).
Usage: blender --background --python statue_angel.py -- [--preview | --stage bake]"""
import math
import os
import sys

import addon_utils
import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import statue_lib as sl  # noqa: E402

dlib, pl, hl, cp = sl.dlib, sl.pl, sl.hl, sl.cp
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
PROP = 'dec94'
PREVIEW = '--preview' in args
STAGE = args[args.index('--stage') + 1] if '--stage' in args else 'build'
M = 'mixamorig:'
MACRO = {'gender': 0.0, 'muscle': 0.5, 'weight': 0.42, 'proportions': 0.8, 'height': 0.55, 'cupsize': 0.5,
         'firmness': 0.6}
# Standing on the left leg, the right foot a little forward; hands on the hips with the elbows out and back; the
# chest lifted, the head turned to her left (screen right in the sprite's view) and up. She faces -y.
POSE = [
    ('aim', M + 'LeftUpLeg', (0.03, 0.02, -1), 1.0),
    ('aim', M + 'LeftLeg', (0.0, 0.05, -1), 1.0),
    ('aim', M + 'RightUpLeg', (-0.06, -0.16, -1), 1.0),
    ('aim', M + 'RightLeg', (-0.02, 0.0, -1), 1.0),
    ('rot', M + 'Hips', (0, 1, 0), 3),
    ('rot', M + 'Spine1', (1, 0, 0), -6),
    ('rot', M + 'Spine2', (0, 1, 0), -4),
    ('aim', M + 'LeftArm', (0.55, 0.3, -0.78), 1.0),
    ('aim', M + 'LeftForeArm', (-0.62, -0.35, -0.7), 1.0),
    ('aim', M + 'LeftHand', (-0.1, -0.35, -0.93), 1.0),
    ('aim', M + 'RightArm', (-0.55, 0.3, -0.78), 1.0),
    ('aim', M + 'RightForeArm', (0.62, -0.35, -0.7), 1.0),
    ('aim', M + 'RightHand', (0.1, -0.35, -0.93), 1.0),
    ('rot', M + 'Head', (0, 0, 1), 32),
    ('rot', M + 'Head', (1, 0, 0), -22),
]
LEVELS = [(3300, 0), (1150, 1), ('far', 340, 0.012), ('far', 200, 0.012)]
PLINTH = {'lower': (1.0, 0.8, 0.46), 'upper': (0.84, 0.66, 0.06)}   # a block and a thin top slab: 23 % of the height, as the sprite
# Sprite means (sRGB) of the figure rows and the plinth rows of dec94_p2; outdoor grade per channel.
TARGETS = {'body': (90, 81, 68), 'wing': (86, 77, 64), 'plinth': (103, 94, 82)}
GAIN = (0.88, 0.85, 0.8)


def human():
    addon_utils.enable('bl_ext.blender_org.mpfb', default_set=True)
    from bl_ext.blender_org.mpfb.services.humanservice import HumanService
    from bl_ext.blender_org.mpfb.services.targetservice import TargetService
    macro = TargetService.get_default_macro_info_dict()
    macro.update(MACRO)
    body = HumanService.create_human(mask_helpers=True, detailed_helpers=False, macro_detail_dict=macro, scale=0.1)
    arm = HumanService.add_builtin_rig(body, 'mixamo')
    fit_arm_rest(arm, body)
    # keep the deforming armature last: apply the helper mask now
    bpy.ops.object.select_all(action='DESELECT'); body.select_set(True); bpy.context.view_layer.objects.active = body
    if body.data.shape_keys:                          # the macro targets: bake them into the base shape
        bpy.ops.object.shape_key_remove(all=True, apply_mix=True)
    for mod in list(body.modifiers):
        if mod.type == 'MASK':
            bpy.ops.object.modifier_apply(modifier=mod.name)
    for pb in arm.pose.bones:
        pb.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()
    return arm, body


def fit_arm_rest(arm, body):
    """Move the arm bones' rest onto the mesh's A-pose arms: elbow and wrist at the centroids of the vertices shared
    by the neighbouring bones' weights (the armature then deforms from the mesh's real rest)."""
    co = np.array([body.matrix_world @ v.co for v in body.data.vertices])

    def weights(name):
        gi = body.vertex_groups[name].index
        return np.array([next((g.weight for g in v.groups if g.group == gi), 0.0) for v in body.data.vertices])

    joints = {}
    for side in ('Left', 'Right'):
        upper, fore, hand = weights(M + side + 'Arm'), weights(M + side + 'ForeArm'), weights(M + side + 'Hand')
        elbow = co[(upper > 0.2) & (fore > 0.2)].mean(0)
        wrist = co[(fore > 0.2) & (hand > 0.2)].mean(0)
        joints[side] = (Vector(elbow), Vector(wrist))
    bpy.ops.object.select_all(action='DESELECT'); arm.select_set(True); bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='EDIT')
    inv = arm.matrix_world.inverted()
    eb = arm.data.edit_bones
    for side, (elbow, wrist) in joints.items():
        e, w = inv @ elbow, inv @ wrist
        eb[M + side + 'Arm'].tail = e
        eb[M + side + 'ForeArm'].head = e
        eb[M + side + 'ForeArm'].tail = w
        h = eb[M + side + 'Hand']
        h.head = w
        h.tail = w + (w - e).normalized() * 0.08
    bpy.ops.object.mode_set(mode='OBJECT')
    print('ARM REST refitted', {k: [tuple(round(x, 3) for x in v) for v in vs] for k, vs in joints.items()})


def build_pose():
    arm, body = human()
    cp.pose(arm, POSE)
    j = {pb.name: (arm.matrix_world @ pb.head, arm.matrix_world @ pb.tail) for pb in arm.pose.bones}
    head_m = arm.matrix_world @ arm.pose.bones[M + 'Head'].matrix @ arm.data.bones[M + 'Head'].matrix_local.inverted()
    chest_m = arm.matrix_world @ arm.pose.bones[M + 'Spine2'].matrix @ \
        arm.data.bones[M + 'Spine2'].matrix_local.inverted()
    static = cp.bake(arm, body, 'Body')
    static.vertex_groups.clear()
    for key in ('rest', 'custom_normal'):
        if key in static.data.attributes:
            static.data.attributes.remove(static.data.attributes[key])
    bpy.data.objects.remove(body); bpy.data.objects.remove(arm)
    return static, j, head_m, chest_m


BODY = []                # the posed body, for snapping hair strands onto the scalp


def snap(point, centre, lift=0.006):
    """Move a posed point onto the posed body's surface along the ray from the head centre (plus a lift)."""
    from mathutils.bvhtree import BVHTree
    if not BODY:
        return point
    if len(BODY) == 1:
        BODY.append(BVHTree.FromObject(BODY[0], bpy.context.evaluated_depsgraph_get()))
    d = (point - centre).normalized()
    hit = BODY[1].ray_cast(centre + d * 0.3, -d, 0.3)
    return hit[0] + d * lift if hit[0] is not None else point


def hair(detail, mat, head_m, head_top):
    """A close cap over the cranium and a bun at the back of the head (rest frame, moved with the head)."""
    seg = (14, 10, 6, 5)[detail]
    z = head_top
    parts = []
    cap = pl.lathe('HairCap', [(0.0, z + 0.008), (0.05, z + 0.0), (0.082, z - 0.04), (0.094, z - 0.085),
                               (0.09, z - 0.12)], seg, mat, u_repeat=2.0, v_scale=6.0)
    cap.scale = (0.98, 1.1, 1.0); cap.location = (0, 0.006, 0); dlib.apply(cap)
    # open the cap's face side: drop the vertices in front below the hairline
    bm = bmesh.new(); bm.from_mesh(cap.data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.y < -0.035 and v.co.z < z - 0.05], context='VERTS')
    bm.to_mesh(cap.data); bm.free()
    parts.append(cap)
    if detail < 3:
        bun = pl.lathe('Bun', [(0.0, -0.035), (0.03, -0.028), (0.042, 0.0), (0.03, 0.028), (0.0, 0.035)],
                       (10, 8, 6)[detail], mat, smooth=True)
        bun.rotation_euler = (math.radians(70), 0, 0); bun.location = (0, 0.1, z - 0.07); dlib.apply(bun)
        parts.append(bun)
    if detail < 2:
        # carved strands pulled back from the hairline over the crown to the bun (rev 2: the cap alone read bald)
        centre = Vector((0.0, 0.006, z - 0.085))
        radii = Vector((0.094 * 0.98, 0.094 * 1.1, 0.093))
        count = (11, 7)[detail]
        for k in range(count):
            phi = math.radians(-62 + 124 * k / (count - 1))
            pts = []
            for a in np.linspace(math.radians(28), math.radians(152), (9, 6)[detail]):
                v = Vector((0.0, -math.cos(a), math.sin(a)))
                v = Vector((v.z * math.sin(phi), v.y, v.z * math.cos(phi)))     # rotated about the y axis
                pts.append(centre + Vector((v.x * radii.x, v.y * radii.y, v.z * radii.z)) * 1.035)
            pts[-1] = pts[-1].lerp(Vector((0.0, 0.1, z - 0.07)), 0.5)          # gathered into the bun
            pts = [snap(head_m @ p, head_m @ centre) for p in pts]
            strand = sl.sweep_m(f'Strand{k}', pts, [0.008] * (len(pts) - 1) + [0.004], 4, mat, flat=0.6)
            strand.data.transform(head_m.inverted())          # back to the rest frame (moved below with the rest)
            parts.append(strand)
    for p in parts:
        p.data.transform(head_m)
        for poly in p.data.polygons:
            poly.use_smooth = True
    return parts


def feather(name, root, direction, length, width, normal, detail, mat, curl=0.12):
    """One flat feather slab from root along direction (curling toward -normal), tapering to a point."""
    d = Vector(direction).normalized(); n = Vector(normal).normalized()
    steps = (4, 3, 2, 1)[detail]
    pts, radii = [], []
    for k in range(steps + 1):
        t = k / steps
        pts.append(Vector(root) + d * (length * t) - n * (curl * length * t * t))
        radii.append(width * (0.55 + 0.6 * math.sin(math.pi * min(1.0, t * 1.15 + 0.1))) * (1 - 0.85 * t ** 3))
    obj = sl.sweep_m(name, pts, radii, 4, mat, flat=0.16, caps=detail < 2, up=n)
    return obj


def wing(sign, detail, mat, chest_m):
    """A wing in the chest's frame: root on the shoulder blade, the arm rising up, back and out; feathers fan
    from the arm, the long primaries splayed at the tip (the sprite's fingered silhouette)."""
    root = Vector((sign * 0.07, 0.11, 1.33))
    elbow = root + Vector((sign * 0.13, 0.2, 0.13))
    wrist = elbow + Vector((sign * 0.06, 0.21, 0.11))
    tip = wrist + Vector((sign * 0.02, 0.12, 0.06))
    arm_pts = [root, elbow, wrist, tip]
    parts = [sl.sweep_m(f'WingArm{sign}', arm_pts, [0.04, 0.035, 0.026, 0.01], (6, 5, 4, 3)[detail], mat, flat=0.55)]
    # the wing plane: spanned by the arm and the 'down-back' direction the feathers hang along
    plane_n = (wrist - root).cross(Vector((0, 1, -0.6))).normalized()
    if plane_n.x * sign < 0:
        plane_n = -plane_n
    counts = {'covert': (7, 5, 3, 2), 'secondary': (8, 5, 4, 3), 'primary': (8, 6, 5, 4)}
    rows = []
    # coverts along the inner arm: short, hanging back-down
    for k in range(counts['covert'][detail]):
        t = (k + 0.5) / counts['covert'][detail]
        p = root.lerp(elbow, t) if t < 0.6 else elbow.lerp(wrist, (t - 0.6) / 0.4)
        rows.append(('Cov', p, Vector((sign * 0.1, 0.75, -0.6)), 0.14 + 0.06 * t, 0.04))
    # secondaries from the forearm: longer, pointing back
    for k in range(counts['secondary'][detail]):
        t = (k + 0.5) / counts['secondary'][detail]
        p = root.lerp(elbow, 0.5 + 0.5 * t) if t < 0.5 else elbow.lerp(wrist, (t - 0.5) * 2)
        a = math.radians(-55 + 30 * t)
        rows.append(('Sec', p, Vector((sign * 0.15, math.cos(a), math.sin(a))), 0.28 + 0.08 * t, 0.042))
    # primaries from the hand: long, splayed from back-up to up
    for k in range(counts['primary'][detail]):
        t = (k + 0.5) / counts['primary'][detail]
        p = wrist.lerp(tip, t)
        a = math.radians(-22 + 55 * t)
        rows.append(('Pri', p, Vector((sign * (0.1 + 0.1 * t), math.cos(a), math.sin(a))), 0.36 + 0.08 * math.sin(
            math.pi * t), 0.036))
    for k, (kind, p, d, length, width) in enumerate(rows):
        parts.append(feather(f'{kind}{sign}{k}', p, d, length, width, plane_n, detail, mat))
    for o in parts:
        o.data.transform(chest_m)
    return parts


def wing_fan(sign, mat, chest_m, thickness=0.012):
    """The coarsest wing: its outline (arm on top, the feather tips round the back) as a thin two-faced fan."""
    root = Vector((sign * 0.07, 0.11, 1.33))
    elbow = root + Vector((sign * 0.13, 0.2, 0.13))
    wrist = elbow + Vector((sign * 0.06, 0.21, 0.11))
    tip = wrist + Vector((sign * 0.02, 0.12, 0.06))
    outline = [elbow, wrist, tip, tip + Vector((sign * 0.06, 0.34, 0.12)), tip + Vector((sign * 0.05, 0.36, -0.12)),
               wrist + Vector((sign * 0.05, 0.3, -0.3)), elbow + Vector((sign * 0.04, 0.2, -0.3)),
               root + Vector((sign * 0.02, 0.1, -0.18))]
    normal = (wrist - root).cross(Vector((0, 1, -0.6))).normalized() * thickness / 2
    bm = bmesh.new(); uv = bm.loops.layers.uv.verify()
    for side in (1, -1):
        centre = bm.verts.new(root + normal * side)
        ring = [bm.verts.new(p + normal * side) for p in outline]
        for a, b in zip(ring, ring[1:]):
            f = bm.faces.new((centre, a, b) if side > 0 else (centre, b, a))
            for loop in f.loops:
                loop[uv].uv = (loop.vert.co.y * 2, loop.vert.co.z * 2)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = pl.to_object(f'Fan{sign}', bm, mat, False)
    obj.data.transform(chest_m)
    return obj


def box(name, w, d, z0, z1, mat):
    return pl.box(name, (0, 0, (z0 + z1) / 2), (w, d, z1 - z0), mat, uv_scale=2.0)


def plinth(mat):
    lw, ld, lh = PLINTH['lower']; uw, ud, uh = PLINTH['upper']
    return [box('PlinthLower', lw, ld, 0.0, lh, mat), box('PlinthUpper', uw, ud, lh, lh + uh, mat)]


def materials(stage):
    if stage == 'bake':
        m = bpy.data.materials.new('Plain'); return {k: m for k in ('Body', 'Wing', 'Plinth', 'Hair')}
    return {'Body': dlib.material('Stone', 'statue_dec94', extras={'openyamm_specular': 0.3}),
            'Wing': dlib.material('Wing', 'statue_granite', extras={'openyamm_specular': 0.3}),
            'Hair': dlib.material('Hair', 'statue_granite', extras={'openyamm_specular': 0.3}),
            'Plinth': dlib.material('Plinth', 'statue_granite', extras={'openyamm_specular': 0.3})}


def tint_table():
    import json
    exposed = json.load(open(os.path.join(dlib.WORK, f'{PROP}_texture.json')))['exposed_mean']
    g = lambda c: tuple(v * k for v, k in zip(c, GAIN))                         # noqa: E731
    return {'Stone': (g(TARGETS['body']), exposed), 'Wing': (g(TARGETS['wing']), None),
            'Hair': (g(TARGETS['wing']), None), 'Plinth': (g(TARGETS['plinth']), None)}


def main():
    pl.reset()
    mats = materials(STAGE)
    static, j, head_m, chest_m = build_pose()
    co = sl.coords(static)
    lift = PLINTH['lower'][2] + PLINTH['upper'][2] - float(co[:, 2].min())
    feet = co[co[:, 2] < co[:, 2].min() + 0.06]
    centre = Vector((float(feet[:, 0].mean()), float(feet[:, 1].mean()) + 0.05, 0))
    place = Matrix.Translation(Vector((0, 0, lift)) - centre)
    static.data.transform(place)
    head_m = place @ head_m; chest_m = place @ chest_m
    CHEST.append(chest_m)
    head_top = float(max(v.co.z for v in static.data.vertices)) - lift
    sl.single_material(static, mats['Body'])
    BODY[:] = [static]
    count = 1 if STAGE == 'bake' else len([lv for lv in LEVELS if lv[0] != 'far'])
    built = []
    for index in range(count):
        tris, detail = LEVELS[index]
        body = sl.duplicate(static, 'Statue' if index == 0 else f'Statue_LOD{index}')
        sl.decimate(body, tris)
        # the head's own frame: hair built at the rest head top (z of the rest crown)
        groups = {'body': [body], 'hair': [],
                  'wing': wing(1, detail, mats['Wing'], chest_m) + wing(-1, detail, mats['Wing'], chest_m),
                  'plinth': plinth(mats['Plinth'])}
        groups['hair'] = hair(detail, mats['Hair'], head_m, REST_HEAD_TOP)
        built.append(groups)
    bpy.data.objects.remove(static)
    if STAGE == 'bake':
        body0 = built[0]['body'][0]
        sl.smooth(body0, 70)
        sl.stone_bake(body0, os.path.join(dlib.WORK, f'{PROP}_bake.npy'), (1024, 1024), stone='rock_surface',
                      scale=5.0)
        return
    lods = []
    for index, groups in enumerate(built):
        parts = [p for objs in groups.values() for p in objs]
        joined = pl.join('Statue' if index == 0 else f'Statue_LOD{index}', parts)
        sl.smooth(joined, 60)
        pl.vertex_occlusion(joined, rays=(32, 20)[index], distance=0.12, strength=0.55, floor=True)
        sl.tint_groups(joined, tint_table(), keep={'Stone': 0.35})
        lods.append(joined)
    far_mat = dlib.material('StoneFar', 'statue_stone', extras={'openyamm_specular': 0.3})
    for index, entry in enumerate(LEVELS):
        if entry[0] != 'far':
            continue
        _, target, voxel = entry
        # the body alone is remeshed (thin feathers fall apart in a remesh); the plinth stays boxes and the wings
        # come back as their coarse builds
        figure = sl.duplicate(lods[1], f'Figure{index}')
        names = [m.name for m in figure.data.materials]
        drop = {names.index(n) for n in ('Plinth', 'Wing') if n in names}
        bm = bmesh.new(); bm.from_mesh(figure.data)
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index in drop], context='FACES')
        bm.to_mesh(figure.data); bm.free()
        # rev 2: one collapse pass of the textured body (the remesh's vertex colour read flat)
        bpy.ops.object.select_all(action='DESELECT'); figure.select_set(True)
        bpy.context.view_layer.objects.active = figure
        m = figure.modifiers.new('Decimate', 'DECIMATE'); m.ratio = target / pl.triangles(figure)
        m.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier=m.name)
        far = sl.duplicate(figure, f'Statue_LOD{index}')
        bpy.data.objects.remove(figure)
        wings = (wing(1, 3, mats['Wing'], CHEST[0]) + wing(-1, 3, mats['Wing'], CHEST[0]) if index == 2 else
                 [wing_fan(1, mats['Wing'], CHEST[0]), wing_fan(-1, mats['Wing'], CHEST[0])])
        base = pl.join(f'Base{index}', plinth(mats['Plinth']) + wings)
        pl.vertex_occlusion(base, rays=8, distance=0.12, strength=0.55, floor=True)
        sl.tint_groups(base, tint_table())
        lods.append(pl.join(far.name, [far, base]))
    dlib.save(PROP, lods)


CHEST = []
REST_HEAD_TOP = 1.655              # the rest crown (head_m maps the rest frame to the posed head)


if __name__ == '__main__':
    if PREVIEW:
        pl.reset()
        mats = {k: None for k in ('Body', 'Wing', 'Plinth', 'Hair')}
        static, j, head_m, chest_m = build_pose()
        parts = [static] + wing(1, 0, None, chest_m) + wing(-1, 0, None, chest_m) + hair(0, None, head_m,
                                                                                         REST_HEAD_TOP)
        print('POSED', [round(v, 3) for v in pl.bounds(parts)[0]], [round(v, 3) for v in pl.bounds(parts)[1]])
        pl.setup_render((500, 600))
        out = os.path.join(dlib.REVIEW, PROP, 'pose'); os.makedirs(out, exist_ok=True)
        pl.render_views(parts, out, 'pose', views=((-60, 12), (0, 6), (90, 6), (180, 6)))
    else:
        main()
