"""Export the provisional assembled LOD0 for numerical checks; anatomy decision and final LODs remain pending."""
import bpy,json,sys,os
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/overseer_assembly.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
for name in ['OV_Equipment','OV_Glow','OV_Sash','DemonHead_A']:
 for m in bpy.data.materials:
  if m.name==name or m.name.startswith(name+'.'):m.use_backface_culling=True
parts=[o for o in bpy.data.objects if o.type=='MESH' and (o.name=='Body' or o.name.startswith(('Arm_','Sash_','OV_')))]
for o in parts:
 o.hide_render=False;o.hide_set(False)
 for slot in o.material_slots:
  if slot.material and slot.material.name.startswith('OV_'):
   base=slot.material.name.split('.')[0];slot.material=bpy.data.materials[base]
for o in bpy.data.objects:o.select_set(o in parts)
bpy.context.view_layer.objects.active=body;bpy.ops.object.join();body.name=body.data.name='OV_Assembled'
# Every source has four normalized influences, including the hand web smoothing.
assert max(sum(g.weight>1e-6 for g in v.groups) for v in body.data.vertices)<=4
for a in list(bpy.data.actions):
 if a.name.startswith('Winged_'):bpy.data.actions.remove(a)
rig.animation_data.action=bpy.data.actions['Overseer_Flight']
if rig.animation_data.action.slots:rig.animation_data.action_slot=rig.animation_data.action.slots[0]
for o in bpy.data.objects:o.select_set(o in (body,rig))
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(P/'work/overseer_assembled_lod0.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=False,export_attributes=False,export_morph=False,export_extras=False,export_reset_pose_bones=True,export_anim_slide_to_zero=True)
print('PREVIEW_EXPORT_DONE',sum(len(f.vertices)-2 for f in body.data.polygons),'triangles including all mutually exclusive boss equipment',flush=True)
sys.stdout.flush();sys.stderr.flush();os._exit(0)
