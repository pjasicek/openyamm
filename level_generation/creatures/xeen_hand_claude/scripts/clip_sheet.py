"""Clay contact sheet of every clip of work/anim_v1.blend: N frames per clip from the party's three-quarter-front
view (rows = clips). Usage: clip_sheet.py [frames per clip] [view: quarter|side|front]; writes review/clips_<view>.png"""
import bpy, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
N = int(a[0]) if a else 6
view = a[1] if len(a) > 1 else 'quarter'
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'anim_v1.blend'))
rig = bpy.data.objects['Hand_Rig']; sc = bpy.context.scene
CAM = {'quarter': ((-2.6, -3.6, 1.3), (0, -0.1, 0.3)), 'side': ((4.5, -0.1, 0.3), (0, -0.1, 0.3)),
       'front': ((0, -4.5, 0.5), (0, 0, 0.3))}[view]
tiles = []
for act in [x for x in bpy.data.actions if x.use_fake_user]:
    rig.animation_data.action = act
    if len(getattr(act, 'slots', [])):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
    row = []
    for k in range(N):
        f = round(f0 + (f1 - f0) * k / max(1, N - 1))
        sc.frame_set(f)
        p = os.path.join(HERE, 'work', f'_sheet_{act.name}_{k}.png')
        C.render(*CAM, 1.0, p, res=(360, 300))
        row.append(p)
    tiles.append((act.name, row))
import json
json.dump(tiles, open(os.path.join(HERE, 'work', '_sheet.json'), 'w'))
