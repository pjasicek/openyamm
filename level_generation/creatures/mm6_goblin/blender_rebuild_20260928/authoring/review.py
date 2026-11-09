"""Short fixed-camera review queues, with saved progress and no changes to character geometry."""
import json
import traceback

import bpy
from mathutils import Vector

from mesh_tools import ROOT


def render_set(label, views=('front', 'quarter', 'profile', 'back', 'head')):
    scene = bpy.data.scenes['MM6 Goblin - Authored 15K']
    output = ROOT / 'review' / label
    output.mkdir(parents=True, exist_ok=True)
    queue = list(views)
    viewspec = {'front': ((0, -4, .86), (0, 0, .86), 1.94),
                'quarter': ((-3, -5, 2.05), (0, 0, .86), 1.94),
                'profile': ((-4, 0, .86), (0, 0, .86), 1.94),
                'back': ((0, 4, .86), (0, 0, .86), 1.94),
                'head': ((-.38, -2.5, 1.59), (0, 0, 1.565), .405),
                'head_front': ((0, -3, 1.565), (0, 0, 1.565), .405),
                'hand': ((-.92, -1.0, 1.04), (-.48, -.03, .85), .28)}

    def step():
        try:
            bpy.context.window.scene = scene
            if not queue:
                (output / 'status.json').write_text(json.dumps({'state': 'complete', 'views': list(views)}))
                return None
            name = queue.pop(0)
            (output / 'status.json').write_text(json.dumps({'state': 'rendering', 'view': name}))
            pos, target, scale = viewspec[name]
            if name == 'hand' and bpy.data.objects.get('GB15 Goblin rig'):
                target = bpy.data.objects['GB15 Goblin rig'].pose.bones['weapon.R'].head.copy()
                pos = target + Vector((-.7, -.65, .4))
            camera = scene.camera
            camera.location = pos
            camera.rotation_euler = (Vector(target) - camera.location).to_track_quat('-Z', 'Y').to_euler()
            camera.data.ortho_scale = scale
            scene.render.resolution_x = 960
            scene.render.resolution_y = 1120 if name in ['front', 'quarter', 'profile', 'back'] else 960
            scene.render.resolution_percentage = 100
            scene.render.filepath = str(output / (name + '.png'))
            bpy.ops.render.render(write_still=True)
            return .2
        except Exception:
            (output / 'status.json').write_text(json.dumps({'state': 'error', 'traceback': traceback.format_exc()}))
            return None

    bpy.app.timers.register(step, first_interval=.2)
    print('Scheduled', label, list(views))


def pose_set(label, specs):
    import motion
    scene = bpy.data.scenes['MM6 Goblin - Authored 15K']
    output = ROOT / 'review' / label
    output.mkdir(parents=True, exist_ok=True)
    queue = list(specs)

    def step():
        try:
            if not queue:
                (output / 'status.json').write_text(json.dumps({'state': 'complete'}))
                return None
            name, action, time, view = queue.pop(0)
            (output / 'status.json').write_text(json.dumps({'state': 'rendering', 'pose': name}))
            getattr(motion, action)(time)
            motion.ground_correct()
            target = Vector((0, 0, .86))
            offset = Vector((0, -4, 0)) if view == 'front' else Vector((-4, 0, 0)) if view == 'profile' else Vector((-3, -5, 1.3))
            if action == 'death' and time > .85:
                target = Vector((0, -.60, .17))
                offset = Vector((-2.3, -2.8, 3))
            scene.camera.location = target + offset
            scene.camera.rotation_euler = (-offset).to_track_quat('-Z', 'Y').to_euler()
            scene.camera.data.ortho_scale = 2.12
            scene.render.resolution_x = 1040
            scene.render.resolution_y = 1040
            scene.render.filepath = str(output / (name + '.png'))
            bpy.ops.render.render(write_still=True)
            return .2
        except Exception:
            (output / 'status.json').write_text(json.dumps({'state': 'error', 'traceback': traceback.format_exc()}))
            return None

    bpy.app.timers.register(step, first_interval=.2)
