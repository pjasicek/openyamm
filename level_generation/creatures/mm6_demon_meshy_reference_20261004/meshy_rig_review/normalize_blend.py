"""Convert the isolated Blender library into a normal directly openable project."""
import bpy
import hashlib
import json
from pathlib import Path

stage = Path(__file__).resolve().parent
path = stage / 'mm6_demon_rig_corrected.blend'
bpy.ops.wm.open_mainfile(filepath=str(path))
assert len(bpy.data.scenes) == 1
scene = bpy.data.scenes['MM6_Demon_Rig_Repair']
bpy.context.window.scene = scene
rig = scene.objects['Demon_Rig_Review']
obj = scene.objects['Demon_Rigged_Review']
assert len(rig.data.bones) == 79
assert len(obj.data.vertices) == 7899 and len(obj.data.polygons) == 15686
assert {track.name for track in rig.animation_data.nla_tracks} == {'Walking', 'Running'}
assert {action.name for action in bpy.data.actions} == {'Walking', 'Running'}
scene.frame_set(12)
rig.hide_set(True)
for item in scene.objects:
    item.select_set(False)
obj.select_set(True)
bpy.context.view_layer.objects.active = obj
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces.active.shading.type = 'SOLID'
            area.spaces.active.region_3d.view_perspective = 'CAMERA'
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(path), compress=True)
report = {'normal_startup_project': True, 'scenes': [item.name for item in bpy.data.scenes],
          'bones': len(rig.data.bones), 'vertices': len(obj.data.vertices),
          'triangles': len(obj.data.polygons), 'actions': [action.name for action in bpy.data.actions],
          'fps': scene.render.fps, 'windows': len(bpy.data.window_managers[0].windows),
          'workspaces': [workspace.name for workspace in bpy.data.workspaces]}
assert report['windows'] > 0 and report['workspaces'], report
(stage / 'blend_startup_validation.json').write_text(json.dumps(report, indent=2) + '\n')
acceptance = json.loads((stage / 'acceptance.json').read_text())
acceptance['normal_blender_startup_project_verified'] = True
acceptance['files'][path.name] = {'bytes': path.stat().st_size,
                                 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
(stage / 'acceptance.json').write_text(json.dumps(acceptance, indent=2) + '\n')
print(json.dumps(report, indent=2))
