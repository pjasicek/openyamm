"""Correct lower-lip weights without changing geometry, UVs, materials or animation tracks."""
from pathlib import Path
import bpy,json,sys,shutil
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
from common_rat import render_ortho
source=P/'work/rat_final.blend';backup=P/'work/rat_final_before_jaw_fix.blend'
if not backup.exists():shutil.copy2(source,backup)
bpy.ops.wm.open_mainfile(filepath=str(source))
mesh=bpy.data.objects['Rat'];rig=bpy.data.objects['Rat_Rig'];parts=mesh.data.attributes['anatomy'].data
changed=0
for v in mesh.data.vertices:
 x,y,z=v.co;part=parts[v.index].value
 if y>=-.31 and part not in (1,2,3,4):continue
 j=1.0 if part==3 else (0.0 if part in (1,2,4) else max(0,min(1,(-y-.385)/.025))*max(0,min(1,(.177-z)/.002)))
 h=max(0,min(1,(-y-.31)/.025))
 for g in mesh.vertex_groups:g.remove([v.index])
 for name,w in [('Jaw',j),('Head',(1-j)*h),('Neck1',(1-j)*(1-h))]:
  if w>1e-6:mesh.vertex_groups[name].add([v.index],w,'REPLACE')
 assert part==3 or z<.177 or j==0
 changed+=1
for img in bpy.data.images:
 if img.source=='FILE':img.reload()
rig.animation_data.action=bpy.data.actions['Standing'];bpy.context.scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(source))
for obj in bpy.data.objects:obj.select_set(obj in (mesh,rig))
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(P/'export/mm8_m452_lod0.glb'),use_selection=True,export_format='GLB',export_yup=True,
 export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,
 export_skins=True,export_all_influences=False,export_attributes=False,export_morph=False,
 export_image_format='AUTO',export_reset_pose_bones=True,export_anim_slide_to_zero=True)
rig.animation_data.action=bpy.data.actions['Attack'];bpy.context.scene.frame_set(12,subframe=.52)
render_ortho((2,-3,1.2),(0,-.05,.20),1.22,str(P/'review/jaw_fix_bite.png'),res=(1200,900),textured=True)
(P/'work/jaw_fix.json').write_text(json.dumps({'changed_vertices':changed,'upper_lip_start_z':.177,
 'lower_lip_full_weight_z':.175,'reason':'Upper muzzle vertices were wrongly blended to Jaw; preserves rigid upper muzzle and lower incisors.'},indent=2)+'\n')
