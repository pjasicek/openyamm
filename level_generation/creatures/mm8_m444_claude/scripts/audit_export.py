"""Compare animated Blender bone matrices with the reimported runtime GLB; report gait and dimensions."""
from pathlib import Path
import bpy,json,math
import numpy as np
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'export/mm8_m444.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene
roles=['Standing','Walking','Running','Attack','Cast','Hit','Death','Dead','Fidget'];bones=list(rig.pose.bones.keys());samples={};report={'clips':{},'gait':{}}
body=bpy.data.objects.get('Smuggler') or bpy.data.objects['Body']
for role in roles:
 a=bpy.data.actions[role];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];duration=float(a.frame_range[1])/30;times=np.linspace(0,duration,max(2,int(duration*48)+1));rows=[];feet=[]
 for t in times:
  f=t*30;sc.frame_set(int(f),subframe=f-int(f));rows.append({n:np.array(rig.matrix_world@rig.pose.bones[n].matrix) for n in bones})
  feet.append([list((rig.matrix_world@rig.pose.bones['B_'+side+'_Foot'].matrix).translation) for side in ['L','R']])
 samples[role]=(times,rows);report['clips'][role]={'seconds':duration}
 if role in ['Walking','Running']:
  feet=np.array(feet);report['gait'][role]={'stride_2x_foot_excursion_m':float(2*np.mean(np.ptp(feet[:,:,1],axis=0)))}
 if role=='Standing':
  sc.frame_set(0);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();groups={g.index:g.name for g in body.vertex_groups};ids=[v.index for v in body.data.vertices if not any(groups[g.group]=='Sword' and g.weight>.5 for g in v.groups)];z=np.array([(body.matrix_world@me.vertices[i].co).z for i in ids]);ev.to_mesh_clear();report['standing_body_height_m']=float(np.ptp(z));report['native_height_units']=179;report['runtime_scale']=179/float(np.ptp(z))
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(p/'export/mm8_m444.glb'));rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');sc=bpy.context.scene
for role,(times,rows) in samples.items():
 a=next(a for a in bpy.data.actions if a.name.split('@')[-1]==role);rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];worst=0;angle=0
 for t,ref in zip(times,rows):
  f=t*sc.render.fps;sc.frame_set(int(f),subframe=f-int(f))
  for n in bones:
   m=np.array(rig.matrix_world@rig.pose.bones[n].matrix);worst=max(worst,float(np.linalg.norm(m[:3,3]-ref[n][:3,3])));angle=max(angle,float(np.max(np.abs(m[:3,:3]-ref[n][:3,:3]))))
 report['clips'][role].update(max_joint_position_error_mm=worst*1000,max_matrix_rotation_element_error=angle)
 assert worst<.001,(role,worst)
 assert angle<.002,(role,angle)
(p/'work/export_audit.json').write_text(json.dumps(report,indent=2));print('EXPORT_AUDIT',json.dumps(report))
