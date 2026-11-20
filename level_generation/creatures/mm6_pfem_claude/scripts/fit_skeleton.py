"""Step 2a: fit the MPFB Mixamo skeleton (with fingers) inside the step-1 Meshy mesh by articulated ICP.

The MPFB proxy body (work/body_v3.blend) is posed bone-chain by bone-chain: each chain is rotated (and where
noted uniformly scaled) about its joint so the proxy surface of that chain matches the Meshy surface
(Umeyama with a fixed pivot, outlier pairs rejected). The pose is then applied as the new rest pose.
Output: work/fit_v1.blend = step-1 parts + Peasant_Rig (fitted) + Proxy (fitted MPFB body, weight/collider source).
"""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'step1_v1.blend'))
with bpy.data.libraries.load(os.path.join(common.WORK, 'body_v3.blend')) as (src, dst):
    dst.objects = ['Human', 'Human.rig']
proxy, rig = dst.objects
for o in (proxy, rig):
    bpy.context.scene.collection.objects.link(o)
proxy.name = 'Proxy'; rig.name = 'Peasant_Rig'; rig.data.name = 'Peasant_Rig'
rig.location = (0, 0, 0)
for m in list(proxy.modifiers):
    if m.type == 'MASK':
        proxy.modifiers.remove(m)
proxy.hide_render = True
groups = {g.index: g.name for g in proxy.vertex_groups}
dominant = []
for v in proxy.data.vertices:
    best, w = '', 0.0
    for g in v.groups:
        n = groups[g.group]
        if n.startswith('mixamorig:') and g.weight > w:
            best, w = n[10:], g.weight
    helper = any(groups[g.group] in ('HelperGeometry', 'JointCubes') and g.weight > 0 for g in v.groups)
    dominant.append('' if helper else best)
dominant = np.array(dominant)


def tree(objs):
    verts, polys = [], []
    for o in objs:
        base = len(verts)
        verts += [o.matrix_world @ v.co for v in o.data.vertices]
        polys += [tuple(base + i for i in p.vertices) for p in o.data.polygons]
    return BVHTree.FromPolygons(verts, polys)


body_tree = tree([bpy.data.objects['Body']])
leg_tree = tree([bpy.data.objects['LegLeft'], bpy.data.objects['LegRight']])
PB = rig.pose.bones
for b in PB:
    b.rotation_mode = 'QUATERNION'


def proxy_points(names):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = proxy.evaluated_get(dg); me = ev.to_mesh()
    co = np.array([tuple(proxy.matrix_world @ v.co) for v in me.vertices])
    ev.to_mesh_clear()
    mask = np.isin(dominant, list(names))
    return co[mask]


def transform_bone(name, M):
    bone = PB['mixamorig:' + name]
    bone.matrix = rig.matrix_world.inverted() @ M @ rig.matrix_world @ bone.matrix
    bpy.context.view_layer.update()


def head(name):
    return rig.matrix_world @ PB['mixamorig:' + name].head


def fit(name, names, target, scale=False, iters=8, reject=(0.03, 0.012), sub=None):
    """Rotate (and optionally scale) bone `name` about its head so proxy points of `names` match `target`."""
    for it in range(iters):
        p = np.array(head(name))
        A = proxy_points(names)
        if sub is not None:
            A = A[sub(A)]
        if len(A) < 10:
            return
        thr = reject[0] + (reject[1] - reject[0]) * it / max(1, iters - 1)
        B = []
        keep = []
        for i, a in enumerate(A):
            hit = target.find_nearest(Vector(a))
            if hit[0] is not None and hit[3] < thr:
                B.append(tuple(hit[0])); keep.append(i)
        if len(B) < 10:
            return
        a = A[keep] - p; b = np.array(B) - p
        U, S, Vt = np.linalg.svd(b.T @ a)
        D = np.diag([1, 1, np.sign(np.linalg.det(U @ Vt))])
        R = U @ D @ Vt
        s = float(np.trace(np.diag(S) @ D) / (a * a).sum()) if scale else 1.0
        s = min(max(s, 0.85), 1.18)
        M = Matrix.Translation(Vector(p)) @ (Matrix(R.tolist()).to_4x4() * 1.0) @ Matrix.Scale(s, 4) @ Matrix.Translation(-Vector(p))
        M[3][3] = 1.0
        transform_bone(name, M)


