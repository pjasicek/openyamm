"""Soft wrist-swing limit (arm gate: wrist swing <= 60 deg). The set's palm-push casts bend the hand back ~100 deg against
the forearm; on our rigid claws that reads as a broken wrist. Per frame and side the hand's local rotation against the
forearm (rest relation removed) is split into swing and twist about the hand axis (armik.split_swing_twist); a swing
above KNEE deg is compressed smoothly toward LIMIT (KNEE + (LIMIT - KNEE) * tanh(excess / (LIMIT - KNEE))), the twist
is kept. Keys the hand quaternions in place. Args: -- <in blend> <out blend> [Action ...]"""
import bpy, sys, os, math
from mathutils import Quaternion, Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import armik
a = sys.argv[sys.argv.index('--') + 1:]
src, out, acts = a[0], a[1], a[2:]
KNEE, LIMIT = float(os.environ.get('KNEE', '42')), float(os.environ.get('LIMIT', '58'))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
scene = bpy.context.scene; rig = bpy.data.objects['Rig']
acts = acts or [x.name for x in bpy.data.actions if x.name in ('Standing', 'Walking', 'Attack', 'Cast', 'Hit', 'Death', 'Fidget')]
for name in acts:
    act = bpy.data.actions[name]; rig.animation_data_create(); rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(round(x)) for x in act.frame_range); worst = {s: [0, 0] for s in os.environ.get('SIDES', 'LR')}
    for f in range(f0, f1 + 1):
        scene.frame_set(f)
        for s in os.environ.get('SIDES', 'LR'):
            hd = f'B_{s}_Hand'; fa = f'B_{s}_Forearm'
            pb = rig.pose.bones[hd]; pb.rotation_mode = 'QUATERNION'
            axis = (rig.data.bones[hd].matrix_local.to_3x3().inverted() @ (rig.data.bones[hd].head_local - rig.data.bones[fa].head_local)).normalized()
            q = pb.rotation_quaternion.copy()                    # = the hand's local rotation against its rest relation
            sw, tw = armik.split_swing_twist(q, axis)
            ang = math.degrees(sw.angle if sw.angle <= math.pi else 2 * math.pi - sw.angle)
            worst[s][0] = max(worst[s][0], ang)
            if ang > KNEE:
                new = KNEE + (LIMIT - KNEE) * math.tanh((ang - KNEE) / (LIMIT - KNEE))
                ax = Vector((sw.x, sw.y, sw.z)).normalized() * (1 if sw.w >= 0 else -1)
                pb.rotation_quaternion = Quaternion(ax, math.radians(new)) @ Quaternion(axis, tw)
                pb.keyframe_insert('rotation_quaternion', frame=f)
                worst[s][1] = max(worst[s][1], new)
            else:
                worst[s][1] = max(worst[s][1], ang)
    print('WRIST', name, {s: [round(v, 1) for v in worst[s]] for s in worst})
rig.animation_data.action = None
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
