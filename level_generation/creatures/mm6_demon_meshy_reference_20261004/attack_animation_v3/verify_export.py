"""Leave the reviewed revision visible in the live MCP scene."""
import bpy
import json
from pathlib import Path
from mathutils import Vector

stage = Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_demon_meshy_reference_20261004/attack_animation_v3')
scene = bpy.data.scenes['MM6_Demon_Attack_v3']
bpy.context.window.scene = scene
rig = scene.objects['Demon_Attack_v3_Rig']
mesh = scene.objects['Demon_Attack_v3_Mesh']
for track in rig.animation_data.nla_tracks:
    track.mute = True
action = bpy.data.actions['Demon_Native_Attack_v3']
rig.animation_data.action = action
rig.animation_data.action_slot = action.slots[0]
scene.frame_set(18)
center = Vector((0, -.10, .86))
scene.camera.data.ortho_scale = 2.35
scene.camera.location = center + Vector((0, -6, 0))
scene.camera.rotation_euler = (center - scene.camera.location).to_track_quat('-Z', 'Y').to_euler()
rig.hide_set(True)
for obj in scene.objects:
    obj.select_set(False)
mesh.select_set(True)
bpy.context.view_layer.objects.active = mesh
for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        area.spaces.active.shading.type = 'SOLID'
        area.spaces.active.region_3d.view_perspective = 'CAMERA'
(stage / 'live_viewport_review.json').write_text(json.dumps({'gui': not bpy.app.background,
    'scene': scene.name, 'frame': scene.frame_current, 'fps': scene.render.fps,
    'action': action.name, 'retained_scenes': [s.name for s in bpy.data.scenes]}, indent=2) + '\n')
print('Revision 3 displayed in Blender at attack frame 18; other scenes preserved.')
