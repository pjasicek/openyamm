import bpy
import json
from pathlib import Path
stage=Path(__file__).resolve().parent
path=stage/'mm6_demon_attack.blend'
bpy.ops.wm.open_mainfile(filepath=str(path))
assert len(bpy.data.scenes)==1
scene=bpy.data.scenes['MM6_Demon_Attack']
bpy.context.window.scene=scene
rig=scene.objects['Demon_Attack_Rig'];mesh=scene.objects['Demon_Attack_Mesh']
assert len(rig.data.bones)==85 and len(mesh.data.vertices)==7899
assert len(mesh.data.polygons)==15686
for track in rig.animation_data.nla_tracks:
 track.strips[0].action.name=track.name
 track.mute=True
action=bpy.data.actions['Attack']
rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0]
scene.frame_start=0;scene.frame_end=36;scene.frame_set(12)
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':
   area.spaces.active.shading.type='SOLID'
   area.spaces.active.region_3d.view_perspective='CAMERA'
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True)
report={'normal_startup_project':True,'scenes':[s.name for s in bpy.data.scenes],
 'actions':[a.name for a in bpy.data.actions],'bones':len(rig.data.bones),'vertices':len(mesh.data.vertices),
 'triangles':len(mesh.data.polygons),'active_action':rig.animation_data.action.name,
 'windows':len(bpy.data.window_managers[0].windows),'fps':scene.render.fps}
assert report['windows']>0 and set(report['actions'])=={'Attack','Walking','Running'}
(stage/'blend_startup_validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
