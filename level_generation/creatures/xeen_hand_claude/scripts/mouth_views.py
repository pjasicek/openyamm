"""Mouth close-ups at several lid angles (front along n, three-quarter from above). review/lips_<deg>_<view>.png
Args: -- <blend> <deg> [<deg> ...]"""
import bpy, os, sys, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C, handpose as H
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', a[0]))
rig = bpy.data.objects['Hand_Rig']
M = json.load(open(os.path.join(HERE, 'work', 'mouth.json')))
O, n = np.array(M['O']), np.array(M['n'])
for deg in a[1:]:
    H.reset(rig); H.hand(rig, (0, 0, 0), lips=float(deg))
    for vn, d in {'front': n * 3, 'quarter': np.array((1.5, -2.5, 2.0))}.items():
        C.render(tuple(O + d), tuple(O), 0.24, os.path.join(HERE, 'review', f'lips_{deg}_{vn}.png'), res=(420, 320),
                 floor=False)
