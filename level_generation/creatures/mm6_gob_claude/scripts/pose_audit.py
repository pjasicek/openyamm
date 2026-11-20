"""Per-frame pose audit for authored clips: limb/sword penetration into the body and joint ranges.

Args: clip[,clip...] [step]. For every sampled frame reports
  pen_L/pen_R  deepest forearm/hand (and distal upper-arm) vertex inside the torso skin (m) and how many verts,
  sword        deepest sword vertex inside the body skin (m),
  wrist_L/R    hand swing relative to the forearm (deg), twist_L/R forearm-to-hand twist (deg),
  elev_L/R     upper-arm elevation above hanging (deg), cross_L/R how far the elbow crosses the body midline (m).
Writes work/pose_audit_<clip>.json. Thresholds: pen > 0.008 m, wrist > 70, |twist| > 100, elev > 105, |humeral (upper-arm roll)| > 60.
"""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector, Quaternion
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

args = sys.argv[sys.argv.index('--') + 1:]
clips = args[0].split(',')
step = int(args[1]) if len(args) > 1 else 1
rig = bpy.data.objects['Peasant_Rig']; mesh = bpy.data.objects['Peasant']
PARTS = json.loads(bpy.context.scene['pfem_parts'])
part_attr = np.zeros(len(mesh.data.polygons), dtype=np.int32)
mesh.data.attributes['part'].data.foreach_get('value', part_attr)

# dominant bone per vertex
names = [g.name for g in mesh.vertex_groups]
dom = np.full(len(mesh.data.vertices), -1)
best = np.zeros(len(mesh.data.vertices))
for v in mesh.data.vertices:
    for g in v.groups:
        if g.weight > best[v.index]:
            best[v.index] = g.weight; dom[v.index] = g.group
dom_name = np.array([names[d] if d >= 0 else '' for d in dom])


def limb_mask(side):
    distal = np.array([(side + 'ForeArm' in n) or (side + 'Hand' in n) for n in dom_name])
    upper = dom_name == f'mixamorig:{side}Arm'
    return distal, upper


TORSO = np.array([any(k in n for k in ('Hips', 'Spine', 'Neck', 'Head', 'UpLeg', 'Shoulder')) for n in dom_name])
sword_poly = part_attr == PARTS.index('Sword')
body_poly = part_attr == PARTS.index('Body')
sword_vert = np.zeros(len(mesh.data.vertices), bool)
for p in mesh.data.polygons:
    if sword_poly[p.index]:
        sword_vert[list(p.vertices)] = True
masks = {s: limb_mask(s) for s in ('Left', 'Right')}


RAYS = [Vector(d).normalized() for d in ((1, 0.1, 0.05), (-1, 0.05, 0.1), (0.1, 1, 0.05), (0.05, -1, 0.1),
                                          (0.1, 0.05, 1), (0.05, 0.1, -1))]


def inside(tree, v):
    """Ray-parity vote; the torso skin has holes at the shoulders/knees, so a majority of 6 rays decides."""
    odd = 0
    for d in RAYS:
        n, origin = 0, v
        while n < 12:
            hit = tree.ray_cast(origin, d, 2.0)
            if hit[0] is None:
                break
            n += 1; origin = hit[0] + d * 1e-4
        odd += n % 2
    return odd >= 4


def penetration(co, tree, verts):
    depth, count = 0.0, 0
    for i in np.nonzero(verts)[0]:
        v = Vector(co[i])
        near = tree.find_nearest(v, 0.10)
        if near[0] is None:
            continue
        if inside(tree, v):
            depth = max(depth, near[3]); count += 1
    return round(depth, 4), count


