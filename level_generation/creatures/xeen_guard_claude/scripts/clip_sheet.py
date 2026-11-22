"""Clay frames of every clip of work/anim_v1.blend (or the blend given): N frames per clip from VIEW (front, side,
quarter, back), one row per clip -> review/clips_<view>.png (rows joined by sheet_rows in Python after).
Args: -- <view> [blend] [clip ...]"""
import bpy, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]
view = a[0]; blend = a[1] if len(a) > 1 else 'work/anim_v1.blend'; only = a[2:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, blend))
rig = bpy.data.objects['Guard_Rig']
import colorize; colorize.colorize(bpy.data.objects['Guard']); sc = bpy.context.scene
CAM = {'front': ((0, -5, 0.9), (0, 0, 0.9)), 'side': ((5, 0, 0.9), (0, 0, 0.9)),
       'quarter': ((3.4, -3.6, 1.6), (0, 0, 0.8)), 'back': ((0, 5, 0.9), (0, 0, 0.9))}[view]
out = os.path.join(HERE, 'work', 'clipframes'); os.makedirs(out, exist_ok=True)
N = 7
for act in bpy.data.actions:
    if only and act.name not in only: continue
    rig.animation_data.action = act
    if len(getattr(act, 'slots', [])): rig.animation_data.action_slot = act.slots[0]
    f0, f1 = act.frame_range
    for k in range(N):
        f = int(round(f0 + (f1 - f0) * k / (N - 1)))
        sc.frame_set(f)
        C.render(*CAM, 2.4, os.path.join(out, f'{act.name}_{view}_{k}.png'), res=(360, 420), color='MATERIAL')
print('DONE')
