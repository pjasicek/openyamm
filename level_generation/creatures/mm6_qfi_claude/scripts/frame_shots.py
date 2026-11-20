"""Close renders of chosen (action, frame) pairs from work/<blend>, front / three-quarter / left, the rock hidden.
Config work/frame_shots.json {"blend": "anim_v2.blend", "shots": [["Attack", 18], ...], "zoom": 2.2}.
Writes review/shot_<action>_<frame>_<view>.png."""
import bpy, sys, json
from pathlib import Path
P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P / 'scripts'))
import common
cfg = json.loads((P / 'work' / 'frame_shots.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(P / 'work' / cfg.get('blend', 'anim_v2.blend')))
rig = bpy.data.objects['Rig']; bpy.data.objects['Rock'].hide_render = True
PLACE = (lambda d: d.get('queen_actor_location', d['queen_location']))(json.loads((P / 'work' / 'placement.json').read_text()))
scene = bpy.context.scene
common.workbench_clay(scene)
for name, f in cfg['shots']:
    act = bpy.data.actions[name]
    rig.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    scene.frame_set(int(f))
    common.render_views(str(P / 'review' / f'shot_{name}_{f}'), PLACE[2] + cfg.get('z', 1.55), cfg.get('zoom', 2.2),
                        views=('front', 'three_quarter', 'left'), resolution=(500, 500), target=(PLACE[0], PLACE[1]))
