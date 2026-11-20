"""Front (slightly raised) renders of sampled frames of every clip in work/anim_v1.blend -> review/clips_v1/<clip>.png
(one row per clip, time under each frame)."""
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'scripts'))
import reactor_blender as RB  # noqa: E402

bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'anim_v1.blend'))
RB.setup_materials(render=True)
rig = bpy.data.objects['Reactor_Rig']
scene = bpy.context.scene
try:
    scene.render.engine = 'BLENDER_EEVEE'
except TypeError:
    scene.render.engine = 'BLENDER_EEVEE_NEXT'
scene.view_settings.view_transform = 'Standard'
world = bpy.data.worlds.new('W'); scene.world = world; world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.25, 0.26, 0.29, 1)
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3.0
sun.rotation_euler = (math.radians(50), 0, math.radians(-30)); scene.collection.objects.link(sun)
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); scene.collection.objects.link(cam); scene.camera = cam
view = os.environ.get('REA_VIEW', 'front')
if view == 'front':
    cam.location = Vector((0, -11.0, 2.0)); target = Vector((0, 0, 2.15)); cam.data.lens = 40
else:
    cam.location = Vector((7.0, -8.0, 1.0)); target = Vector((0, 0, 2.15)); cam.data.lens = 40
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.render.resolution_x, scene.render.resolution_y = 300, 420
scene.render.film_transparent = False
out_dir = os.path.join(HERE, 'review', os.environ.get('REA_OUT', 'clips_v1'))
os.makedirs(out_dir, exist_ok=True)
clips = os.environ.get('REA_CLIPS', 'Standing,Attack,Hit,Death').split(',')
step = int(os.environ.get('REA_STEP', '3'))
for clip in clips:
    act = bpy.data.actions[clip]
    rig.animation_data.action = act
    first, last = (int(v) for v in act.frame_range)
    for f in range(first, last + 1, step):
        scene.frame_set(f)
        scene.render.filepath = os.path.join(out_dir, f'{clip}_{f:03d}.png')
        bpy.ops.render.render(write_still=True)
print('SHEETS', out_dir)
