"""Clip scan of the rig in work/source.blend (identical clips in the installed and reduced GLBs) at the viewer's 48
frames per second: per-frame world height of Head and Hips (largest single-frame step, against the clip's median
step), the fastest bone point per frame (largest world displacement of any deform bone head or tail, m per frame),
the frames whose fastest step is over three times the clip's median, the still time at the start of every clip (until any bone point has moved 1 cm from frame 0) and the lowest bone point.
Usage: blender -b -P anim_scan.py  -> work/anim_scan.json"""
import bpy, json, os
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'source.blend'))
sc = bpy.context.scene; rig = bpy.data.objects['Rig']
EFFECT = ('Root', 'AshRoot', 'BurstLeft', 'BurstRight')   # effect bones (ash, palm plumes) and the root are left out
bones = [b for b in rig.data.bones if b.use_deform and b.name not in EFFECT and not b.name.startswith('Socket')]
fps = sc.render.fps / sc.render.fps_base
report = {}
for act in sorted(bpy.data.actions, key=lambda a: a.name):
    rig.animation_data.action = act
    f0, f1 = act.frame_range; n = int(round((f1 - f0) / fps * 48)) + 1
    pts, head, hips = [], [], []
    for k in range(n):
        sc.frame_set(int(f0), subframe=0.0) if False else None
        fr = f0 + k * fps / 48; sc.frame_set(int(fr), subframe=fr - int(fr))
        M = rig.matrix_world; pb = rig.pose.bones
        pts.append([tuple(M @ pb[b.name].head) for b in bones] + [tuple(M @ pb[b.name].tail) for b in bones])
        head.append((M @ pb['Head'].head).z); hips.append((M @ pb['Hips'].head).z)
    P = np.array(pts); head = np.array(head); hips = np.array(hips)
    step = np.linalg.norm(np.diff(P, axis=0), axis=2).max(1)
    moved = np.linalg.norm(P - P[0], axis=2).max(1)
    still = int(np.argmax(moved > .01)) if (moved > .01).any() else n
    dh = np.diff(head); dp = np.diff(hips)
    report[act.name] = {
        'frames_48': n, 'still_start_frames': still, 'still_start_s': round(still / 48, 3),
        'head_z_range': [round(float(head.min()), 3), round(float(head.max()), 3)],
        'head_max_step_mm': round(float(np.abs(dh).max()) * 1000, 1), 'head_max_step_frame': int(np.abs(dh).argmax()) + 1,
        'head_median_step_mm': round(float(np.median(np.abs(dh))) * 1000, 2),
        'hips_max_step_mm': round(float(np.abs(dp).max()) * 1000, 1), 'hips_max_step_frame': int(np.abs(dp).argmax()) + 1,
        'fastest_point_mm_per_frame': round(float(step.max()) * 1000, 1), 'fastest_frame': int(step.argmax()) + 1,
        'fastest_bone': bones[int(np.linalg.norm(np.diff(P, axis=0), axis=2)[step.argmax()].argmax()) % len(bones)].name,
        'steps_over_3x_median': [int(i) + 1 for i in np.flatnonzero(step > 3 * max(np.median(step), 1e-3))][:12],
        'median_point_mm_per_frame': round(float(np.median(step)) * 1000, 1),
        'lowest_bone_point_z': round(float(P[..., 2].min()), 3),
        'loop_seam_mm': round(float(np.linalg.norm(P[-1] - P[0], axis=1).max()) * 1000, 1)}
    print('SCAN', act.name, json.dumps(report[act.name]))
open(os.path.join(HERE, 'work', 'anim_scan.json'), 'w').write(json.dumps(report, indent=1))
