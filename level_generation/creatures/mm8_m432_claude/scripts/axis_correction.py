import bpy,sys,json,math,os,runpy
from pathlib import Path
from mathutils import Vector,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import armik
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_axis_base.blend'));r=bpy.data.objects['Rig'];ac=bpy.data.actions['Attack'];sc=bpy.context.scene
G=json.loads((P/'work/grip_pose.json').read_text());C=Vector(G['handle_centre_hand_local']);A=Vector(G['handle_axis_hand_local'])
def smooth(t):t=max(0,min(1,t));return t*t*(3-2*t)
poses=[]
for f in range(int(ac.frame_range[1])+1):
 r.animation_data.action=ac;r.animation_data.action_slot=ac.slots[0];sc.frame_set(f);p={b.name:b.matrix_basis.copy() for b in r.pose.bones};h=r.pose.bones['B_R_Hand'].matrix.copy();axis=(h.translation-r.pose.bones['B_R_Forearm'].head).normalized();centre=(r.pose.bones['B_R_UpperArm'].head+r.pose.bones['B_L_UpperArm'].head)*.5;rc=h@C;r.animation_data.action=None
 for n,m in p.items():r.pose.bones[n].matrix_basis=m
 bpy.context.view_layer.update();w=smooth((f-14)/5)*(1-smooth((f-23)/9));rot=Quaternion(axis,math.radians(35*w)).to_matrix()@h.to_3x3().normalized();rc+=(centre-rc).normalized()*(.035*w)
 armik.solve(r,'R',rc-rot@C,hand_rot=rot)
 poses.append({f'B_R_{n}':r.pose.bones[f'B_R_{n}'].rotation_quaternion.copy() for n in ('UpperArm','Forearm','Hand')})
r.animation_data.action=ac;r.animation_data.action_slot=ac.slots[0];prev={}
for f,p in enumerate(poses):
 for n,q in p.items():
  if n in prev and q.dot(prev[n])<0:q=-q
  prev[n]=q;r.pose.bones[n].rotation_quaternion=q;r.pose.bones[n].keyframe_insert('rotation_quaternion',frame=f)
r.animation_data.action=None;bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_axis_corrected.blend'))
os.environ['ARM_INPUT']='work/rig_axis_corrected.blend';os.environ['ARM_OUTPUT']='work/rig_axis_fitted.blend';os.environ['ARM_CLIPS']='Attack';os.environ['ARM_SIDES']='L';os.environ['ARM_PHI']='170'
runpy.run_path(str(P/'scripts/smooth_arm_fit.py'),run_name='__main__')
os.environ['BAKE_ONLY']='1';os.environ['FA']='0.6';os.environ['FA_RAMP']='0.15,0.85'
sys.argv=['twist_bones.py','--',str(P/'work/rig_axis_fitted.blend'),str(P/'work/rig_final_motion.blend')]
runpy.run_path(str(P/'scripts/twist_bones.py'),run_name='__main__');runpy.run_path(str(P/'scripts/assemble.py'),run_name='__main__');runpy.run_path(str(P/'scripts/gates.py'),run_name='__main__')
print('SOURCE JERK COMPARISON',flush=True)
sys.argv=['jerk_probe.py','--',str(P/'work/rig_fingers.blend'),'Attack','Cast','Death'];runpy.run_path(str(P/'scripts/jerk_probe.py'),run_name='__main__')
