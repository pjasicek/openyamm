"""Location channel stats over all clips (not setup): bone axis mean min max. Args: <rig blend>"""
import bpy, sys
import numpy as np
from collections import defaultdict
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
v = defaultdict(list)
for act in bpy.data.actions:
    if 'setup' in act.name.lower():
        continue
    fcs = list(getattr(act, 'fcurves', []) or [])
    if not fcs and hasattr(act, 'layers'):
        fcs = [fc for l in act.layers for s in l.strips for cb in s.channelbags for fc in cb.fcurves]
    for fc in fcs:
        if fc.data_path.endswith('.location'):
            v[(fc.data_path.split('"')[1], fc.array_index)] += [(act.name, kp.co.y) for kp in fc.keyframe_points]
for (b, a), x in sorted(v.items()):
    y = np.array([t[1] for t in x])
    if np.abs(y).max() > 0.004:
        s = np.array([t[1] for t in x if t[0] in ('stand', 'walk', 'run')])
        print('LOC', b, a, 'all mean %.4f range %.4f..%.4f | stand/walk/run %.4f..%.4f' % (y.mean(), y.min(), y.max(), s.min(), s.max()))
