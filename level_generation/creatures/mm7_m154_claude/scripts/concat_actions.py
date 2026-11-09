"""Join retargeted clips end to end into one action (m154: the attack is Mixamo Standing Draw Arrow + Standing Aim Recoil,
both mirrored; the recoil's first frame equals the draw's last, so the join drops it). Every bone's rotation and the
pelvis location are sampled per frame and re-keyed; the parts are removed. Writes scene['concat'] = {name: [frames of
each part]} for later steps (the release is the end of the first part).
Args: -- <in blend> <out blend> <Name>=<A>+<B>[+...] ..."""
import bpy, sys, os, json
a = sys.argv[sys.argv.index('--') + 1:]
src, out, specs = a[0], a[1], a[2:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; sc = bpy.context.scene; names = [b.name for b in rig.data.bones]


def set_act(x):
    rig.animation_data_create(); rig.animation_data.action = x
    if x is not None and len(x.slots):
        rig.animation_data.action_slot = x.slots[0]


info = json.loads(sc.get('concat', '{}'))
for spec in specs:
    name, parts = spec.split('='); parts = parts.split('+')
    poses, lens = [], []
    for k, p in enumerate(parts):
        act = bpy.data.actions[p]; f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
        set_act(act); n0 = len(poses)
        for f in range(f0 + (1 if k else 0), f1 + 1):
            sc.frame_set(f)
            poses.append({n: (rig.pose.bones[n].rotation_quaternion.copy(), rig.pose.bones[n].location.copy()) for n in names})
        lens.append(len(poses) - n0)
    old = bpy.data.actions.get(name)
    if old:
        bpy.data.actions.remove(old)
    act = bpy.data.actions.new(name); act.use_fake_user = True; set_act(act); prev = {}
    for i, pose in enumerate(poses):
        for n, (q, l) in pose.items():
            pb = rig.pose.bones[n]; pb.rotation_mode = 'QUATERNION'
            if n in prev and q.dot(prev[n]) < 0:
                q = -q
            prev[n] = q; pb.rotation_quaternion = q; pb.location = l
            pb.keyframe_insert('rotation_quaternion', frame=i)
            if n == 'B_Pelvis':
                pb.keyframe_insert('location', frame=i)
    act.use_frame_range = True; act.frame_start, act.frame_end = 0, len(poses) - 1
    set_act(None)
    for p in parts:
        if p != name and p in bpy.data.actions:
            bpy.data.actions.remove(bpy.data.actions[p])
    info[name] = lens
    print('CONCAT', name, '=', '+'.join(parts), 'frames', lens, 'total', len(poses))
sc['concat'] = json.dumps(info)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
