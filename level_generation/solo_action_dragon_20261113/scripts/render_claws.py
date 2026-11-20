"""Render the exported forelegs view model from its Camera01 at chosen clip times, as the game frames them.

blender -b --python render_claws.py -- <forelegs.glb> <out_dir> <background.jpg> clip:seconds [clip:seconds ...]

The view model looks along +Y with +Z up at a 60-degree vertical field of view (screen right +X), as the engine draws
it.
"""

import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
glb, out, background = argv[0], Path(argv[1]), argv[2]
shots = [(item.split(':')[0], float(item.split(':')[1])) for item in argv[3:]]
out.mkdir(parents=True, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
# glTF times become frames at the scene's rate when importing: 30 fps first.
bpy.context.scene.render.fps = 30
bpy.ops.import_scene.gltf(filepath=glb)
scene = bpy.context.scene
scene.render.resolution_x, scene.render.resolution_y = 1600, 900
scene.render.resolution_percentage = 50
scene.render.film_transparent = True
scene.render.engine = 'BLENDER_EEVEE' if 'BLENDER_EEVEE' in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items.keys() else 'BLENDER_EEVEE_NEXT'
rig = next(o for o in scene.objects if o.type == 'ARMATURE')

camera_data = bpy.data.cameras.new('eye')
camera_data.sensor_fit = 'VERTICAL'
camera_data.angle_y = math.radians(60)
camera_data.clip_start, camera_data.clip_end = 1, 1000
camera = bpy.data.objects.new('eye', camera_data)
scene.collection.objects.link(camera)
scene.camera = camera

sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN'))
sun.data.energy = 3.5
sun.rotation_euler = (math.radians(50), 0, math.radians(150))
scene.collection.objects.link(sun)
fill = bpy.data.objects.new('fill', bpy.data.lights.new('fill', 'SUN'))
fill.data.energy = 1.0
fill.rotation_euler = (math.radians(-60), 0, math.radians(-30))
scene.collection.objects.link(fill)
world = bpy.data.worlds.new('w')
world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.45, 0.5, 0.6, 1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.6
scene.world = world

actions = {a.name: a for a in bpy.data.actions}
print('ACTIONS', sorted(actions)); print('RANGE', {n: tuple(a.frame_range) for n, a in actions.items() if 'attackright' in n})
paths = []
for clip, seconds in shots:
    action = actions.get(clip) or next((a for n, a in actions.items() if n.startswith(clip)), None)
    if action is None:
        print('MISSING', clip)
        continue
    rig.animation_data_create().action = action
    if hasattr(rig.animation_data, 'action_slot') and action.slots:
        rig.animation_data.action_slot = action.slots[0]
    scene.frame_set(round(seconds * 30))
    eye = rig.matrix_world @ rig.pose.bones['Camera01'].head
    camera.location = eye
    # Look along +Y, +Z up: the camera's -Z to +Y.
    camera.rotation_euler = (math.radians(90), 0, 0)
    path = out / f'{clip}_{seconds:.2f}.png'
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    paths.append((clip, seconds, path))

print('RENDERED', len(paths))
