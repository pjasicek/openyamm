"""Clay renders of chosen frames: frames.py <out.png> <clip:frame:view> ... (views front, quarter, side, top, back,
low = party eye height in front). Tiles of 500 px joined into one row by the caller (work/_frames.json)."""
import bpy, os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', a[0] if a[0].endswith('.blend') else 'anim_v1.blend'))
if a[0].endswith('.blend'): a = a[1:]
out, specs = a[0], a[1:]
rig = bpy.data.objects['Mantis_Rig']; sc = bpy.context.scene
CAM = {'front': ((0, -4, 0.6), (0, 0, 0.5)), 'quarter': ((2.4, -3.4, 1.6), (0, -0.1, 0.5)),
       'side': ((4.5, -0.1, 0.55), (0, -0.1, 0.5)), 'top': ((0, -0.01, 4), (0, 0, 0)), 'back': ((0, 4, 0.6), (0, 0, 0.5)),
       'low': ((0.3, -3.0, 1.2), (0, -0.1, 0.5))}
tiles = []
for k, spec in enumerate(specs):
    clip, f, view = spec.split(':')
    act = bpy.data.actions[clip]; rig.animation_data.action = act
    if len(getattr(act, 'slots', [])):
        rig.animation_data.action_slot = act.slots[0]
    sc.frame_set(int(f))
    p = os.path.join(HERE, 'work', f'_fr_{k}.png')
    C.render(*CAM[view], 1.6, p, res=(500, 500))
    tiles.append(p)
json.dump({'out': out, 'tiles': tiles}, open(os.path.join(HERE, 'work', '_frames.json'), 'w'))
