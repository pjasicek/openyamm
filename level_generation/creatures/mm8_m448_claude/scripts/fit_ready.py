from pathlib import Path
import bpy,sys,math,json
from mathutils import Vector,Quaternion
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import armik
code=(p/'scripts/finalize_motion.py').read_text().split('stand=sample')[0].replace('work/motion_level.blend','work/rig_finished.blend')
exec(compile(code,str(p/'scripts/finalize_motion.py'),'exec'))
G=json.loads((p/'work/grip_pose.json').read_text());axis=Vector(G['handle_axis_hand_local'])
stand_original=sample(bpy.data.actions['Standing'],0)
# The native Ratman carries the sword diagonally upward, both hands forward of the torso.
previous=None;report={}
arm_names=[n for n in names if n.startswith(('B_R_','B_L_')) and any(k in n for k in ('Clavicle','UpperArm','Forearm','Hand','Finger'))]
for name in ('Standing','Walking','Running'):
 a=bpy.data.actions[name];poses=[sample(a,f) for f in range(int(a.frame_range[1])+1)];out=[];cost=[];previous=None
 for f,pose in enumerate(poses):
  apply(pose);pel=rig.pose.bones['B_Pelvis'].head;ch=rig.pose.bones['B_Spine2'].matrix.to_3x3()
  # Keep the gait's small hand swing, with a forward carrying centre.
  w=rig.pose.bones['B_R_Hand'].head;lw=rig.pose.bones['B_L_Hand'].head
  sway=.025*math.sin(2*math.pi*f/max(1,len(poses)-1)) if name!='Standing' else .005*math.sin(2*math.pi*f/max(1,len(poses)-1))
  z=pel.z+.18
  armik.solve(rig,'R',Vector((-.24,-.37+sway,z)))
  R,roll,sw,tw=armik.hand_for_axis(rig,'R',axis,Vector((-.12,-.57,.81)),prev_roll=previous,step=3,k_twist=.25,k_cont=.1)
  previous=roll;armik.set_world(rig,'B_R_Hand',armik.rot_world(armik.W(rig,'B_R_Hand'),R))
  armik.solve(rig,'L',Vector((.30,-.28-sway,pel.z+.12)))
  out.append({n:(rig.pose.bones[n].rotation_quaternion.copy(),rig.pose.bones[n].location.copy()) for n in names});cost.append([sw,tw])
 if name in ('Walking','Running'):out[-1]=out[0]
 write(name,out);report[name]={'wrist_cost_max':np.max(cost,axis=0).tolist()}
ready=sample(bpy.data.actions['Standing'],0)
# Preserve each one-shot's source motion; only its existing lead-in/recovery tends to the fitted guard.
for name,lead,tail in [('Attack',25,6),('Hit',3,4),('Fidget',8,8),('Death',6,0)]:
 a=bpy.data.actions[name];poses=[sample(a,f) for f in range(int(a.frame_range[1])+1)];out=[]
 for f,pose in enumerate(poses):
  w=max(1-smooth(f/max(1,lead)),1-smooth((len(poses)-1-f)/tail) if tail else 0)
  for n in arm_names:pose[n]=(pose[n][0].slerp(ready[n][0],w),pose[n][1])
  out.append(pose)
 write(name,out)
# Twist helper poses follow the newly fitted arms; existing weights remain untouched.
FA=.6;UA=.35
exec(compile('def twist_about'+(p/'scripts/twist_bones.py').read_text().split('def twist_about',1)[1].split('for act in [a for a in bpy.data.actions',1)[0],str(p/'scripts/twist_bones.py'),'exec'))
for a in [a for a in bpy.data.actions if a.use_fake_user]:bake_twist(a)
set_act(None)
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_ready.blend'))
(p/'work/ready_fit.json').write_text(json.dumps(report,indent=2));print('READY_FIT',report)
