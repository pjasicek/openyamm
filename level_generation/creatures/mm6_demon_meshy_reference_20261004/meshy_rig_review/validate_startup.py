"""Validate the delivered project when passed directly to Blender at startup."""
import bpy
import json
from pathlib import Path

stage = Path(__file__).resolve().parent
scene = bpy.context.scene
assert scene.name == 'MM6_Demon_Rig_Repair', scene.name
assert len(bpy.data.scenes) == 1
rig = scene.objects['Demon_Rig_Review']
obj = scene.objects['Demon_Rigged_Review']
assert len(rig.data.bones) == 79 and len(obj.data.vertices) == 7899
assert len(obj.data.polygons) == 15686 and scene.render.fps == 48
assert set(action.name for action in bpy.data.actions) == {'Walking', 'Running'}
for bone, parent in [('Bone_041', 'mixamorig:LeftShoulder'), ('Bone_036', 'mixamorig:RightShoulder')]:
    assert rig.data.bones[bone].parent.name == parent
assert rig.animation_data.action.name == 'Walking'
assert len(bpy.context.window_manager.windows) == 1
report = {'direct_startup_validation': 'passed', 'scene': scene.name,
          'actions': [action.name for action in bpy.data.actions], 'fps': scene.render.fps,
          'corrected_shoulder_parents_verified': True, 'vertices': len(obj.data.vertices),
          'triangles': len(obj.data.polygons), 'bones': len(rig.data.bones)}
(stage / 'blend_direct_startup_validation.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
