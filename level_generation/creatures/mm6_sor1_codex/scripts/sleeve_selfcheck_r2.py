import bpy,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));from sleeve_fit_r2 import Sleeve
bpy.ops.wm.open_mainfile(filepath=str(p/'work/round2_motion.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];rig.animation_data.action=bpy.data.actions['Attack'];rig.animation_data.action_slot=rig.animation_data.action.slots[0]
G=json.loads((p/'work/grip_pose.json').read_text());out={}
for f in [60,85,120]:
 bpy.context.scene.frame_set(f);s='B_R_';sh=Sleeve(rig,body,s);r={};refs={}
 for part,key,pos in [('UpperArm','Ra','S'),('Forearm','Rf','E'),('Hand','Rh','W')]:r[key]=rig.pose.bones[s+part].matrix.to_3x3();r[pos]=rig.pose.bones[s+part].head
 for n,child,fac in [('Forearm','Hand',2),('UpperArm','Forearm',-2)]:
  b=rig.data.bones[s+n];axis=(b.matrix_local.inverted()@rig.data.bones[s+child].head_local).normalized();q=rig.pose.bones[s+n+'Twist'].rotation_quaternion;refs[s+n+'Twist']=fac*2*math.atan2(Vector((q.x,q.y,q.z)).dot(axis),q.w)
 H=rig.pose.bones[s+'Hand'].matrix;C=H@Vector(G['handle_centre_hand_local']);A=H.to_3x3()@Vector(G['handle_axis_hand_local']);sh.begin();cost=sh.cost(r,C,A,refs)
 ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();co=np.array([m.vertices[i].co[:] for i in sh.chosen]);ev.to_mesh_clear();err=np.linalg.norm(co-sh.last_co,axis=1)
 out[f]={'predicted_contact_mm':cost*1000,'skin_error_mm':float(err.max()*1000),'bone_matrix_error':{n:float(np.max(abs(np.array(M)-np.array(rig.pose.bones[n].matrix)))) for n,M in sh.last_m.items()}}
print('SLEEVE_SELFTEST',json.dumps(out),flush=True)
(p/'work/round2_sleeve_selftest.json').write_text(json.dumps(out,indent=2))
assert all(r['skin_error_mm']<.01 for r in out.values())
