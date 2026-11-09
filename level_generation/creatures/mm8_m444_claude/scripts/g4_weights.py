"""G4 / H5: weight quality on the arms at the clip's own extremes, before any polish.
For each listed (action, frame) - typically the ROM extremes from work/rom.json - per side:
- stretch: posed/rest length of arm-region edges (verts with upper-arm+forearm+hand weight > 0.3); 99th percentile
  and max, with the dominant bone at the worst edge;
- forearm twist profile: the forearm (rest) is cut into 6 rings between elbow and wrist; each ring's rotation about
  the posed forearm axis relative to its rest orientation (carried by the forearm bone) is measured from the ring's
  vertices; reported as degrees at 0/20/40/60/80/100 % plus the hand's own twist - a healthy forearm ramps up, a
  candy-wrapper keeps 0 and jumps at the wrist;
- elbow volume: cross-section area of the ring through the elbow, posed / rest;
- upper arm twist near the shoulder (ring at 20 % of the upper arm) vs the bone's twist.
Writes work/g4_<tag>.json. Args: -- <blend> <tag> action:frame [action:frame ...]"""
import bpy, bmesh, sys, os, json, math
import numpy as np
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index('--') + 1:]
blend, tag, picks = a[0], a[1], a[2:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
nv = len(me.vertices)
rest = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices])
W = {}
for g in body.vertex_groups:
    w = np.zeros(nv)
    for v in me.vertices:
        for e in v.groups:
            if e.group == g.index:
                w[v.index] = e.weight
    W[g.name] = w
edges = np.array([tuple(e.vertices) for e in me.edges])
rest_len = np.linalg.norm(rest[edges[:, 0]] - rest[edges[:, 1]], axis=1)
J = lambda n: np.array(rig.matrix_world @ rig.pose.bones[n].head)


def posed():
    deps = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(deps); m = ev.to_mesh()
    c = np.empty(len(m.vertices) * 3); m.vertices.foreach_get('co', c); ev.to_mesh_clear()
    return (np.array(body.matrix_world) @ np.c_[c.reshape(-1, 3), np.ones(nv)].T).T[:, :3]


def ring_ids(p0, p1, t, tol, side_mask):
    ax = (p1 - p0) / np.linalg.norm(p1 - p0)
    s = (rest - p0) @ ax / np.linalg.norm(p1 - p0)
    rad = np.linalg.norm((rest - p0) - np.outer((rest - p0) @ ax, ax), axis=1)
    return np.where(side_mask & (np.abs(s - t) < tol) & (rad < 0.07))[0]


def ring_angle(ids, rest_axis, pose_axis, rest_ref, pose_ref, P):
    """signed rotation of a vertex ring about the limb axis, posed vs rest, after removing the limb swing"""
    sw = Vector(rest_axis).rotation_difference(Vector(pose_axis)).to_matrix()
    a = []
    rc = rest[ids].mean(0); pc = P[ids].mean(0)
    for i in ids:
        r = np.array(sw @ Vector(rest[i] - rc)); p = P[i] - pc
        r -= pose_axis * (r @ pose_axis); p -= pose_axis * (p @ pose_axis)
        if np.linalg.norm(r) < 1e-4 or np.linalg.norm(p) < 1e-4:
            continue
        a.append(math.atan2(np.cross(r, p) @ pose_axis, r @ p))
    return math.degrees(np.angle(np.mean(np.exp(1j * np.array(a))))) if a else float('nan')


