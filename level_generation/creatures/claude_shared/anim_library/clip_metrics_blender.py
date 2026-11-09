"""Measure animation clips headlessly for the animation library index.

Run: blender -b --factory-startup -P clip_metrics_blender.py -- LIST.txt OUT.jsonl
LIST.txt holds one clip path per line (FBX or GLB). Each clip is imported into an empty scene and sampled; one JSON
line per clip is appended to OUT.jsonl (clips already present in OUT.jsonl are skipped, so a rerun resumes).

Metrics are scale and rig independent (Mixamo `mixamorig:*` and humanoid-set `B_*` skeletons):
  hips/head height as a fraction of the standing reference -> posture per frame
  hips XY travel and yaw change relative to the first frame's facing -> root motion / turning
  first-vs-last local pose difference -> loopability
  hand speed, reach and height -> attack / cast hints
  a hash of the sampled joint positions -> identical-motion duplicates
"""
import bpy, hashlib, json, math, os, sys
from mathutils import Vector

JOINTS = {
    'hips': ('Hips', 'B_Pelvis'),
    'head': ('Head', 'B_Head'),
    'l_hand': ('LeftHand', 'B_L_Hand'),
    'r_hand': ('RightHand', 'B_R_Hand'),
    'l_thigh': ('LeftUpLeg', 'B_L_Thigh'),
    'r_thigh': ('RightUpLeg', 'B_R_Thigh'),
    'l_knee': ('LeftLeg', 'B_L_Calf'),
    'r_knee': ('RightLeg', 'B_R_Calf'),
    'l_foot': ('LeftFoot', 'B_L_Foot'),
    'r_foot': ('RightFoot', 'B_R_Foot'),
}
MAX_SAMPLES = 240


def find_bone(arm, names):
    by_suffix = {b.name.split(':')[-1]: b.name for b in arm.pose.bones}
    for n in names:
        if n in by_suffix:
            return by_suffix[n]
    return None


def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def import_clip(path):
    low = path.lower()
    if low.endswith('.fbx'):
        bpy.ops.import_scene.fbx(filepath=path, use_anim=True)
    else:
        bpy.ops.import_scene.gltf(filepath=path)


def pick_armature():
    arms = [o for o in bpy.context.scene.objects if o.type == 'ARMATURE']
    arms.sort(key=lambda o: -len(o.data.bones))
    return arms[0] if arms else None