def subtree(prefix_names):
    return set(prefix_names)


FINGERS = ['Thumb', 'Index', 'Middle', 'Ring', 'Pinky']
report = {}
# 1. global height/position: proxy skin top to Meshy skin top, torso centred.
body_co = np.array([tuple(v.co) for v in bpy.data.objects['Body'].data.vertices])
prox_co = proxy_points(set(dominant) - {''})
s = (body_co[:, 2].max()) / prox_co[:, 2].max()
chest_m = body_co[(np.abs(body_co[:, 2] - 1.15) < 0.01) & (np.abs(body_co[:, 0]) < 0.1)]
chest_p = prox_co[(np.abs(prox_co[:, 2] - 1.15 / s) < 0.01) & (np.abs(prox_co[:, 0]) < 0.1)]
dy = (chest_m[:, 1].min() + chest_m[:, 1].max()) / 2 - s * (chest_p[:, 1].min() + chest_p[:, 1].max()) / 2
transform_bone('Hips', Matrix.Translation((0, dy, 0)) @ Matrix.Scale(s, 4))
report['global_scale'] = s
# 2. head and neck
fit('Neck', {'Neck', 'Head'}, body_tree, scale=False, iters=5)
fit('Head', {'Head'}, body_tree, scale=True, iters=6, sub=lambda A: A[:, 2] > 1.36)
# 3. arms, hands, fingers: landmark-driven lengths (fingertips), ICP only for rotations.
body_obj = bpy.data.objects['Body']
body_pts = np.array([tuple(body_obj.matrix_world @ v.co) for v in body_obj.data.vertices])


def tail(name):
    return rig.matrix_world @ PB['mixamorig:' + name].tail


def aim_scale(name, src_tip, dst_tip, scale=True):
    """Rotate bone subtree about its head so src_tip points at dst_tip, scaling to match the distance."""
    p = head(name)
    a = (src_tip - p); b = (dst_tip - p)
    q = a.normalized().rotation_difference(b.normalized())
    s_ = b.length / a.length if scale else 1.0
    M = Matrix.Translation(p) @ q.to_matrix().to_4x4() @ Matrix.Scale(s_, 4) @ Matrix.Translation(-p)
    transform_bone(name, M)
    return s_


def far_point(points, origin, direction):
    proj = (points - np.array(origin)) @ np.array(direction)
    return Vector(points[int(np.argmax(proj))])


def seg_dist(P, a, b):
    a = np.array(a); b = np.array(b); ab = b - a
    t = np.clip(((P - a) @ ab) / max(ab @ ab, 1e-12), 0, 1)
    return np.linalg.norm(P - (a + t[:, None] * ab), axis=1)


