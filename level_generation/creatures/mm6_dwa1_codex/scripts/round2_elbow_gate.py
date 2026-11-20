"""Signed elbow flexion about the anatomical upper-arm hinge and axial forearm roll, both arms at 48 Hz."""
import bpy,sys,math,json,numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/export_reimport.blend'));tag='round2'
rig=bpy.data.objects['Rig'];scene=bpy.context.scene;cal={}
source=json.loads((p/'work/source_rest.json').read_text())
with bpy.data.libraries.load(str(p/'work/textured_master.blend'),link=False)as(src,dst):dst.objects=['Rig']
author=dst.objects[0]
for sd in 'LR':
 U,F,H=[rig.data.bones['B_'+sd+'_'+n] for n in ['UpperArm','Forearm','Hand']];u=(F.head_local-U.head_local).normalized();f=(H.head_local-F.head_local).normalized()
 # Source-frame hinge: the fitted A-pose's small elbow kink does not define its anatomical flexion plane.
 n=f'B_{sd}_UpperArm';su=Vector(source[n]['seg']).normalized();sh=su.cross(Vector((0,-1,0))).normalized()
 h=author.data.bones[n].matrix_local.to_3x3()@Matrix(source[n]['rot']).inverted()@sh
 cal[sd]={'hinge':U.matrix_local.to_3x3().inverted()@h,'rel':U.matrix_local.to_3x3().inverted()@F.matrix_local.to_3x3(),'f':F.matrix_local.to_3x3().inverted()@f}
bpy.data.objects.remove(author,do_unlink=True)
def flex(u,f,h):return math.degrees(math.atan2(h.dot(u.cross(f)),u.dot(f)))
# Sign regression: reversed hinge motion must fail, including a nearly straight arm.
u=Vector((0,1,0));h=Vector((1,0,0))
assert abs(flex(u,Quaternion(h,math.radians(45))@u,h)-45)<.001
assert flex(u,Quaternion(h,math.radians(-20))@u,h)<-5
report={}
for role in ['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget']:
 rig.animation_data.action=None
 for pb in rig.pose.bones:pb.matrix_basis.identity()
 act=bpy.data.actions[role];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];rows={s:[] for s in 'LR'}
 for t in np.arange(0,float(act.frame_range[1])/scene.render.fps+1e-6,1/48):
  f=t*scene.render.fps;scene.frame_set(int(f),subframe=float(f%1))
  for sd in 'LR':
   U,F,H=[rig.pose.bones['B_'+sd+'_'+n] for n in ['UpperArm','Forearm','Hand']];u=(F.head-U.head).normalized();v=(H.head-F.head).normalized();Ra=U.matrix.to_3x3();hinge=(Ra@cal[sd]['hinge']).normalized();b=flex(u,v,hinge);off=math.degrees(math.asin(max(-1,min(1,v.dot(hinge)))))
   Rf=Ra@cal[sd]['rel'];Rf=(Rf@cal[sd]['f']).rotation_difference(v).to_matrix()@Rf;q=(F.matrix.to_3x3()@Rf.inverted()).to_quaternion();roll=(math.degrees(2*math.atan2(Vector((q.x,q.y,q.z)).dot(v),q.w))+180)%360-180
   rows[sd].append([float(t),b,roll,off])
 report[role]={}
 for sd,a in rows.items():
  a=np.array(a);bad=a[(a[:,1]<-5.001)|(a[:,1]>150.001)|(np.abs(a[:,2])>90.001)|(np.abs(a[:,3])>5.0)]
  report[role][sd]={'samples':len(a),'sample_hz':48,'flexion_deg':[float(a[:,1].min()),float(a[:,1].max())],'forearm_roll_deg':[float(a[:,2].min()),float(a[:,2].max())],'out_of_plane_max_deg':float(abs(a[:,3]).max()),'failed_samples':len(bad),'first_failures':bad[:5].tolist(),'pass':len(bad)==0}
 print('ELBOW',role,json.dumps(report[role]),flush=True)
(p/'review/round2/elbow_gate.json').write_text(json.dumps({'limits':{'flexion_deg':[-5,150],'forearm_roll_deg':[-90,90],'out_of_plane_deg':5},'signed_angle_selftest':'pass','clips':report,'pass':all(x['pass'] for a in report.values() for x in a.values())},indent=2))
assert all(x['pass'] for a in report.values() for x in a.values()),'Anatomical elbow gate failed'
