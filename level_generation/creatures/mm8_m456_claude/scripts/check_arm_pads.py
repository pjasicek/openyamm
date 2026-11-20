"""Check the delivered motion, shoulder hinge attachment and retained sword path at 120 Hz."""
from pathlib import Path
import sys,json,numpy as np
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parent/'claude_shared/gates'))
from run_gates import Glb,sample_grid
from scipy.spatial.transform import Rotation
a=Glb(P/'review/arm_pad_repair/before/mm8_m456.glb');g=Glb(P/'export/mm8_m456.glb')
report={'before_sha256':a.sha256,'after_sha256':g.sha256,'clips':{}}
for name,c,start,end in g.clips():
 times=sample_grid(start,end,120);poses=g.pose(c,times)
 old=a.pose(next(c for n,c,s,e in a.clips() if n==name),times)
 chest=g.names['B_Spine2'];D=poses[:,chest]@np.linalg.inv(g.rest[chest]);row={}
 for sd,sg in [('L',1),('R',-1)]:
  index=g.names[f'B_{sd}_Pauldron'];pad=poses[:,index]@np.linalg.inv(g.rest[index]);pivot=np.array([sg*.135,-.005,1.34,1])
  drift=float(np.linalg.norm((pad@pivot)[:,:3]-(D@pivot)[:,:3],axis=1).max()*1000)
  assert drift<.1,(name,sd,'pauldron hinge detached',drift)
  row[sd+'_pad_hinge_drift_mm']=drift
  if name in ['Standing','Walking','Running']:
   index=g.names[f'B_{sd}_UpperArm'];expected=(D@g.rest[index])[:,:3,3]
   drift=float(np.linalg.norm(poses[:,index,:3,3]-expected,axis=1).max()*1000)
   assert drift<30,(name,sd,'shoulder outside socket',drift)
   row[sd+'_shoulder_drift_mm']=drift
 # Death is re-grounded after changing the free arm, so compare the sword relative to the pelvis.
 current=poses[:,g.names['B_L_Hand'],:3,3].copy();prior=old[:,a.names['B_L_Hand'],:3,3].copy()
 if name=='Death':
  current-=poses[:,g.names['B_Pelvis'],:3,3];prior-=old[:,a.names['B_Pelvis'],:3,3]
 delta=float(np.linalg.norm(current-prior,axis=1).max()*1000)
 assert delta<.1,(name,'sword hand moved',delta)
 row['left_hand_path_error_mm']=delta
 new_rot=poses[:,g.names['Sword'],:3,:3];old_rot=old[:,a.names['Sword'],:3,:3]
 error=float(np.abs(new_rot-old_rot).max())
 assert error<1e-4,(name,'sword orientation changed',error)
 row['sword_rotation_matrix_error']=error
 if name=='Attack':
  rest= np.linalg.inv(D)
  hand=(rest@poses[:,g.names['B_R_Hand']])[:,:3,3]
  elbow=(rest@poses[:,g.names['B_R_Forearm']])[:,:3,3]
  assert elbow[:,0].max()<-.21,('free elbow enters torso',elbow[:,0].max())
  assert hand[:,1].max()<0,('free hand swings behind torso',hand[:,1].max())
  step=float(np.linalg.norm(np.diff(hand,axis=0),axis=1).max()*1000)
  assert step<10,('free hand jumps',step)
  row['right_hand_max_step_mm_at_120_hz']=step
 if name in ['Attack','Hit','Fidget','Death']:
  t48=sample_grid(start,end,48);p48=g.pose(c,t48);dt=np.diff(t48)
  for bone in ['B_R_UpperArm','B_R_Forearm','B_R_Hand']:
   rotations=p48[:,g.names[bone],:3,:3]
   velocity=Rotation.from_matrix(rotations[1:]@rotations[:-1].transpose(0,2,1)).as_rotvec()/dt[:,None]
   acceleration=np.linalg.norm(np.diff(velocity,axis=0),axis=1)/((dt[1:]+dt[:-1])/2)*180/np.pi
   assert acceleration.max()<20000,(name,bone,'abrupt fitted arm transition',acceleration.max())
   row[bone+'_acceleration_deg_s2']=float(acceleration.max())
 if name=='Attack':
  idle=next(c for n,c,s,e in g.clips() if n=='Standing')
  error=float(np.abs(poses[[0,-1]]-g.pose(idle,np.array([0]))).max())
  assert error<1e-4,('attack guard discontinuity',error)
  row['guard_endpoint_matrix_error']=error
 report['clips'][name]=row
(P/'review/arm_pad_repair/motion_check.json').write_text(json.dumps(report,indent=2)+'\n')
print('ARM_PAD_PASS',json.dumps(report['clips'],indent=2))
