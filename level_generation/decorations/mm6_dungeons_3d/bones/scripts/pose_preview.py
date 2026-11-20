"""Front orthographic render of a posed skeleton LOD0 framed like the cage sprite (x2 pixels), for overlaying on the
sprite. Usage: blender --background ../work/skeleton_<pose>.blend --python pose_preview.py -- <out.png> <width units>
<height units> [yaw degrees]"""
import math
import sys

import bpy
from mathutils import Vector

args = sys.argv[sys.argv.index('--') + 1:]
out, width, height = args[0], float(args[1]), float(args[2])
yaw = math.radians(float(args[3])) if len(args) > 3 else 0.0
zoom = float(args[4]) if len(args) > 4 else 2.0
U = 1 / 81.7
scene = bpy.context.scene
for engine in ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'):
    try:
        scene.render.engine = engine
        break
    except TypeError:
        continue
scene.render.resolution_x = int(width * zoom); scene.render.resolution_y = int(height * zoom)
scene.render.film_transparent = True
scene.view_settings.view_transform = 'Standard'
for o in scene.objects:
    if o.type == 'MESH':
        o.hide_render = not o.name.endswith('L0')
world = scene.world or bpy.data.worlds.new('W'); scene.world = world; world.use_nodes = True
next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND').inputs['Strength'].default_value = 0.5
sun = bpy.data.objects.new('S', bpy.data.lights.new('S', 'SUN')); scene.collection.objects.link(sun)
sun.data.energy = 2.5; sun.rotation_euler = (math.radians(40), 0, math.radians(-30))
cam = bpy.data.objects.new('C', bpy.data.cameras.new('C')); scene.collection.objects.link(cam); scene.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = max(width, height) * U
d = Vector((math.sin(yaw), -math.cos(yaw), 0))
cam.location = Vector((0, 0, height / 2 * U)) + d * 10
cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
scene.render.filepath = out
bpy.ops.render.render(write_still=True)
