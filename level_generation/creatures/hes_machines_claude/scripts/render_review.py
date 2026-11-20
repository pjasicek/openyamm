"""Eevee review stills of a runtime export (export/hes_<name>.glb as the game loads it: emission on, the glow / dark
switch by bone scale): per clip and frame, from the front three-quarter and the back three-quarter, on a mid-grey
ground. Args: -- <name> <out prefix> <clip:frame>[,<clip:frame>...]"""
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = sys.argv[sys.argv.index('--') + 1:]
name, prefix, shots = args[0], args[1], [s.split(':') for s in args[2].split(',')]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.render.fps = 30          # before the import: it keys the clips at the scene rate
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, 'export', f'hes_{name}.glb'))
scene = bpy.context.scene
for engine in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'):
    try:
        scene.render.engine = engine
        break
    except TypeError:
        continue
scene.render.resolution_x, scene.render.resolution_y = 640, 800
world = bpy.data.worlds.new('w'); scene.world = world
world.use_nodes = True
bg = next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND')
bg.inputs['Color'].default_value = (0.05, 0.05, 0.06, 1); bg.inputs['Strength'].default_value = 1.0
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); scene.collection.objects.link(sun)
sun.data.energy = 3.0; sun.rotation_euler = (math.radians(50), 0, math.radians(30))
fill = bpy.data.objects.new('fill', bpy.data.lights.new('fill', 'SUN')); scene.collection.objects.link(fill)
fill.data.energy = 1.0; fill.rotation_euler = (math.radians(60), 0, math.radians(200))
try:
    scene.eevee.use_bloom = True
except AttributeError:
    pass
rig = next(o for o in scene.objects if o.type == 'ARMATURE')
meshes = [o for o in scene.objects if o.type == 'MESH']
# only LOD0: hide the LOD and shadow meshes the GLB carries
for o in meshes:
    if 'LOD' in o.name or 'Shadow' in o.name or 'shadow' in o.name:
        o.hide_render = True
co = np.array([(o.matrix_world @ v.co)[:] for o in meshes if not o.hide_render for v in o.data.vertices])
lo, hi = Vector(co.min(0)), Vector(co.max(0)); centre = (lo + hi) / 2; size = (hi - lo).length
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); scene.collection.objects.link(cam); scene.camera = cam
cam.data.lens = 50
rig.animation_data_create()
for clip, frame in shots:
    action = bpy.data.actions[clip]
    rig.animation_data.action = action
    if hasattr(action, 'slots') and len(action.slots):
        rig.animation_data.action_slot = action.slots[0]
    scene.frame_set(int(frame))
    for view, az in (('front', 35.0), ('back', 200.0)):
        a, e = math.radians(az), math.radians(14)
        # glTF +z is the model's front; imported into Blender as -y
        d = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
        cam.location = centre + d * size * 1.6
        cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = f'{prefix}_{clip}_{frame}_{view}.png'
        bpy.ops.render.render(write_still=True)
print('RENDERED', name, shots)
