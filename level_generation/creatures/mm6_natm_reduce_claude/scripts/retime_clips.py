"""Play clips faster by compressing their key times (user, 2026-10-14: attack 50 % faster, death 2x faster).
Each <Action>:<speed> divides the action's length by speed, rounded to whole frames so the clip ends on a sampled
frame (Death 109 -> 54 frames: the held Dead pose is its true last frame); key handles scale with the keys. An action
retimed once carries the custom property 'retimed' and is skipped (swap_body.py rebuilds rig_v5 from the master, so
run this after it). Prints the new length and the factor to apply to event times. Rewrites <blend> in place.
Args: -- <blend> Attack:1.5 Death:2"""
import bpy, sys, os
a = sys.argv[sys.argv.index('--') + 1:]
blend, specs = a[0], a[1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))


def fcurves(action):
    fcs = list(getattr(action, 'fcurves', []) or [])
    if not fcs and hasattr(action, 'layers'):
        fcs = [fc for layer in action.layers for strip in layer.strips for cb in strip.channelbags for fc in cb.fcurves]
    return fcs


for spec in specs:
    name, speed = spec.split(':'); act = bpy.data.actions[name]
    f0, f1 = act.frame_range
    if act.get('retimed'):
        print('RETIME', name, 'already retimed by', act['retimed'], '- skipped'); continue
    n1 = max(1, round((f1 - f0) / float(speed))); k = (f1 - f0) / n1
    for fc in fcurves(act):
        for kp in fc.keyframe_points:
            for attr in ('co', 'handle_left', 'handle_right'):
                v = getattr(kp, attr); v[0] = f0 + (v[0] - f0) / k
        fc.update()
    act.use_frame_range = True; act.frame_start, act.frame_end = f0, f0 + n1
    act['retimed'] = round(k, 4)
    print('RETIME', name, f'{f1 - f0:g} -> {n1} frames ({(f1 - f0) / 30:.3f} -> {n1 / 30:.3f} s at 30 fps), speed x{k:.4f};'
          f' event times / {k:.4f}')
bpy.ops.wm.save_mainfile()
