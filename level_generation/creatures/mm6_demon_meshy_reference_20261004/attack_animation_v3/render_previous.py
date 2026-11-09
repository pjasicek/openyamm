"""Render revision-2 Attack anchors for a direct before/after comparison."""
import bpy
from pathlib import Path
from mathutils import Vector

stage = Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(stage.parent / 'attack_animation_v2/mm6_demon_attack.blend'))
scene = bpy.context.scene
rig = scene.objects['Demon_Attack_Rig']
action = next(t.strips[0].action for t in rig.animation_data.nla_tracks if t.name == 'Attack')
for track in rig.animation_data.nla_tracks:
    track.mute = True
rig.animation_data.action = action
rig.animation_data.action_slot = action.slots[0]
scene.render.resolution_x = 1300
scene.render.resolution_y = 1100
for frame in [0, 6, 12, 18, 24, 30]:
    scene.frame_set(frame)
    for name, direction, center, scale in [('front', (0, -6, 0), (0, -.10, .86), 2.35),
                                           ('feet_detail', (-1.5, -3, 1.1), (0, -.25, .17), .8)]:
        center = Vector(center)
        scene.camera.data.ortho_scale = scale
        scene.camera.location = center + Vector(direction)
        scene.camera.rotation_euler = (center - scene.camera.location).to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = str(stage / 'review_frames' / f'before_{name}_{frame:02d}.png')
        bpy.ops.render.render(write_still=True)
print('Rendered original revision-2 Attack, not locomotion, for before/after plates.')
