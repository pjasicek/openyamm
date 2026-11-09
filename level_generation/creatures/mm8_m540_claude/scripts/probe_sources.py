from pathlib import Path
import bpy,json
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(p.parent/'mm6_ogr_claude/export/mm6_ogr.glb'))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
print('IMPORTED_RIG',rig.name,'nla',[(t.name,t.mute,len(t.strips)) for t in rig.animation_data.nla_tracks],flush=True)
for a in bpy.data.actions:
 print('ACTION',a.name,[(s.identifier,s.target_id_type) for s in a.slots],list(a.frame_range),flush=True)
 if 'Walking' not in a.name and 'Running' not in a.name:continue
 rig.animation_data.action=a
 for slot in a.slots:
  rig.animation_data.action_slot=slot
  for f in [a.frame_range[0],sum(a.frame_range)/2,a.frame_range[1]]:
   bpy.context.scene.frame_set(int(f),subframe=f-int(f))
   print('SOURCE_POSE',a.name,slot.identifier,float(f),{n:list(rig.pose.bones[n].rotation_quaternion) for n in ['B_L_Thigh','B_L_Calf','B_L_UpperArm','B_Head']},flush=True)
bpy.ops.wm.open_mainfile(filepath=str(p/'work/pilot_sources.blend'))
rig=bpy.data.objects['Rig']
for name in ['Walking','Running']:
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
 for f in [0,sum(a.frame_range)/2,a.frame_range[1]]:
  bpy.context.scene.frame_set(int(f),subframe=f-int(f));print('RETARGETED_POSE',name,float(f),{n:list(rig.pose.bones[n].rotation_quaternion) for n in ['B_L_Thigh','B_L_Calf','B_L_UpperArm','B_Head']},flush=True)
