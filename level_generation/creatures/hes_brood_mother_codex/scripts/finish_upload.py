"""Prepare the gated reduced rig and its identical static texturing upload."""
import bpy
import bmesh
import json
from pathlib import Path
import numpy as np
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/reduced_65.blend'))
rig=bpy.data.objects['Rig'];rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update()
body=bpy.data.objects['BroodMother'];base=body.vertex_groups['Base'].index
trim=[]
for socket in json.loads((P/'socket_layout.json').read_text())['sockets']:
 c=np.array(socket['top_centre_blender_m']);ids=[]
 cap=bpy.data.objects['Socket_'+socket['name']]
 cap_co=np.array([tuple(v.co) for v in cap.data.vertices]);top=cap_co[np.abs(cap_co[:,2]-cap_co[:,2].max())<1e-6]
 old=(top.min(0)+top.max(0))/2;delta=c-old
 for v in body.data.vertices:
  if v.co.z>old[2]+.03 or sum(e.weight for e in v.groups if e.group==base)<.999:continue
  radius=np.linalg.norm(np.array(v.co)[:2]-old[:2])
  fall=float(np.clip((.9-radius)/.25,0,1));fall=fall*fall*(3-2*fall)
  height=float(np.clip(v.co.z/max(old[2],.1),0,1));height=height*height*(3-2*height)
  v.co+=Vector(delta*fall*height)
 cap=bpy.data.objects['Socket_'+socket['name']]
 for v in cap.data.vertices:
  v.co+=Vector(delta)
  v.co.z=c[2]+(v.co.z-c[2])*(.32/.12)
 bpy.context.view_layer.objects.active=rig
 bpy.ops.object.mode_set(mode='EDIT')
 bone=rig.data.edit_bones['Socket_Sac_'+socket['name']];bone.head=Vector(c);bone.tail=Vector(c)+Vector((0,0,.1))
 bpy.ops.object.mode_set(mode='OBJECT')
 for v in body.data.vertices:
  radius=np.linalg.norm(np.array(v.co)[:2]-c[:2])
  if radius<.70 and c[2]-.14<v.co.z<c[2]+1.3:
   if sum(e.weight for e in v.groups if e.group==base)<.999:continue
   v.co.z=c[2]-.30-.02*(radius/.70);ids.append(v.index)
 trim.append({'socket':socket['name'],'trimmed_cradle_vertices':ids})
body.data.update()
for ob in bpy.context.scene.objects:
 if ob.type!='MESH':continue
 bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
 for mat in ob.data.materials:mat.use_backface_culling=True
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/texture_ready.blend'))
(P/'review/socket_final_trim.json').write_text(json.dumps(trim,indent=2)+'\n')
for ob in bpy.context.scene.objects:ob.select_set(ob.type in ('ARMATURE','MESH'))
bpy.context.view_layer.objects.active=rig
rig.animation_data.action=bpy.data.actions['Standing']
if rig.animation_data.action.slots:rig.animation_data.action_slot=rig.animation_data.action.slots[0]
bpy.context.scene.frame_set(0)
bpy.ops.export_scene.gltf(filepath=str(P/'work/texture_ready.glb'),use_selection=True,export_format='GLB',
 export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,
 export_frame_step=1,export_skins=True,export_all_influences=False,export_attributes=False,
 export_morph=False,export_reset_pose_bones=True,export_anim_slide_to_zero=True)
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update()
copies=[]
for ob in list(bpy.context.scene.objects):
 if ob.type!='MESH':continue
 dup=ob.copy();dup.data=ob.data.copy();dup.modifiers.clear();dup.parent=None
 dup.matrix_world=ob.matrix_world;dup.vertex_groups.clear();dup.data.materials.clear()
 bpy.context.scene.collection.objects.link(dup);copies.append(dup)
for ob in bpy.context.scene.objects:ob.select_set(ob in copies)
bpy.context.view_layer.objects.active=copies[0];bpy.ops.object.join()
bpy.context.object.name='BroodMotherTextureUpload'
(P/'texturing').mkdir(exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(P/'texturing/brood_mother_upload.glb'),use_selection=True,
 export_format='GLB',export_yup=True,export_animations=False,export_skins=False,export_materials='NONE',
 export_attributes=False)
print('UPLOAD_READY_CANDIDATE',json.dumps(trim))
