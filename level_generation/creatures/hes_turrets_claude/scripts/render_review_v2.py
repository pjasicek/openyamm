"""Eevee review renders of a v2 turret actor on its mount: rest from the concept's camera (front three-quarter of the
turret's left, slightly from below), aim up (B_Barrel +MAX_UP), aim down (MIN_DOWN, side), the Attack's shot frame,
Dead, a head close-up and the back. The energy material glows (emission = its base colour x 1.5) as a stand-in for the
engine's emissive + bloom. Writes review/<actor>_<view>.png. Args: -- <ward_turret|gate_bastion> [max_up min_down]"""
import math
import os
import sys

import bpy
from mathutils import Quaternion, Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
args = sys.argv[sys.argv.index('--') + 1:]
NAME = args[0]
MAX_UP, MIN_DOWN = (float(args[1]), float(args[2])) if len(args) > 2 else (30.0, -35.0)
ACTOR = f'hes_{NAME}_actor'
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'export', f'{ACTOR}.blend'))
bpy.ops.import_scene.gltf(filepath=os.path.join(REPO, 'level_generation', 'props', 'hesper_decorations', 'work',
                                                'hard_surface', f'hes_{NAME}_mount.glb'))
scene = bpy.context.scene
rig = bpy.data.objects['Rig']
for mat in bpy.data.materials:
    if mat.name.endswith('_Energy') and mat.use_nodes:
        nodes, links = mat.node_tree.nodes, mat.node_tree.links
        bsdf = nodes['Principled BSDF']; tex = next(n for n in nodes if n.type == 'TEX_IMAGE')
        links.new(tex.outputs['Color'], bsdf.inputs['Emission Color'])
        bsdf.inputs['Emission Strength'].default_value = 1.5
engines = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items]
scene.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in engines else 'BLENDER_EEVEE'
scene.render.resolution_x, scene.render.resolution_y = 900, 700
world = scene.world or bpy.data.worlds.new('World'); scene.world = world
world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.16, 0.15, 0.15, 1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value = 1.6
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); scene.collection.objects.link(sun)
sun.data.energy = 3.2; sun.rotation_euler = (math.radians(45), 0, math.radians(30))
fill = bpy.data.objects.new('Fill', bpy.data.lights.new('Fill', 'SUN')); scene.collection.objects.link(fill)
fill.data.energy = 1.0; fill.rotation_euler = (math.radians(70), 0, math.radians(200))
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


heavy = NAME == 'gate_bastion'
h = 2.1 if heavy else 1.58
d = 1.45 if heavy else 1.0
mid = (0, -0.35 * d, 0.55 * h)


def shot(view, location, target=mid, lens=78):
    cam.data.lens = lens
    look(location, target)
    scene.render.filepath = os.path.join(HERE, 'review', f'{ACTOR}_{view}.png')
    bpy.ops.render.render(write_still=True)


concept_cam = (3.3 * d, -4.4 * d, 0.45 * h)               # front three-quarter of the turret's left, a little below
set_pose(); shot('rest', concept_cam)
set_pose(0, MAX_UP); shot('aim_up', concept_cam)
set_pose(0, MIN_DOWN); shot('aim_down', (5.4 * d, -0.6 * d, 0.6 * h))
set_pose(); clip_frame('Attack', 5); shot('attack_shot', (4.6 * d, -1.8 * d, 0.9 * h))
set_pose(); clip_frame('Dead', 0); shot('dead', (4.6 * d, -1.8 * d, 0.9 * h))
set_pose(); shot('head_closeup', (1.9 * d, -2.2 * d, 0.95 * h), (0, -0.3 * d, 0.75 * h), 50)
set_pose(); shot('back', (-3.0 * d, 4.4 * d, 0.8 * h))
set_pose(); shot('side', (5.6 * d, -0.35 * d, 0.5 * h))
set_pose(); shot('back_straight', (0.0, 5.6 * d, 0.6 * h))
print('REVIEW', ACTOR)
