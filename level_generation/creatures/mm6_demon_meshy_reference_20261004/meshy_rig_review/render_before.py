import bpy
import json
from pathlib import Path
from mathutils import Vector

stage = Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_demon_meshy_reference_20261004/meshy_rig_review')
scene = bpy.data.scenes['MM6_Demon_Rig_Repair']
bpy.context.window.scene = scene
rig = scene.objects['Demon_Rig_Review']
obj = scene.objects['Demon_Rigged_Review']
scene.render.engine = 'BLENDER_WORKBENCH'
scene.render.resolution_x = 1300
scene.render.resolution_y = 1300
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.film_transparent = False
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'SINGLE'
scene.display.shading.single_color = (.62, .66, .7)
scene.display.shading.show_shadows = False
scene.display.shading.show_cavity = True
scene.display.shading.cavity_type = 'BOTH'
scene.display.shading.background_type = 'WORLD'
scene.world = bpy.data.worlds.new('DemonRigReviewWorld')
scene.world.color = (.065, .075, .09)
camera_data = bpy.data.cameras.new('DemonRigCamera')
camera = bpy.data.objects.new('DemonRigCamera', camera_data)
scene.collection.objects.link(camera)
camera_data.type = 'ORTHO'
scene.camera = camera
for track in rig.animation_data.nla_tracks:
    track.mute = True
curve_stats = {}
for name in ('Walking', 'Running'):
    action = bpy.data.actions[name]
    stats = []
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    if any(part in curve.data_path for part in ('Bone_036', 'Bone_041', 'ToeBase', 'Toe_End')):
                        values = [point.co.y for point in curve.keyframe_points]
                        stats.append({'path': curve.data_path, 'axis': curve.array_index,
                                      'range': [min(values), max(values)]})
    curve_stats[name] = stats
(stage / 'feature_animation_channels.json').write_text(json.dumps(curve_stats, indent=2) + '\n')
print('Feature channels:', json.dumps({name: [entry for entry in entries
    if entry['range'][1] - entry['range'][0] > .001] for name, entries in curve_stats.items()}, indent=2))

def render(name, direction, center, scale):
    center = Vector(center)
    camera_data.ortho_scale = scale
    camera.location = center + Vector(direction) * 2
    camera.rotation_euler = (center - camera.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = str(stage / (name + '.png'))
    bpy.ops.render.render(write_still=True)

rig.data.pose_position = 'REST'
render('before_rest', (1.2, -3, .25), (0, -.05, .85), 2.12)
rig.data.pose_position = 'POSE'
for action_name, frame in [('Walking', 6), ('Walking', 17), ('Running', 4)]:
    action = bpy.data.actions[action_name]
    rig.animation_data.action = action
    rig.animation_data.action_slot = action.slots[0]
    scene.frame_set(frame)
    render('before_' + action_name.lower() + '_' + str(frame), (1.2, -3, .25), (0, -.05, .85), 2.12)
    if action_name == 'Walking' and frame == 6:
        render('before_shoulders', (0, 3, .25), (0, -.02, 1.37), 1.05)
        render('before_feet', (1.2, -3, .5), (0, -.14, .26), .95)
print('Rendered original rig at rest and walking/running samples')
