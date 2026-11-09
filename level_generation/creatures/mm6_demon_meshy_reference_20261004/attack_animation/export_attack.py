import bpy
import json
from pathlib import Path
from mathutils import Vector

stage=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_demon_meshy_reference_20261004/attack_animation')
review=json.loads((stage/'deformation_review.json').read_text())['summary']
assert review['samples']==145 and review['maximum_arm_length_relative_error']<1e-5
assert review['maximum_rigid_tip_edge_relative_error']<.001
assert review['maximum_foot_drift']<.002 and review['minimum_rigid_sole_height']>-.002
assert review['maximum_hand_torso_triangle_intersections']==0
assert review['minimum_triangle_area_ratio']>.1, 'Unresolved collapsing surface flag'
scene=bpy.data.scenes['MM6_Demon_Attack']
bpy.context.window.scene=scene
rig=scene.objects['Demon_Attack_Rig'];mesh=scene.objects['Demon_Attack_Mesh']
for item in scene.objects:item.select_set(False)
rig.hide_set(False);mesh.hide_set(False)
rig.select_set(True);mesh.select_set(True)
bpy.context.view_layer.objects.active=rig
rig.data.pose_position='POSE'
for track in rig.animation_data.nla_tracks:track.mute=True
scene.render.fps=48
scene.frame_start=0;scene.frame_end=36
bpy.ops.export_scene.gltf(
 filepath=str(stage/'mm6_demon_attack.glb'),export_format='GLB',use_selection=True,use_active_scene=True,
 export_animations=True,export_animation_mode='NLA_TRACKS',export_frame_range=False,
 export_force_sampling=True,export_frame_step=1,export_all_influences=True,export_def_bones=False,
 export_optimize_animation_size=False,export_materials='NONE',export_normals=True,export_yup=True,
 export_cameras=False,export_lights=False)
action=bpy.data.actions['Demon_Native_Attack']
rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0]
scene.frame_set(12)
center=Vector((0,-.10,.86))
scene.camera.data.ortho_scale=2.35
scene.camera.location=center+Vector((0,-6,0))
scene.camera.rotation_euler=(center-scene.camera.location).to_track_quat('-Z','Y').to_euler()
rig.hide_set(True)
for item in scene.objects:item.select_set(False)
mesh.select_set(True);bpy.context.view_layer.objects.active=mesh
for area in bpy.context.screen.areas:
 if area.type=='VIEW_3D':
  area.spaces.active.shading.type='SOLID'
  area.spaces.active.region_3d.view_perspective='CAMERA'
bpy.data.libraries.write(str(stage/'mm6_demon_attack.blend'),{scene},path_remap='RELATIVE')
manifest={
 'family':'mm6_dmn','native_attack_group':'danatka0','native_attack_frames':['dmnatk'+c+'0' for c in 'abcdef'],
 'native_attack_aliases':{'attack2':'Attack'},'native_attack_genuine_views':1,
 'fps':48,'clips':{'Attack':{'duration_seconds':.75,'frames':[0,36],'loop':False,'native_anchor_frames':[0,6,12,18,24,30],'endpoint':'F hold'},
 'Walking':{'duration_seconds':50/48,'frames':[0,50],'loop':True},'Running':{'duration_seconds':32/48,'frames':[0,32],'loop':True}},
 'vertices':len(mesh.data.vertices),'triangles':len(mesh.data.polygons),'bones':len(rig.data.bones),
 'existing_mesh_topology_preserved':True,'new_bones':[b.name for b in rig.data.bones if b.name.startswith('Demon_')],
 'materials_and_uvs':'Untextured supplied mesh; no source textures/UVs existed',
 'motion_depth':'Inferred from frontal native attack and standing anatomy views',
 'mesh_hand_anatomy':'Four physical long claws plus thumb; native attack art shows three long claws plus thumb. Supplied mesh retained.',
 'gameplay_installation':False,
}
(stage/'animation_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Exported staged GLB and isolated Blender project:',manifest['clips'])
