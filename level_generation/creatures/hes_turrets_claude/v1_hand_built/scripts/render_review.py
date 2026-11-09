"""Review renders of a turret actor on its mount decoration: rest (three-quarter), head +60 deg yaw with the barrel
raised 15 deg (three-quarter and a side close-up of the ring), the Attack's shot frame and the Dead pose.
Writes review/<name>_<view>.png (scripts/review_sheet.py joins them). Args: -- <actor name> <mount glb>"""
import math
import os
import sys

import bpy
from mathutils import Quaternion, Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
name, mount = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'export', f'{name}.blend'))
bpy.ops.import_scene.gltf(filepath=os.path.abspath(mount))
scene = bpy.context.scene
rig = bpy.data.objects['Rig']
scene.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in [e.identifier for e in
    bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE'
scene.render.resolution_x, scene.render.resolution_y = 900, 700
scene.render.film_transparent = False
world = scene.world or bpy.data.worlds.new('World'); scene.world = world
world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.42, 0.40, 0.44, 1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.9
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); scene.collection.objects.link(sun)
sun.data.energy = 3.0; sun.rotation_euler = (math.radians(50), 0, math.radians(-35))
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); scene.collection.objects.link(cam); scene.camera = cam
cam.data.lens = 50


def look(location, target):
    cam.location = Vector(location)
    cam.rotation_euler = (Vector(target) - cam.location).to_track_quat('-Z', 'Y').to_euler()


def set_pose(yaw=0.0, up=0.0):
    rig.animation_data.action = None
    for pb in rig.pose.bones:
        pb.matrix_basis.identity()
    for bone, axis, deg in (('B_Head', (0, 0, 1), yaw), ('B_Barrel', (1, 0, 0), -up)):
        rest = rig.data.bones[bone].matrix_local.to_3x3()
        pb = rig.pose.bones[bone]; pb.rotation_mode = 'QUATERNION'
        pb.rotation_quaternion = Quaternion((rest.inverted() @ Vector(axis)).normalized(), math.radians(deg))
    bpy.context.view_layer.update()


def clip_frame(action, frame):
    rig.animation_data.action = bpy.data.actions[action]
    if len(bpy.data.actions[action].slots):
        rig.animation_data.action_slot = bpy.data.actions[action].slots[0]
    scene.frame_set(frame)


heavy = 'bastion' in name
d = 1.35 if heavy else 1.0
shots = []


def shot(view, location, target):
    look(location, target)
    path = os.path.join(HERE, 'review', f'{name}_{view}.png')
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    shots.append(path)


mid = (0, -0.6 * d, 1.0 * d)
three_quarter = (3.6 * d, -4.6 * d, 2.4 * d)
set_pose(); shot('rest', three_quarter, mid)
set_pose(60, 15); shot('yaw60_up15', three_quarter, mid)
set_pose(60, 15); shot('ring_closeup', (2.2 * d, 0.6 * d, 0.95), (0, 0, 0.85))
set_pose(); clip_frame('Attack', 5); shot('attack_shot', (4.2 * d, -1.6 * d, 1.7 * d), mid)
set_pose(); clip_frame('Dead', 0); shot('dead', (4.2 * d, -1.6 * d, 1.7 * d), mid)
