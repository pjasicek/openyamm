"""Even out a burst of speed in a clip by retiming it, keeping its length (Mage Cast: the set's Unarmed Cast L Buff 1
flicks the staff hand up at 12-16 m/s for two frames between frames at ~2 m/s; user review 2026-10-20: "really
abrupt, should be more evenly distributed to the surrounding frames").
The playback rate through the source, du/df, is min(1, CAP / speed(u)) of BONE's world speed, smoothed over SMOOTH
frames and then scaled by one factor so the clip keeps its frame count (the rest of the clip runs that much faster).
Every animated pose bone is resampled at the new source times (evaluated pose, slerp/lerp between frames by the
evaluator) and keyed on the integer frames. Run before robe_sim.py (the cloth is simulated on the retimed clip).
Args: -- <in blend> <out blend> <Action>:<bone>:<cap m/s> [...]"""
import bpy, sys, os, math
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
src, out, items = a[0], a[1], a[2:]
SMOOTH = float(os.environ.get('RETIME_SMOOTH', '1.5'))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
scene = bpy.context.scene; rig = bpy.data.objects['Rig']; AW = rig.matrix_world


def use(act):
    rig.animation_data_create(); rig.animation_data.action = act
    if len(act.slots):
        rig.animation_data.action_slot = act.slots[0]


def at(u):
    scene.frame_set(int(math.floor(u)), subframe=u - math.floor(u))


for it in items:
    name, bone, cap = it.split(':'); cap = float(cap)
    act = bpy.data.actions[name]; use(act)
    f0, f1 = (int(round(x)) for x in act.frame_range); n = f1 - f0
    P = []
    for f in range(f0, f1 + 1):
        scene.frame_set(f); P.append(np.array(AW @ rig.pose.bones[bone].head))
    sp = np.linalg.norm(np.diff(np.array(P), axis=0), axis=1) * scene.render.fps     # per source interval
    rate = np.minimum(1.0, cap / np.maximum(sp, 1e-6))
    if SMOOTH > 0:
        r = int(math.ceil(3 * SMOOTH)); k = np.exp(-0.5 * (np.arange(-r, r + 1) / SMOOTH) ** 2); k /= k.sum()
        rate = np.minimum(rate, np.convolve(np.pad(rate, r, mode='edge'), k, mode='valid'))
    dur = 1.0 / rate                                   # output frames spent on each source interval
    dur *= n / dur.sum()                               # keep the clip length
    tout = np.concatenate([[0.0], np.cumsum(dur)])     # output time at each source frame
    u_of_f = np.interp(np.arange(n + 1), tout, np.arange(n + 1)) + f0
    # sample every animated bone at the new source times
    bags = [cb for layer in act.layers for strip in layer.strips for cb in strip.channelbags]
    names = sorted({fc.data_path.split('"')[1] for cb in bags for fc in cb.fcurves if fc.data_path.startswith('pose.bones["')})
    samples = []
    for u in u_of_f:
        at(float(u))
        samples.append({b: (rig.pose.bones[b].location.copy(), rig.pose.bones[b].rotation_quaternion.copy(),
                            rig.pose.bones[b].scale.copy()) for b in names})
    for cb in bags:
        for fc in list(cb.fcurves):
            if fc.data_path.startswith('pose.bones["') and fc.data_path.split('"')[1] in names:
                cb.fcurves.remove(fc)
    for i, f in enumerate(range(f0, f1 + 1)):
        for b in names:
            pb = rig.pose.bones[b]; pb.rotation_mode = 'QUATERNION'
            pb.location, pb.rotation_quaternion, pb.scale = samples[i][b]
            pb.keyframe_insert('location', frame=f); pb.keyframe_insert('rotation_quaternion', frame=f); pb.keyframe_insert('scale', frame=f)
    P2 = []
    for f in range(f0, f1 + 1):
        scene.frame_set(f); P2.append(np.array(AW @ rig.pose.bones[bone].head))
    sp2 = np.linalg.norm(np.diff(np.array(P2), axis=0), axis=1) * scene.render.fps
    print('RETIME', name, bone, 'frames', n + 1, 'peak m/s', round(float(sp.max()), 1), '->', round(float(sp2.max()), 1),
          'rest sped up x', round(1.0 / float(np.median(rate * dur)), 3))
rig.animation_data.action = None
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
