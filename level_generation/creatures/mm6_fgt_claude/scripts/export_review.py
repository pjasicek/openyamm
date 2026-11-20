"""Export the gated clay master, preserving the authored mace release and all eight roles."""
from pathlib import Path
import bpy,json
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v7.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];mace=bpy.data.objects['Mace']
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update()
for o in bpy.data.objects:o.select_set(o in (body,mace))
bpy.context.view_layer.objects.active=body;bpy.ops.object.join()
mat=bpy.data.materials.new('Clay');mat.use_nodes=True
body.data.materials.clear();body.data.materials.append(mat)
for f in body.data.polygons:f.material_index=0
rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=rig.animation_data.action.slots[0]
bpy.context.scene.render.fps=30
out=p/'review/viewer/mm6_fgt_clay.glb';out.parent.mkdir(parents=True,exist_ok=True)
for o in bpy.data.objects:o.select_set(o in (body,rig))
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(out),use_selection=True,export_format='GLB',export_yup=True,
 export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,
 export_skins=True,export_all_influences=False,export_attributes=False,export_morph=False,
 export_reset_pose_bones=True,export_anim_slide_to_zero=True)
json.dump({a.name:float((a.frame_range[1]-a.frame_range[0])/30) for a in bpy.data.actions},open(p/'work/clip_durations.json','w'),indent=2)
print('EXPORTED',out)
