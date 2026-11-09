"""Focused hand-side and grip review before rebaking the seven actions."""
import json
import traceback

import bpy
from mathutils import Vector

import motion
import pose
from mesh_tools import ROOT


def render(label='hand_correction/latest'):
    scene = bpy.data.scenes['MM6 Goblin - Authored 15K']
    bpy.context.window.scene = scene
    pose.rig().animation_data.action = None
    output = ROOT / 'review' / label
    output.mkdir(parents=True, exist_ok=True)
    tasks = [('front', 'standing', 0), ('quarter', 'standing', 0),
             ('grip', 'standing', 0), ('thumb', 'standing', 0), ('free_hand', 'standing', 0),
             ('free_front', 'standing', 0), ('free_palm', 'standing', 0), ('neck', 'standing', 0),
             ('attack', 'attack', .34), ('hit', 'hit', .28), ('corpse', 'death', 1)]

    def step():
        try:
            if not tasks:
                pose.standing()
                (output / 'status.json').write_text(json.dumps({'state': 'complete'}))
                return None
            name, action, time = tasks.pop(0)
            (output / 'status.json').write_text(json.dumps({'state': 'rendering', 'view': name}))
            (pose.standing if action == 'standing' else getattr(motion, action))(time)
            motion.ground_correct()
            target, offset, scale = Vector((0, 0, .87)), Vector((-3, -5, 1.33)), 1.99
            if name == 'front':
                target, offset, scale = Vector((0, 0, .88)), Vector((0, -4, 0)), 1.96
            if name in ['grip', 'thumb']:
                target = pose.rig().pose.bones['weapon.R'].head.copy()
                offset = Vector((-.7, -.65, .40) if name == 'grip' else (.65, -.5, .30))
                scale = .30
            if name in ['free_hand', 'free_front', 'free_palm']:
                hand = pose.rig().pose.bones['hand.L']
                target = hand.head + hand.vector * .9
                offset, scale = Vector((.65, -.7, .2)), .30
                if name == 'free_front':
                    offset = Vector((0, -.9, 0))
                elif name == 'free_palm':
                    offset = Vector((-.65, -.75, .1))
            if name == 'neck':
                target, offset, scale = Vector((0, .02, 1.455)), Vector((0, -4, 0)), .46
            if name == 'corpse':
                target, offset, scale = Vector((0, -.65, .19)), Vector((-2.3, -2.85, 3.01)), 2.1
            bpy.data.objects['GB15 Ground'].hide_render = name in \
                ['grip', 'thumb', 'free_hand', 'free_front', 'free_palm', 'neck']
            scene.camera.location = target + offset
            scene.camera.rotation_euler = (-offset).to_track_quat('-Z', 'Y').to_euler()
            scene.camera.data.ortho_scale = scale
            scene.render.resolution_x = 960
            scene.render.resolution_y = 1120 if name in ['front', 'quarter'] else 960
            scene.render.resolution_percentage = 100
            scene.render.filepath = str(output / (name + '.png'))
            bpy.ops.render.render(write_still=True)
            return .1
        except Exception:
            (output / 'status.json').write_text(json.dumps({'state': 'error', 'traceback': traceback.format_exc()}))
            return None

    bpy.app.timers.register(step, first_interval=.2)
    print('Scheduled', len(tasks), 'focused hand and neck views')
