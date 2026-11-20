import bpy,sys,json
from pathlib import Path
p=Path(__file__).resolve().parents[1];level=int(sys.argv[sys.argv.index('--')+1]);bpy.ops.wm.open_mainfile(filepath=str(p/'work'/f'round3_lod{level}.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];staff=bpy.data.objects['Staff'];scene=bpy.context.scene
for m in bpy.data.materials:m.name='old_'+m.name
for m,n in zip([*body.data.materials,*staff.data.materials],['Sorcerer','SorcererHead','SorcererStaff']):
 m.name=n+(f'LOD{level}' if level else '')+('_A' if n!='SorcererStaff' else '')
 for node in m.node_tree.nodes:
  if node.type=='BSDF_PRINCIPLED':node.inputs['Specular IOR Level'].default_value=.5;node.inputs['IOR'].default_value=1.5
for o in [body,staff]:
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.vertex_group_limit_total(limit=8);bpy.ops.object.vertex_group_normalize_all(lock_active=False)
rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=bpy.data.actions['Standing'].slots[0];scene.frame_set(0)
if level==0:bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/production_master.blend'))
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);staff.select_set(True);bpy.context.view_layer.objects.active=body;bpy.ops.object.join();body.name=body.data.name='Sorcerer'
for n in ['piece','finger','head','orig_co']:
 if n in body.data.attributes:body.data.attributes.remove(body.data.attributes[n])
for o in bpy.data.objects:o.select_set(o in [body,rig])
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(p/'export'/f'mm6_sor1_lod{level}.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=level==0,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=True,export_attributes=False,export_morph=False,export_image_format='AUTO',export_reset_pose_bones=True,export_anim_slide_to_zero=True)