def measure(path):
    clear_scene()
    import_clip(path)
    sc = bpy.context.scene
    arm = pick_armature()
    if arm is None:
        return {'error': 'no armature'}
    meshes = [o for o in sc.objects if o.type == 'MESH']
    actions = list(bpy.data.actions)
    act = arm.animation_data.action if arm.animation_data and arm.animation_data.action else None
    if act is None and actions:
        act = max(actions, key=lambda a: a.frame_range[1] - a.frame_range[0])
        arm.animation_data_create()
        arm.animation_data.action = act
    if act is None:
        return {'error': 'no action', 'has_mesh': bool(meshes)}
    bones = {k: find_bone(arm, v) for k, v in JOINTS.items()}
    missing = [k for k, v in bones.items() if v is None]
    if missing:
        return {'error': 'missing joints ' + ','.join(missing), 'bone_count': len(arm.data.bones)}
    f0, f1 = act.frame_range
    f0, f1 = int(round(f0)), int(round(f1))
    fps = sc.render.fps / sc.render.fps_base
    nframes = f1 - f0 + 1
    step = max(1, math.ceil(nframes / MAX_SAMPLES))
    frames = list(range(f0, f1 + 1, step))
    if frames[-1] != f1:
        frames.append(f1)
    mw = arm.matrix_world
    all_bones = [pb.name for pb in arm.pose.bones]
    samples = []
    hash_rows = []
    for f in frames:
        sc.frame_set(f)
        pos = {k: (mw @ arm.pose.bones[b].head).copy() for k, b in bones.items()}
        hips_m = mw @ arm.pose.bones[bones['hips']].matrix
        samples.append((f, pos, hips_m))
        hash_rows.append(','.join('%d' % round(c * 1000) for b in all_bones[:60]
                                  for c in (mw @ arm.pose.bones[b].head)))
    motion_hash = hashlib.sha1(('%d|' % nframes + '\n'.join(hash_rows)).encode()).hexdigest()

    p0 = samples[0][1]
    leg = (p0['l_thigh'] - p0['l_knee']).length + (p0['l_knee'] - p0['l_foot']).length
    leg = max(leg, 1e-4)
    torso = (p0['hips'] - p0['head']).length
    stand_hips = leg * 1.0
    stand_head = leg + torso
    # Facing from the first frame: right = right thigh - left thigh, forward = up x right.
    up = Vector((0, 0, 1))
    right0 = (p0['r_thigh'] - p0['l_thigh'])
    right0.z = 0
    right0 = right0.normalized() if right0.length > 1e-6 else Vector((1, 0, 0))
    fwd0 = up.cross(right0).normalized()

    floor = 0.0
    hip_r, head_r, feet_min, yaw, hips_xy = [], [], [], [], []
    for f, pos, hm in samples:
        hip_r.append((pos['hips'].z - floor) / stand_hips)
        head_r.append((pos['head'].z - floor) / stand_head)
        feet_min.append((min(pos['l_foot'].z, pos['r_foot'].z) - floor) / leg)
        r = pos['r_thigh'] - pos['l_thigh']
        r.z = 0
        if r.length > 1e-6:
            fw = up.cross(r.normalized())
            ang = math.degrees(math.atan2(fw.cross(fwd0).z * -1, fw.dot(fwd0)))
        else:
            ang = yaw[-1] if yaw else 0.0
        yaw.append(ang)
        d = pos['hips'] - p0['hips']
        hips_xy.append((d.dot(fwd0), d.dot(right0)))

    def posture(hr):
        if hr >= 0.86:
            return 'standing'
        if hr >= 0.66:
            return 'crouched'
        if hr >= 0.42:
            return 'low'
        return 'lying'

    post = [posture(h) for h in head_r]
    n = len(samples)
    frac = {k: round(post.count(k) / n, 3) for k in ('standing', 'crouched', 'low', 'lying')}
    # Unwrap yaw.
    uy, prev, off = [], yaw[0], 0.0
    for a in yaw:
        if a - prev > 180:
            off -= 360
        elif a - prev < -180:
            off += 360
        uy.append(a + off)
        prev = a
    net_f, net_r = hips_xy[-1]
    excursion = max(math.hypot(a, b) for a, b in hips_xy)
    path = sum(math.hypot(hips_xy[i][0] - hips_xy[i - 1][0], hips_xy[i][1] - hips_xy[i - 1][1]) for i in range(1, n))

    def local(pos):
        return {k: pos[k] - pos['hips'] for k in pos}

    la, lb = local(samples[0][1]), local(samples[-1][1])
    loop_err = sum((la[k] - lb[k]).length for k in la) / len(la) / leg
    loop_err += abs(samples[0][1]['hips'].z - samples[-1][1]['hips'].z) / leg

    duration = (f1 - f0) / fps if fps else 0
    dt = step / fps if fps else 1
    hand_speed, peak_t = 0.0, 0.0
    reach, above_head = 0.0, -9.0
    for i in range(n):
        pos = samples[i][1]
        for h in ('l_hand', 'r_hand'):
            rel = pos[h] - pos['hips']
            reach = max(reach, rel.dot(fwd0) / leg)
            above_head = max(above_head, (pos[h].z - pos['head'].z) / leg)
            if i:
                prel = samples[i - 1][1][h] - samples[i - 1][1]['hips']
                sp = (rel - prel).length / dt / leg
                if sp > hand_speed:
                    hand_speed, peak_t = sp, (samples[i][0] - f0) / fps
    activity = 0.0
    for i in range(1, n):
        a, b = local(samples[i - 1][1]), local(samples[i][1])
        activity += sum((a[k] - b[k]).length for k in a) / len(a)
    activity = activity / max(duration, 1e-3) / leg
    foot_travel = max(max((s[1][k] - p0[k]).length for s in samples) for k in ('l_foot', 'r_foot')) / leg

    def series(vals, count=24):
        if len(vals) <= count:
            return [round(v, 3) for v in vals]
        return [round(vals[round(i * (len(vals) - 1) / (count - 1))], 3) for i in range(count)]

    return {
        'series': {
            'head_ratio': series(head_r), 'hips_ratio': series(hip_r), 'feet_min': series(feet_min),
            'root_fwd': series([a for a, b in hips_xy]), 'root_right': series([b for a, b in hips_xy]),
            'yaw': series([a - uy[0] for a in uy]),
        },
        'fps': round(fps, 3), 'frames': nframes, 'duration_s': round(duration, 3),
        'bone_count': len(arm.data.bones), 'has_mesh': bool(meshes), 'action': act.name,
        'actions_in_file': len(actions), 'motion_hash': motion_hash,
        'leg_m': round(leg, 3),
        'posture_frac': frac, 'posture_start': post[0], 'posture_end': post[-1],
        'head_ratio': {'min': round(min(head_r), 3), 'median': round(sorted(head_r)[n // 2], 3),
                       'max': round(max(head_r), 3), 'start': round(head_r[0], 3), 'end': round(head_r[-1], 3)},
        'hips_ratio_median': round(sorted(hip_r)[n // 2], 3),
        'feet_min_ratio': round(min(feet_min), 3),
        'feet_min_q': [round(sorted(feet_min)[int(q * (n - 1))], 3) for q in (0.1, 0.5, 0.9)],
        'root_net_fwd': round(net_f / leg, 3), 'root_net_right': round(net_r / leg, 3),
        'root_excursion': round(excursion / leg, 3), 'root_path': round(path / leg, 3),
        'yaw_net_deg': round(uy[-1] - uy[0], 1), 'yaw_max_abs_deg': round(max(abs(a - uy[0]) for a in uy), 1),
        'loop_err': round(loop_err, 3),
        'hand_speed_max': round(hand_speed, 2), 'hand_peak_t': round(peak_t, 3),
        'hand_reach_fwd': round(reach, 3), 'hand_above_head': round(above_head, 3),
        'activity': round(activity, 3), 'foot_travel': round(foot_travel, 3),
    }


def main():
    argv = sys.argv[sys.argv.index('--') + 1:]
    list_path, out_path = argv[0], argv[1]
    done = set()
    if os.path.exists(out_path):
        for line in open(out_path):
            try:
                done.add(json.loads(line)['path'])
            except Exception:
                pass
    paths = [p.strip() for p in open(list_path) if p.strip()]
    with open(out_path, 'a') as out:
        for p in paths:
            if p in done:
                continue
            try:
                rec = measure(p)
            except Exception as e:
                rec = {'error': repr(e)[:300]}
            rec['path'] = p
            rec['size'] = os.path.getsize(p)
            out.write(json.dumps(rec) + '\n')
            out.flush()


main()
