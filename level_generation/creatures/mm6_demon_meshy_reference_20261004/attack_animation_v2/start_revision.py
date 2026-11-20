import bpy
import json
from pathlib import Path
stage = Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_demon_meshy_reference_20261004/attack_animation_v2')
original = bpy.data.scenes['MM6_Demon_Attack']
original.name = 'MM6_Demon_Attack_v1'
original_rig = original.objects['Demon_Attack_Rig']
original_mesh = original.objects['Demon_Attack_Mesh']
original_rig.name = 'Demon_Attack_v1_Rig'
original_mesh.name = 'Demon_Attack_v1_Mesh'
scene = original.copy()
scene.name = 'MM6_Demon_Attack'
for obj in list(scene.objects):
    scene.collection.objects.unlink(obj)
rig = original_rig.copy()
rig.data = original_rig.data.copy()
rig.name = 'Demon_Attack_Rig'
mesh = original_mesh.copy()
mesh.data = original_mesh.data.copy()
mesh.name = 'Demon_Attack_Mesh'
mesh.parent = rig
for modifier in mesh.modifiers:
    if modifier.type == 'ARMATURE':
        modifier.object = rig
scene.collection.objects.link(rig)
scene.collection.objects.link(mesh)
camera = original.camera.copy()
camera.data = original.camera.data.copy()
camera.name = 'DemonAttackCamera_v2'
scene.collection.objects.link(camera)
scene.camera = camera
bpy.context.window.scene = scene
rig.hide_set(False)
for track in rig.animation_data.nla_tracks:
    if track.name == 'Attack':
        action = track.strips[0].action.copy()
        action.name = 'Demon_Revision_Attack'
        track.strips[0].action = action
        track.strips[0].action_slot = action.slots[0]
    track.mute = True
rig.animation_data.action = action
rig.animation_data.action_slot = action.slots[0]
(stage / 'revision_source.json').write_text(json.dumps({
    'previous_scene': original.name, 'scene': scene.name,
    'previous_package': '../attack_animation/mm6_demon_attack.blend',
    'user_findings': 'Forearm/wrist distortion at 18–28; incorrect left palm orientation.',
    'approved_motion_to_preserve': 'Both shoulder-to-elbow chains.',
}, indent=2) + '\n')
print('Created isolated hand/forearm correction scene', scene.name)
