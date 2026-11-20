"""Strike moment of source attack clips: time of peak sword-tip speed (tip = grip centre + 0.8 m along the source grip
axis, work/grip_source.json) and of the lowest tip point after the raise. Args: -- <set glb> clip [clip ...]"""
import bpy, sys, os, json
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
g = json.load(open(os.path.join(HERE, 'work', 'grip_source.json')))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a[0])
fps = bpy.context.scene.render.fps
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
acts = {x.name.split('@')[-1].split('|')[-1]: x for x in bpy.data.actions}
for clip in a[1:]:
    act = acts[clip]; arm.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        arm.animation_data.action_slot = act.slots[0]
    f0, f1 = act.frame_range; ts, tips = [], []
    f = f0
    while f <= f1:
        bpy.context.scene.frame_set(int(f), subframe=f - int(f))
        M = arm.matrix_world @ arm.pose.bones['B_R_Hand'].matrix
        c = M @ Vector(g['centre_hand']); ax = (M.to_3x3() @ Vector(g['axis_hand'])).normalized()
        tips.append(np.array(c + ax * 0.8 * 2.58 / 1.7)); ts.append((f - f0) / fps)
        f += 0.25
    tips = np.array(tips); ts = np.array(ts)
    sp = np.linalg.norm(np.diff(tips, axis=0), axis=1) / np.diff(ts)
    k = int(np.argmax(sp))
    print(f'STRIKE {clip:14s} length {ts[-1]:.2f} s, peak tip speed at {ts[k]:.2f} s ({sp[k]:.1f} u/s), '
          f'speed > 50% of peak from {ts[np.argmax(sp > 0.5 * sp[k])]:.2f} s')
