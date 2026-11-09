"""Check wrist motion and the delivered GLB with its actual PBR materials."""
import json
import math
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'review'
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.render.fps = 48
bpy.ops.import_scene.gltf(filepath=str(ROOT / 'goblin_finished.glb'))
rig = next(o for o in scene.objects if o.type == 'ARMATURE')
body = next(o for o in scene.objects if o.type == 'MESH' and len(o.data.vertices) > 4000)
actions = {a.name: a for a in bpy.data.actions}
for track in rig.animation_data.nla_tracks:
    track.mute = True
for obj in scene.objects:
    if obj.type == 'MESH' and obj.find_armature() != rig:
        obj.hide_render = True

def select(name, frame):
    rig.animation_data.action = actions[name]
    rig.animation_data.action_slot = actions[name].slots[0]
    scene.frame_set(frame)
    bpy.context.view_layer.update()

motion = []
previous = {}
max_step = {}
for frame in range(37):
    select('MM6_Attack', frame)
    lower = rig.pose.bones['mixamorig:RightForeArm']
    hand = rig.pose.bones['mixamorig:RightHand']
    wrist_angle = math.degrees(lower.y_axis.angle(hand.y_axis))
    motion.append({'frame': frame, 'right_wrist_bend_degrees': wrist_angle})
    for pb in rig.pose.bones:
        q = pb.rotation_quaternion.copy()
        if pb.name in previous:
            step = math.degrees(previous[pb.name].rotation_difference(q).angle)
            step = min(step, 360-step)
            max_step[pb.name] = max(max_step.get(pb.name, 0), step)
        previous[pb.name] = q

assert max(abs(sum(g.weight for g in v.groups)-1) for v in body.data.vertices) < 1e-5
assert max(len(v.groups) for v in body.data.vertices) <= 4
report = json.loads((OUT / 'export_verification.json').read_text())
report['attack_motion'] = {
    'fps': 48,
    'maximum_bone_rotation_step_degrees': max(max_step.values()),
    'maximum_right_wrist_bend_degrees': max(row['right_wrist_bend_degrees'] for row in motion),
    'largest_rotation_steps': sorted(max_step.items(), key=lambda row: -row[1])[:8],
    'wrist_samples': motion,
}
report['materials'] = [
    {'name': m.name, 'images': sorted({n.image.name for n in m.node_tree.nodes
                                     if n.type == 'TEX_IMAGE' and n.image})}
    for m in body.data.materials if m and m.use_nodes
]
(OUT / 'export_verification.json').write_text(json.dumps(report, indent=2) + '\n')
print('MOTION_CHECK', json.dumps(report['attack_motion']['largest_rotation_steps']))
print('WRIST_CHECK', report['attack_motion']['maximum_right_wrist_bend_degrees'])
assert max(row['right_wrist_bend_degrees'] for row in motion) < 55
assert max(max_step.values()) < 45

scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 24
scene.cycles.use_denoising = True
scene.render.resolution_x = 650
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
scene.render.film_transparent = True
scene.view_settings.view_transform = 'AgX'
world = bpy.data.worlds.new('Goblin material check world')
world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (.20, .23, .26, 1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value = .6
scene.world = world
for name, pos, watts, size in [('Key', (-3, -4, 5), 750, 4),
                              ('Fill', (3, -2, 2.5), 400, 3),
                              ('Rim', (0, 3, 4), 650, 3)]:
    data = bpy.data.lights.new(name, 'AREA')
    data.energy = watts
    data.shape = 'DISK'
    data.size = size
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.location = pos
    obj.rotation_euler = (Vector((0, 0, 1))-obj.location).to_track_quat('-Z', 'Y').to_euler()
data = bpy.data.cameras.new('Material check camera')
cam = bpy.data.objects.new('Material check camera', data)
scene.collection.objects.link(cam)
scene.camera = cam
data.type = 'ORTHO'

def render(name, target, direction, scale):
    target = Vector(target)
    cam.location = target + Vector(direction)
    cam.rotation_euler = (target-cam.location).to_track_quat('-Z', 'Y').to_euler()
    data.ortho_scale = scale
    scene.render.filepath = str(OUT / (name+'.png'))
    bpy.ops.render.render(write_still=True)

select('MM6_Attack', 6)
render('material_windup', (0, 0, 1), (-3, -5, .25), 2.45)
render('material_back_plates', (0, 0, 1.23), (1.5, 5, 1), .90)
select('MM6_Attack', 0)
hand = rig.matrix_world @ rig.pose.bones['mixamorig:RightHand'].head
render('material_grip', hand, (-1, -5, 1), .48)
render('material_feet', (0, -.035, .10), (1, -5, 2), .65)
print('MATERIAL_REVIEW_COMPLETE')