def joint_metrics(side):
    pb = rig.pose.bones
    fa = pb[f'mixamorig:{side}ForeArm']; hand = pb[f'mixamorig:{side}Hand']; arm = pb[f'mixamorig:{side}Arm']
    rest_rel = fa.bone.matrix_local.to_quaternion().inverted() @ hand.bone.matrix_local.to_quaternion()
    d = rest_rel.inverted() @ (fa.matrix.to_quaternion().inverted() @ hand.matrix.to_quaternion())
    swing, twist = d.to_swing_twist('Y')
    hips = pb['mixamorig:Hips'].matrix.to_3x3(); hips0 = pb['mixamorig:Hips'].bone.matrix_local.to_3x3()
    down = (hips @ hips0.inverted()) @ Vector((0, 0, -1))
    upper = (arm.tail - arm.head).normalized()
    elev = math.degrees(upper.angle(down))
    mid_x = (hips @ hips0.inverted()) @ Vector((1, 0, 0))
    sx = 1 if side == 'Left' else -1
    cross = -sx * (arm.tail - pb['mixamorig:Spine2'].head).dot(mid_x)    # >0 when the elbow is past the midline
    sh = pb[f'mixamorig:{side}Shoulder']
    rel0 = sh.bone.matrix_local.to_quaternion().inverted() @ arm.bone.matrix_local.to_quaternion()
    da = rel0.inverted() @ (sh.matrix.to_quaternion().inverted() @ arm.matrix.to_quaternion())
    joint_metrics.humeral = round(math.degrees(da.to_swing_twist('Y')[1]))
    return round(math.degrees(swing.angle)), round(math.degrees(twist)), round(elev), round(cross, 3)


report = {}
dg = bpy.context.evaluated_depsgraph_get()
for clip in clips:
    act = bpy.data.actions[clip]
    rig.animation_data.action = act
    f0, f1 = (int(round(x)) for x in act.frame_range)
    rows = []
    for f in range(f0, f1 + 1, step):
        bpy.context.scene.frame_set(f)
        ev = mesh.evaluated_get(dg); me = ev.to_mesh()
        co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
        polys = [tuple(p.vertices) for p in me.polygons]
        torso_polys = [polys[i] for i in range(len(polys)) if body_poly[i] and all(TORSO[j] for j in polys[i])]
        tree = BVHTree.FromPolygons([Vector(c) for c in co], torso_polys)
        row = {'frame': f}
        for side in ('Left', 'Right'):
            distal, upper = masks[side]
            shoulder = Vector(rig.pose.bones[f'mixamorig:{side}Arm'].head)
            far_upper = upper & (np.linalg.norm(co - np.array(shoulder), axis=1) > 0.12)
            row['pen_' + side[0]] = penetration(co, tree, distal | far_upper)
            w, t, e, c = joint_metrics(side)
            row.update({'wrist_' + side[0]: w, 'twist_' + side[0]: t, 'elev_' + side[0]: e, 'cross_' + side[0]: c,
                        'humeral_' + side[0]: joint_metrics.humeral})
        row['sword'] = penetration(co, tree, sword_vert) if sword_vert.any() else (0, 0)
        ev.to_mesh_clear()
        flags = []
        for s in 'LR':
            if row['pen_' + s][0] > 0.008 and row['pen_' + s][1] >= 3: flags.append(f'pen_{s}')
            if row['wrist_' + s] > 70: flags.append(f'wrist_{s}')
            if abs(row['twist_' + s]) > 100: flags.append(f'twist_{s}')
            if row['elev_' + s] > 105: flags.append(f'elev_{s}')
            if abs(row['humeral_' + s]) > 60: flags.append(f'humeral_{s}')
        if row['sword'][0] > 0.008: flags.append('sword')
        row['flags'] = flags
        rows.append(row)
        print('AUDIT', clip, json.dumps(row))
    report[clip] = rows
    json.dump(rows, open(os.path.join(common.WORK, f'pose_audit_{clip}.json'), 'w'), indent=1)
bad = {c: sum(1 for r in rows if r['flags']) for c, rows in report.items()}
print('AUDIT_SUMMARY', json.dumps(bad))