for side, sx in (('Left', 1), ('Right', -1)):
    side_pts = body_pts[body_pts[:, 0] * sx > 0.15]
    shoulder = head(side + 'Arm')
    tip_t = tail(side + 'HandMiddle3')
    tip_m = far_point(side_pts, shoulder, (tip_t - shoulder).normalized())
    report[side + '_arm_scale'] = aim_scale(side + 'Arm', tip_t, tip_m)
    arm_set = {side + 'Arm', side + 'ForeArm'}
    fit(side + 'Arm', {side + 'ForeArm'}, body_tree, iters=6)
    fit(side + 'ForeArm', {side + 'ForeArm'}, body_tree, iters=6)
    wrist = head(side + 'Hand')
    tip_t = tail(side + 'HandMiddle3')
    tip_m = far_point(side_pts, wrist, (tip_t - wrist).normalized())
    report[side + '_hand_scale'] = aim_scale(side + 'Hand', tip_t, tip_m)
    fit(side + 'Hand', {side + 'Hand'}, body_tree, iters=6, reject=(0.015, 0.006))   # palm roll
    # Meshy hand points beyond the wrist, assigned to the nearest template finger chain.
    wrist = np.array(head(side + 'Hand'))
    hand_dir = np.array((tail(side + 'HandMiddle3') - head(side + 'Hand')).normalized())
    hp = side_pts[((side_pts - wrist) @ hand_dir) > 0.02]
    chains = {f: [(head(f'{side}Hand{f}{k}'), tail(f'{side}Hand{f}{k}')) for k in (1, 2, 3)] for f in FINGERS}
    dist = np.stack([np.min([seg_dist(hp, a, b) for a, b in chains[f]], axis=0) for f in FINGERS], 1)
    owner = np.argmin(dist, 1)
    for fi, f in enumerate(FINGERS):
        pts = hp[(owner == fi) & (dist[:, fi] < 0.02)]
        if len(pts) < 5:
            continue
        root = head(f'{side}Hand{f}1'); t_tip = tail(f'{side}Hand{f}3')
        m_tip = far_point(pts, root, (t_tip - root).normalized())
        m_tip = m_tip - (m_tip - root).normalized() * 0.004   # bone tip sits inside the fingertip
        report[f'{side}_{f}_scale'] = round(aim_scale(f'{side}Hand{f}1', t_tip, m_tip), 3)

# 4. legs (shins and shoes only exist below the skirt)
for side in ('Left', 'Right'):
    fit(side + 'UpLeg', {side + 'Leg', side + 'Foot', side + 'ToeBase'}, leg_tree, scale=True, iters=8,
        sub=lambda A: A[:, 2] < 0.5)
    fit(side + 'Leg', {side + 'Leg', side + 'Foot', side + 'ToeBase'}, leg_tree, scale=False, iters=6,
        sub=lambda A: A[:, 2] < 0.5)
    fit(side + 'Foot', {side + 'Foot', side + 'ToeBase'}, leg_tree, scale=False, iters=6)

# Residual: mean distance of proxy skin to Meshy body for key regions.
def residual(names, target):
    A = proxy_points(names)
    d = [target.find_nearest(Vector(a))[3] for a in A]
    return round(float(np.median(d)) * 1000, 1)


for side in ('Left',):
    report['residual_mm'] = {
        'hand': residual({side + 'Hand'}, body_tree),
        'fingers': residual({f'{side}Hand{f}{k}' for f in FINGERS for k in (1, 2, 3)}, body_tree),
        'fingertip_gap_mm': None,
        'forearm': residual({side + 'ForeArm'}, body_tree),
        'head': residual({'Head'}, body_tree),
        'shin': residual({side + 'Leg'}, leg_tree)}

# 5. apply: proxy mesh takes the pose, pose becomes rest.
bpy.context.view_layer.objects.active = proxy
for o in bpy.data.objects:
    o.select_set(o == proxy)
arm_mod = next(m for m in proxy.modifiers if m.type == 'ARMATURE')
bpy.ops.object.modifier_apply(modifier=arm_mod.name)
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects:
    o.select_set(o == rig)
bpy.ops.object.mode_set(mode='POSE'); bpy.ops.pose.select_all(action='SELECT')
bpy.ops.pose.armature_apply(selected=False); bpy.ops.object.mode_set(mode='OBJECT')
m = proxy.modifiers.new('Armature', 'ARMATURE'); m.object = rig
proxy.parent = rig; proxy.matrix_parent_inverse = rig.matrix_world.inverted()
print('FIT', json.dumps(report))
json.dump(report, open(os.path.join(common.WORK, 'fit_report.json'), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'fit_v1.blend'))
