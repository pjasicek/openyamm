"""Clip timing for the engine's action events (playbook "Clip timing"): work/rig_v6.blend -> work/rig_v6t.blend.
- Attack spine twist limit: the source slash turns the chest up to ~90 deg about the spine against the pelvis (110 deg
  shoulder line vs hip line with the clavicles) in the follow-through, about twice a real trunk's axial rotation; the
  neck turns back ~50 deg to keep the head forward. Per frame, the summed twist of B_Spine..B_Spine2 about their
  segment axes is softly limited to TWIST_MAX (unchanged below TWIST_FREE, each bone keeps its share and its swing);
  the removed turn goes to the neck so the head keeps its world direction.
- Attack: a ready pause of LEAD seconds (ease from the Standing pose into the attack's first pose, with a slight
  coil: the chest turned 6 deg toward the sword side) before the source attack at its own
  speed. The blow (peak sword-tip speed of the built clip) then lands near 0.6 s, so the engine's fit of [0, impact]
  to the native 0.75 s action stretches it only ~1.2x. Prints IMPACT for actors.yml `events: attack_melee`.
- Fidget: kept as built (the set's Armed boost 1, 1.0 s at source speed): since 2026-10-10 the engine plays a longer
  fidget to its end while the actor stands. (An interim 0.6 s head shake replaced it while fidgets were cut at the
  native 0.625 s.)
"""
import bpy, sys, os, math, json
import numpy as np
from mathutils import Quaternion, Vector, Matrix
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FPS = 30
LEAD = 0.4
TWIST_FREE, TWIST_MAX = math.radians(25), math.radians(45)
SPINE = ('B_Spine', 'B_Spine1', 'B_Spine2')
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v6.blend'))
scene = bpy.context.scene; scene.render.fps = FPS; scene.render.fps_base = 1
rig = bpy.data.objects['Rig']
names = [b.name for b in rig.data.bones]


def set_act(a):
    rig.animation_data_create(); rig.animation_data.action = a
    if a is not None and getattr(a, 'slots', None) is not None and len(a.slots):
        rig.animation_data.action_slot = a.slots[0]


def sample(act, f):
    set_act(act); scene.frame_set(int(f), subframe=f - int(f))
    return {n: (rig.pose.bones[n].rotation_quaternion.copy(), rig.pose.bones[n].location.copy()) for n in names}


def segment_axis(j, child):
    b, c = rig.data.bones[j], rig.data.bones[child]
    return (b.matrix_local.to_3x3().inverted() @ (c.head_local - b.head_local)).normalized()


TWIST_AXES = {'B_Spine': segment_axis('B_Spine', 'B_Spine1'), 'B_Spine1': segment_axis('B_Spine1', 'B_Spine2'),
              'B_Spine2': segment_axis('B_Spine2', 'B_Neck'), 'B_Neck': segment_axis('B_Neck', 'B_Head')}


def split_twist(q, axis):
    """q = swing @ twist about the bone-local axis; returns (swing, twist angle)."""
    t = 2 * math.atan2(Vector((q.x, q.y, q.z)).dot(axis), q.w)
    t = (t + math.pi) % (2 * math.pi) - math.pi
    return q @ Quaternion(axis, t).inverted(), t


def limit_spine_twist(pose):
    parts = {j: split_twist(pose[j][0], TWIST_AXES[j]) for j in TWIST_AXES}
    total = sum(parts[j][1] for j in SPINE)
    if abs(total) <= TWIST_FREE:
        return pose, total, total
    span = TWIST_MAX - TWIST_FREE
    limited = math.copysign(TWIST_FREE + span * math.tanh((abs(total) - TWIST_FREE) / span), total)
    k = limited / total
    for j in SPINE:
        swing, t = parts[j]; pose[j] = (swing @ Quaternion(TWIST_AXES[j], t * k), pose[j][1])
    swing, t = parts['B_Neck']; pose['B_Neck'] = (swing @ Quaternion(TWIST_AXES['B_Neck'], t + total - limited),
                                                  pose['B_Neck'][1])
    return pose, total, limited


def smooth(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def write(name, frames):
    old = bpy.data.actions.get(name)
    if old:
        bpy.data.actions.remove(old)
    act = bpy.data.actions.new(name); act.use_fake_user = True; set_act(act)
    prev = {}
    for i, pose in enumerate(frames):
        for n, (q, l) in pose.items():
            pb = rig.pose.bones[n]; pb.rotation_mode = 'QUATERNION'
            if n in prev and q.dot(prev[n]) < 0:
                q = -q
            prev[n] = q
            pb.rotation_quaternion = q; pb.location = l
            pb.keyframe_insert('rotation_quaternion', frame=i)
            if n == 'B_Pelvis':
                pb.keyframe_insert('location', frame=i)
    act.use_frame_range = True; act.frame_start, act.frame_end = 0, len(frames) - 1
    set_act(None)
    return act


# ---------------------------------------------------------------- attack with a ready pause
atk = bpy.data.actions['Attack']; st = bpy.data.actions['Standing']
n_atk = int(atk.frame_range[1]); n_lead = int(round(LEAD * FPS))
s0, a0 = sample(st, 0), limit_spine_twist(sample(atk, 0))[0]
frames = []
for i in range(n_lead):
    u = smooth(i / n_lead); coil = math.sin(math.pi * u) * 0.8 + u * 0.2            # coil peaks then holds a little
    pose = {}
    for n in names:
        q = s0[n][0].slerp(a0[n][0], u); l = s0[n][1].lerp(a0[n][1], u)
        if n == 'B_Spine2':
            q = q @ Quaternion((0, 1, 0), math.radians(-6) * coil)
        pose[n] = (q, l)
    frames.append(pose)
worst = (0.0, 0.0)
for f in range(n_atk + 1):
    pose, total, limited = limit_spine_twist(sample(atk, f))
    frames.append(pose)
    if abs(total) > abs(worst[0]):
        worst = (total, limited)
print(f'ATTACK spine twist peak {math.degrees(worst[0]):.0f} deg -> {math.degrees(worst[1]):.0f} deg')
new_atk = write('Attack', frames)
# blow = peak tip speed of the Sword bone tip in the new clip
set_act(new_atk)
G = json.load(open(os.path.join(HERE, 'work', 'grip_pose.json')))
tips = []
for f in range(len(frames)):
    scene.frame_set(f)
    M = rig.matrix_world @ rig.pose.bones['B_R_Hand'].matrix          # the Sword bone is added at export
    c = M @ Vector(G['handle_centre_hand_local']); ax = (M.to_3x3() @ Vector(G['handle_axis_hand_local'])).normalized()
    tips.append(np.array(c + ax * 0.8))
sp = np.linalg.norm(np.diff(np.array(tips), axis=0), axis=1)
k = int(np.argmax(sp)); impact = (k + 0.5) / FPS
set_act(None)
print(f'ATTACK {len(frames) / FPS:.3f} s (lead {n_lead / FPS:.3f} s), blow at {impact:.3f} s -> wind-up stretch '
      f'{0.75 / impact:.2f}x; IMPACT {impact:.3f}')

json.dump({'attack_impact_s': round(impact, 3)}, open(os.path.join(HERE, 'work', 'clip_timing.json'), 'w'))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v6t.blend'))
