"""Fixed-view stills and short clips rendered from the reimported delivery GLB."""
import json
import traceback

import bpy
from mathutils import Vector

from mesh_tools import ROOT
import motion
import roundtrip


def render(output=None, clip_names=None, view_names=None, include_inspection=True):
    scene = bpy.data.scenes['GB15 Export validation']
    output = output or ROOT / 'review/final'
    output.mkdir(parents=True, exist_ok=True)
    tasks = []
    views = {'front': ((0, -4, .88), (0, 0, .88), 1.96),
             'quarter': ((-3, -5, 2.2), (0, 0, .87), 1.99),
             'left': ((-4, 0, .88), (0, 0, .88), 1.96),
             'right': ((4, 0, .88), (0, 0, .88), 1.96),
             'back': ((0, 4, .88), (0, 0, .88), 1.96),
             'head': ((-.20, -3, 1.585), (0, 0, 1.56), .42),
             'attack_prepare': ((0, -4, 1.57), (0, 0, 1.57), .55),
             'neck': ((0, -3.98, 1.455), (0, .02, 1.455), .46),
             'grip': (None, None, .30), 'thumb': (None, None, .30), 'free_hand': (None, None, .30),
             'free_front': (None, None, .30), 'free_palm': (None, None, .30),
             'corpse': ((-2.3, -3.5, 3.2), (0, -.65, .19), 2.10)}
    for name in views:
        if view_names is not None and name not in view_names:
            continue
        if name == 'attack_prepare':
            tasks.append(('still', name, 9, 'attack'))
        else:
            tasks.append(('still', name, 1, 'corpse' if name == 'corpse' else 'standing'))
    manifest = []
    for name, duration, spacing, function in motion.CLIPS:
        if clip_names is not None and name not in clip_names:
            continue
        fps = 12 if name in ['standing', 'corpse', 'fidget'] else 24
        frames = [1] if name == 'corpse' else list(range(1, round(duration * 48) + 1, 48 // fps))
        if name == 'death':
            frames.append(31)
        folder = output / ('frames_' + name)
        folder.mkdir(exist_ok=True)
        for index, frame in enumerate(frames):
            tasks.append(('motion', name, frame, index))
        manifest.append({'name': name, 'duration_seconds': duration, 'fps': fps, 'rendered_frames': len(frames),
                         'folder': folder.name, 'video': name + '.mp4'})
    (output / 'clips.json').write_text(json.dumps(manifest, indent=2) + '\n')
    inspection = []
    for name, action, duration in [('attack_front', 'attack', .75), ('walk_side', 'walk', 1.),
                                   ('walk_front', 'walk', 1.), ('walk_feet', 'walk', 1.)]:
        if not include_inspection or (clip_names is not None and action not in clip_names):
            continue
        folder = output / ('frames_' + name)
        folder.mkdir(exist_ok=True)
        frames = list(range(1, round(duration * 48) + 1, 2))
        for index, frame in enumerate(frames):
            tasks.append(('inspection', name, frame, index))
        inspection.append({'name': name, 'action': action, 'duration_seconds': duration, 'fps': 24,
                           'rendered_frames': len(frames), 'folder': folder.name, 'video': name + '.mp4'})
    (output / 'inspection_clips.json').write_text(json.dumps(inspection, indent=2) + '\n')
    total = len(tasks)

    def step():
        try:
            if not tasks:
                (output / 'status.json').write_text(json.dumps({'state': 'complete', 'renders': total}))
                roundtrip.activate_import('standing', 1)
                return None
            kind, name, frame, extra = tasks.pop(0)
            (output / 'status.json').write_text(json.dumps({'state': 'rendering', 'kind': kind, 'name': name,
                                                           'frame': frame, 'remaining': len(tasks), 'total': total}))
            action = extra if kind == 'still' else name.split('_')[0]
            arm = roundtrip.activate_import(action, frame)
            bpy.data.objects['GB15 Ground'].hide_render = kind == 'still' and name in \
                ['head', 'attack_prepare', 'neck', 'grip', 'thumb', 'free_hand', 'free_front', 'free_palm']
            if kind == 'still':
                position, target, scale = views[name]
                if name in ['grip', 'thumb']:
                    target = arm.matrix_world @ arm.pose.bones['weapon.R'].head
                    offset = (-.7, -.65, .40) if name == 'grip' else (.65, -.5, .30)
                    position = target + Vector(offset)
                if name in ['free_hand', 'free_front', 'free_palm']:
                    hand = arm.pose.bones['hand.L']
                    target = arm.matrix_world @ (hand.head + hand.vector * .9)
                    offset = (.65, -.7, .2)
                    if name == 'free_front':
                        offset = (0, -.9, 0)
                    elif name == 'free_palm':
                        offset = (-.65, -.75, .1)
                    position = target + Vector(offset)
                size = (960, 1120) if name in ['front', 'quarter', 'left', 'right', 'back'] else (960, 960)
                path = output / (name + '.png')
            else:
                position, target, scale = ((-3, -5, 2.3), (0, -.15, .90), 2.37)
                if name == 'corpse':
                    position, target, scale = views['corpse']
                elif name == 'attack_front':
                    position, target, scale = ((0, -4, 1.04), (0, -.10, 1.04), 2.4)
                elif name == 'walk_side':
                    position, target, scale = ((-4, 0, .90), (0, -.10, .90), 2.37)
                elif name == 'walk_front':
                    position, target, scale = ((0, -4, .90), (0, -.10, .90), 2.37)
                elif name == 'walk_feet':
                    position, target, scale = ((-4, 0, .45), (0, -.04, .45), 1.12)
                size = (720, 720)
                path = output / ('frames_' + name) / (str(extra).zfill(3) + '.png')
            camera = scene.camera
            camera.location = position
            camera.rotation_euler = (Vector(target) - camera.location).to_track_quat('-Z', 'Y').to_euler()
            camera.data.ortho_scale = scale
            scene.render.resolution_x, scene.render.resolution_y = size
            scene.render.resolution_percentage = 100
            scene.render.filepath = str(path)
            bpy.ops.render.render(write_still=True)
            return .1
        except Exception:
            (output / 'status.json').write_text(json.dumps({'state': 'error', 'traceback': traceback.format_exc()}))
            return None

    bpy.app.timers.register(step, first_interval=.2)
    print('Scheduled', total, 'delivery-GLB renders')
