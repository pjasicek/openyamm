"""Signed anatomical audit of accepted joint motion, sampled at 48 Hz; no key edits."""
import bpy,json,math,numpy as np,sys,os
from pathlib import Path
from mathutils import Vector,Quaternion
P=Path(__file__).resolve().parents[1];W=P/'work/round3';R=P/'review/round3';bpy.ops.wm.open_mainfile(filepath=str(W/os.environ.get('ANATOMY_BLEND','rebaked_l0.blend')));rig=bpy.data.objects['Rig'];scene=bpy.context.scene;cal={}
for sd in 'LR':
 U,F,H=[rig.data.bones['B_'+sd+'_'+n]for n in ['UpperArm','Forearm','Hand']];u=(F.head_local-U.head_local).normalized();f=(H.head_local-F.head_local).normalized();forward=Vector((0,-1,0));forward=(forward-u*forward.dot(u)).normalized()
 cal[sd]={'hinge':U.matrix_local.to_3x3().inverted()@u.cross(forward).normalized(),'rel':U.matrix_local.to_3x3().inverted()@F.matrix_local.to_3x3(),'f':F.matrix_local.to_3x3().inverted()@f}
def flex(u,f,h):return math.degrees(math.atan2(h.dot(u.cross(f)),u.dot(f)))
u=Vector((0,1,0));h=Vector((1,0,0));assert abs(flex(u,Quaternion(h,math.radians(45))@u,h)-45)<.001;assert flex(u,Quaternion(h,math.radians(-20))@u,h)<-5
report={}
for act in bpy.data.actions:
 rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];rows={s:[]for s in 'LR'}
 for t in np.arange(0,float(act.frame_range[1])/scene.render.fps+.00001,1/48):
  f=t*scene.render.fps;scene.frame_set(int(f),subframe=float(f%1))
  for sd in 'LR':
   U,F,H=[rig.pose.bones['B_'+sd+'_'+n]for n in ['UpperArm','Forearm','Hand']];u=(F.head-U.head).normalized();v=(H.head-F.head).normalized();Ra=U.matrix.to_3x3();hinge=(Ra@cal[sd]['hinge']).normalized();bend=flex(u,v,hinge);off=math.degrees(math.asin(max(-1,min(1,v.dot(hinge)))));Rf=Ra@cal[sd]['rel'];Rf=(Rf@cal[sd]['f']).rotation_difference(v).to_matrix()@Rf;q=(F.matrix.to_3x3()@Rf.inverted()).to_quaternion();roll=(math.degrees(2*math.atan2(Vector((q.x,q.y,q.z)).dot(v),q.w))+180)%360-180;rows[sd].append([float(t),bend,roll,off])
 report[act.name]={}
 for sd,v in rows.items():
  v=np.array(v);bad=v[(v[:,1]<-5.001)|(abs(v[:,2])>90.001)|(abs(v[:,3])>5.001)];report[act.name][sd]={'samples':len(v),'flexion_deg':[float(v[:,1].min()),float(v[:,1].max())],'roll_deg':[float(v[:,2].min()),float(v[:,2].max())],'off_plane_deg_max':float(abs(v[:,3]).max()),'failed_samples':len(bad),'first_failures':bad[:5].tolist()}
result={'sample_hz':48,'clips':report,'absolute_pass':all(v['failed_samples']==0 for row in report.values()for v in row.values()),'scope':'Measure accepted motion. Final export must retain every original animation sample, node and inverse bind; no elbow, palm or finger animation correction is authorized in this round.'};(R/os.environ.get('ANATOMY_REPORT','anatomy.json')).write_text(json.dumps(result,indent=2));print('ANATOMY',result['absolute_pass'],{k:{s:(v['flexion_deg'],v['off_plane_deg_max'],v['failed_samples'])for s,v in row.items()}for k,row in report.items()},flush=True)
