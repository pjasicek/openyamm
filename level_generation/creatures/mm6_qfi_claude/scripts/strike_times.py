"""Clip timing probe on work/anim_v1.blend: per source action, both hands' world speed per frame, the hands' spread,
height and the fastest downward-forward hand motion (the blow), so author_clips.py can trim and mark impacts.
Writes work/strike_times.json."""
import bpy, json
import numpy as np
from pathlib import Path
P = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P / 'work' / 'anim_v1.blend'))
rig = bpy.data.objects['Rig']
scene = bpy.context.scene
out = {}
for act in bpy.data.actions:
    if not act.name.endswith('_src'):
        continue
    rig.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = map(int, act.frame_range)
    H = {s: [] for s in 'LR'}
    for f in range(f0, f1 + 1):
        scene.frame_set(f)
        for s in 'LR':
            tip = rig.matrix_world @ rig.pose.bones[f'B_{s}_Finger22'].tail
            H[s].append(tuple(tip))
    rec = {}
    for s in 'LR':
        p = np.array(H[s]); v = np.diff(p, axis=0) * 30.0
        speed = np.linalg.norm(v, axis=1)
        down_fwd = -v[:, 2] - v[:, 1]                 # moving down and forward (-Y)
        k = int(np.argmax(np.where(down_fwd > 0, speed, 0)))
        rec[s] = {'peak_speed': round(float(speed.max()), 2), 'peak_time': round(float(np.argmax(speed) / 30.0), 3),
                  'blow_time': round(float(k / 30.0), 3), 'blow_speed': round(float(speed[k]), 2),
                  'max_height_time': round(float(np.argmax(p[:, 2]) / 30.0), 3)}
    spread = np.linalg.norm(np.array(H['L']) - np.array(H['R']), axis=1)
    rec['max_spread_time'] = round(float(np.argmax(spread) / 30.0), 3)
    rec['seconds'] = (f1 - f0) / 30.0
    out[act.name] = rec
    print('TIMES', act.name, json.dumps(rec))
(P / 'work' / 'strike_times.json').write_text(json.dumps(out, indent=1))
