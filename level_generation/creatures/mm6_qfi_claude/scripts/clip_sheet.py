"""Clip review: every action of work/<blend> (default anim_v1.blend) sampled at FRAMES evenly spaced times, clay,
front and three-quarter, the rock shown or hidden (work/clip_sheet.json {"blend": ..., "rock": bool, "actions": []}).
Writes review/clips/<action>_<i>_<view>.png and review/clips/frames.json; compose_clips.py builds the sheets."""
import bpy, sys, json
from pathlib import Path
P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P / 'scripts'))
import common
cfg = json.loads((P / 'work' / 'clip_sheet.json').read_text())
FRAMES = cfg.get('frames', 8)
bpy.ops.wm.open_mainfile(filepath=str(P / 'work' / cfg.get('blend', 'anim_v1.blend')))
rig = bpy.data.objects['Rig']; rock = bpy.data.objects['Rock']
rock.hide_render = not cfg.get('rock', False)
PLACE = (lambda d: d.get('queen_actor_location', d['queen_location']))(json.loads((P / 'work' / 'placement.json').read_text()))
scene = bpy.context.scene
common.workbench_clay(scene)
out = P / 'review' / 'clips'; out.mkdir(parents=True, exist_ok=True)
acts = cfg.get('actions') or [a.name for a in bpy.data.actions]
index = {}
for name in acts:
    act = bpy.data.actions[name]
    rig.animation_data_create(); rig.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = act.frame_range
    files = {}
    for i in range(FRAMES):
        f = f0 + (f1 - f0) * i / max(FRAMES - 1, 1)
        scene.frame_set(int(f), subframe=f % 1)
        for view in cfg.get('views', ('front', 'three_quarter')):
            prefix = out / f'{name}_{i}'
            path = common.render_views(str(prefix), PLACE[2] + 1.2, 2.9 if not cfg.get('rock') else 3.4,
                                       views=(view,), resolution=(300, 400), target=(PLACE[0], PLACE[1]))[0]
            files[(i, view)] = path
    index[name] = {f'{i}_{view}': path for (i, view), path in files.items()}
    print('SHEET', name, f0, f1)
(out / 'frames.json').write_text(json.dumps({'frames': FRAMES, 'actions': index}))
