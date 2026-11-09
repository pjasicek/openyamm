"""Static review renders of work/model_v1.blend in the idle pose: front orthographic at the native sprite framing
(680 x 924, 2 px per logical px, ground at the bottom), a front three-quarter and the party's eye view.
Writes review/static_v1/*.png."""
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'scripts'))
import reactor_blender as RB  # noqa: E402

bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'model_v1.blend'))
RB.setup_materials(render=True)
rig = bpy.data.objects['Reactor_Rig']
pose = os.environ.get('REA_POSE', 'idle')
if pose == 'idle':
    RB.idle_pose(rig)
elif pose == 'all':
    RB.idle_pose(rig, on=set(RB.TOGGLES))
scene = bpy.context.scene
try:
    scene.render.engine = 'BLENDER_EEVEE'
except TypeError:
    scene.render.engine = 'BLENDER_EEVEE_NEXT'
world = bpy.data.worlds.new('W'); scene.world = world
world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.28, 0.29, 0.32, 1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value = 1.0
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN'))
sun.data.energy = 3.0
sun.rotation_euler = (math.radians(50), 0, math.radians(-30))
scene.collection.objects.link(sun)
scene.render.film_transparent = True
scene.view_settings.view_transform = 'Standard'
out_dir = os.path.join(HERE, 'review', os.environ.get('REA_OUT', 'static_v1'))
os.makedirs(out_dir, exist_ok=True)
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
scene.collection.objects.link(cam); scene.camera = cam


def shoot(name, location, target, ortho=None, res=(680, 924), lens=50):
    cam.location = Vector(location)
    cam.rotation_euler = (Vector(target) - Vector(location)).to_track_quat('-Z', 'Y').to_euler()
    if ortho:
        cam.data.type = 'ORTHO'; cam.data.ortho_scale = ortho
    else:
        cam.data.type = 'PERSP'; cam.data.lens = lens
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.filepath = os.path.join(out_dir, name + '.png')
    bpy.ops.render.render(write_still=True)


# Native canvas: 340 x 454 logical px = 3.40 x 4.54 m, ground at the bottom row, pivot at x 0.
shoot('front_ortho', (0, -30, 4.54 / 2), (0, 0, 4.54 / 2), ortho=4.54)
shoot('three_quarter', (6.5, -9.0, 3.2), (0, 0, 2.1), res=(800, 1000), lens=45)
shoot('party_eye', (0.0, -9.5, 0.8), (0, 0, 2.1), res=(800, 1000), lens=40)
shoot('back', (-3.0, 9.5, 2.0), (0, 0, 2.1), res=(800, 1000), lens=45)
print('RENDERED', out_dir)
