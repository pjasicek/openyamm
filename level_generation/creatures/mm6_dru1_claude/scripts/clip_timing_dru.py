"""Clip timing for the druidess (playbook "Clip timing"): <in blend> -> <out blend>.
The Unarmed-set clips (Attack = cast R buff 2, Cast = cast dual attack 2, Hit = get-hit F1) start and end in the set's
boxing guard (fists raised at the chest). Their stance is already planted (retarget.py PLANT_FROM); here the whole
upper body is blended from the Standing pose into the source motion over BLEND_IN and back to Standing over
BLEND_OUT, so the guard never shows (pose = slerp(Standing frame 0, source, u)).
An optional ready hold of Standing (LEAD seconds) moves the release toward the native action length.
Release times (forward = -Y, she faces -Y): Attack = peak FORWARD speed of the right hand after it reached its
highest point (the fling down-forward from overhead; the plain speed peak was the source's one-frame flick UP to
overhead), Cast = peak forward speed of the midpoint of the two hands (the palms clap forward). Printed for actors.yml `events` and written to work/clip_timing.json.
Args: -- <in blend> <out blend>"""
import bpy, sys, os, math, json
import numpy as np
from mathutils import Quaternion
SRC_BLEND, OUT_BLEND = sys.argv[sys.argv.index('--') + 1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FPS = 30
CLIPS = {   # name: (lead hold s, blend in s, blend out s)
    'Attack': (float(os.environ.get('ATTACK_LEAD', '0.0')), 0.30, 0.30),
    'Cast': (float(os.environ.get('CAST_LEAD', '0.25')), 0.30, 0.30),   # push at 0.45 s in the source
    'Hit': (0.0, 0.08, 0.15),
}
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(SRC_BLEND))
scene = bpy.context.scene; scene.render.fps = FPS; scene.render.fps_base = 1
rig = bpy.data.objects['Rig']
names = [b.name for b in rig.data.bones if not b.name.startswith('Cloak_')]


def set_act(a):
    rig.animation_data_create(); rig.animation_data.action = a
    if a is not None and getattr(a, 'slots', None) is not None and len(a.slots):
        rig.animation_data.action_slot = a.slots[0]


def sample(act, f):
    set_act(act); scene.frame_set(int(f), subframe=f - int(f))
    return {n: (rig.pose.bones[n].rotation_quaternion.copy(), rig.pose.bones[n].location.copy()) for n in names}


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


def release(act, n_frames, mode):
    set_act(act); pts = []
    for f in range(n_frames):
        scene.frame_set(f)
        r = np.array(rig.matrix_world @ rig.pose.bones['B_R_Hand'].head)
        l = np.array(rig.matrix_world @ rig.pose.bones['B_L_Hand'].head)
        pts.append(r if mode == 'R' else (r + l) / 2)
    set_act(None)
    P = np.array(pts); fwd = -np.diff(P[:, 1]) * FPS
    start = int(np.argmax(P[:, 2])) if mode == 'R' else 0
    k = start + int(np.argmax(fwd[start:]))
    return (k + 0.5) / FPS, fwd[k]


st = bpy.data.actions['Standing']
s0 = sample(st, 0)
out = {}
for name, (lead, b_in, b_out) in CLIPS.items():
    act = bpy.data.actions[name]; n = int(act.frame_range[1])
    frames = [dict(s0) for _ in range(int(round(lead * FPS)))]
    for f in range(n + 1):
        t = f / FPS; T = n / FPS
        u = smooth(t / b_in) * smooth((T - t) / b_out)
        src = sample(act, f)
        frames.append({k: (s0[k][0].slerp(src[k][0], u), s0[k][1].lerp(src[k][1], u)) for k in names})
    new = write(name, frames)
    if name in ('Attack', 'Cast'):
        imp, v = release(new, len(frames), 'R' if name == 'Attack' else 'mid')
        out[name.lower() + '_impact_s'] = round(imp, 3)
        print(f'{name.upper()} {len(frames) / FPS:.3f} s (hold {lead:.2f} s), release at {imp:.3f} s (forward speed '
              f'{v:.2f} m/s); native action 0.75 s -> wind-up fit {0.75 / imp:.2f}x')
    else:
        print(f'{name.upper()} {len(frames) / FPS:.3f} s')
json.dump(out, open(os.path.join(HERE, 'work', 'clip_timing.json'), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(OUT_BLEND))
