import bpy
import json
from pathlib import Path

stage = Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_demon_meshy_reference_20261004/meshy_rig_review')
source = '/home/pjasicek/Downloads/Meshy_AI_mm6_demon_cleaned_All_Animations.glb'
print('Existing scene:', bpy.context.scene.name, 'Blender:', bpy.app.version_string)
scene = bpy.data.scenes.get('MM6_Demon_Rig_Repair')
new_scene = scene is None
if new_scene:
    scene = bpy.data.scenes.new('MM6_Demon_Rig_Repair')
bpy.context.window.scene = scene
if new_scene:
    bpy.ops.import_scene.gltf(filepath=source)
mesh_objects = [obj for obj in scene.objects if obj.type == 'MESH'
                and any(modifier.type == 'ARMATURE' for modifier in obj.modifiers)]
rigs = [obj for obj in scene.objects if obj.type == 'ARMATURE']
assert len(mesh_objects) == len(rigs) == 1, [(obj.name, obj.type) for obj in scene.objects]
obj, rig = mesh_objects[0], rigs[0]
obj.name = 'Demon_Rigged_Review'
rig.name = 'Demon_Rig_Review'
for item in scene.objects:
    if item.type == 'MESH' and item != obj:
        item.hide_render = True
        item.hide_set(True)
report = {'scene': scene.name, 'objects': [(item.name, item.type) for item in scene.objects],
          'vertices': len(obj.data.vertices), 'triangles': len(obj.data.polygons),
          'mesh_matrix': [list(row) for row in obj.matrix_world],
          'rig_matrix': [list(row) for row in rig.matrix_world],
          'bones': [{'name': bone.name, 'parent': bone.parent.name if bone.parent else None,
                     'head': list(bone.head_local), 'tail': list(bone.tail_local)} for bone in rig.data.bones],
          'active_action': rig.animation_data.action.name if rig.animation_data and rig.animation_data.action else None,
          'nla': [{'name': track.name, 'mute': track.mute,
                   'strips': [{'name': strip.name, 'action': strip.action.name,
                               'frames': [strip.frame_start, strip.frame_end]} for strip in track.strips]}
                  for track in rig.animation_data.nla_tracks],
          'actions': [{'name': action.name, 'frames': list(action.frame_range),
                       'slots': [slot.identifier for slot in action.slots]} for action in bpy.data.actions],
          'vertex_groups': [group.name for group in obj.vertex_groups],
          'modifiers': [{'name': modifier.name, 'type': modifier.type,
                         'rig': modifier.object.name if modifier.type == 'ARMATURE' else None}
                        for modifier in obj.modifiers]}
(stage / 'blender_rig_audit.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({key: value for key, value in report.items()
                  if key not in ('bones', 'vertex_groups')}, indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(stage / 'rig_before_weights.blend'), copy=True)