report = {}
for pk in picks:
    act_name, fr = pk.rsplit(':', 1)
    act = bpy.data.actions[act_name]; rig.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    bpy.context.scene.frame_set(int(fr))
    P = posed()
    entry = {}
    for s in ('R', 'L'):
        sh0, el0, wr0 = (np.array(rig.data.bones[f'B_{s}_{n}'].head_local) for n in ('UpperArm', 'Forearm', 'Hand'))
        sh1, el1, wr1 = J(f'B_{s}_UpperArm'), J(f'B_{s}_Forearm'), J(f'B_{s}_Hand')
        side = np.sign(rest[:, 0]) == (1 if s == 'L' else -1)
        armw = W[f'B_{s}_UpperArm'] + W[f'B_{s}_Forearm'] + W[f'B_{s}_Hand']
        m = (armw[edges[:, 0]] > 0.3) & (armw[edges[:, 1]] > 0.3)
        st = np.linalg.norm(P[edges[m, 0]] - P[edges[m, 1]], axis=1) / np.maximum(rest_len[m], 1e-6)
        worst = edges[m][np.argmax(st)]
        dom = max((f'B_{s}_{n}' for n in ('Clavicle', 'UpperArm', 'Forearm', 'Hand')), key=lambda n: W[n][worst[0]])
        fa_r = (wr0 - el0) / np.linalg.norm(wr0 - el0); fa_p = (wr1 - el1) / np.linalg.norm(wr1 - el1)
        prof = []
        for t in (0.05, 0.2, 0.4, 0.6, 0.8, 0.95):
            ids = ring_ids(el0, wr0, t, 0.04, side)
            prof.append(round(ring_angle(ids, fa_r, fa_p, None, None, P), 1) if len(ids) > 5 else None)
        # the hand's twist about the forearm axis relative to the forearm (from the bones)
        Rf = (rig.matrix_world @ rig.pose.bones[f'B_{s}_Forearm'].matrix).to_3x3() @ rig.data.bones[f'B_{s}_Forearm'].matrix_local.to_3x3().inverted()
        Rh = (rig.matrix_world @ rig.pose.bones[f'B_{s}_Hand'].matrix).to_3x3() @ rig.data.bones[f'B_{s}_Hand'].matrix_local.to_3x3().inverted()
        rel = (Rf.inverted() @ Rh).to_quaternion()
        v = Vector((rel.x, rel.y, rel.z)); axr = Vector(fa_r)
        hand_tw = math.degrees(2 * math.atan2(v.dot(axr), rel.w)); hand_tw = (hand_tw + 180) % 360 - 180
        ids = ring_ids(sh0, el0, 1.0, 0.03, side)
        def area(pts, axis):
            c = pts.mean(0); u = np.linalg.svd(pts - c)[2]
            xy = np.c_[(pts - c) @ u[0], (pts - c) @ u[1]]
            ang = np.argsort(np.arctan2(xy[:, 1], xy[:, 0])); xy = xy[ang]
            return 0.5 * abs(np.dot(xy[:, 0], np.roll(xy[:, 1], 1)) - np.dot(xy[:, 1], np.roll(xy[:, 0], 1)))
        el_area = area(P[ids], fa_p) / max(area(rest[ids], fa_r), 1e-9) if len(ids) > 6 else None
        ua_r = (el0 - sh0) / np.linalg.norm(el0 - sh0); ua_p = (el1 - sh1) / np.linalg.norm(el1 - sh1)
        ids = ring_ids(sh0, el0, 0.3, 0.06, side)
        ua_tw = ring_angle(ids, ua_r, ua_p, None, None, P) if len(ids) > 5 else None
        flex = math.degrees(math.acos(np.clip(ua_p @ fa_p, -1, 1)))
        entry[s] = {'stretch_p99': round(float(np.percentile(st, 99)), 2), 'stretch_max': round(float(st.max()), 2),
                    'stretch_bone': dom, 'edge': [int(x) for x in worst], 'piece': int(me.attributes['piece'].data[int(worst[0])].value), 'forearm_twist_profile': prof, 'hand_twist_vs_forearm': round(hand_tw, 1),
                    'elbow_flex_deg': round(flex, 1), 'elbow_area_ratio': None if el_area is None else round(float(el_area), 2),
                    'upper_arm_ring_twist_30pct': None if ua_tw is None else round(ua_tw, 1)}
    report[pk] = entry
    for s in ('R', 'L'):
        e = entry[s]
        print(f"G4 {pk:12s} {s}: stretch p99 {e['stretch_p99']} max {e['stretch_max']} ({e['stretch_bone']}) | hand twist "
              f"{e['hand_twist_vs_forearm']} | forearm rings {e['forearm_twist_profile']} | elbow flex {e['elbow_flex_deg']} "
              f"area {e['elbow_area_ratio']} | upper-arm ring twist {e['upper_arm_ring_twist_30pct']}")
json.dump(report, open(os.path.join(HERE, 'work', f'g4_{tag}.json'), 'w'), indent=1)
