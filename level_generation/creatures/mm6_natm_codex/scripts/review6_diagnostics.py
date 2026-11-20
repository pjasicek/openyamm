"""Revision evidence from the shared pose evaluator; does not implement replacement acceptance gates."""
import sys,json,hashlib,numpy as np
from pathlib import Path
from scipy.spatial.transform import Rotation
P=Path(__file__).resolve().parents[1];B=P/'work/review_round6_before';sys.path.insert(0,str(P.parent/'claude_shared/gates'));import run_gates as S
sys.path.insert(0,str(P.parents[2]/'tools'));from merge_head_material import read_glb
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old,ob=read_glb(B/'export/mm6_natm.glb');new,nb=read_glb(P/'export/mm6_natm.glb')
assert bytes(nb[:len(ob)])==bytes(ob)
for k in ['meshes','skins','nodes','materials','images','textures']:assert old[k]==new[k],k
assert [a for a in old['animations']if a['name']!='Attack']==[a for a in new['animations']if a['name']!='Attack']
for n in ['mm6_natm_spear.glb','mm6_natm_buckler.glb']:assert (P/'export'/n).read_bytes()==(B/'export'/n).read_bytes()
assert (P/'integration/actors.yml').read_text()==(B/'integration/actors.yml').read_text().replace('0.906250000','0.739583333')
out={'classification':__doc__,'source_sha256':sha(P/'export/mm6_natm.glb'),'old_duration_s':57/48,'new_duration_s':55/48,'recovery_frames':[43,55],'recovery_duration_s':12/48,'old_impact_s':43.5/48,'new_impact_s':35.5/48,'metrics':{}}
poses=[]
for label,file,count in [('round5',B/'export/mm6_natm.glb',58),('round6',P/'export/mm6_natm.glb',56)]:
 g=S.Glb(file);ps=g.pose(next(a for a in g.doc['animations']if a['name']=='Attack'),np.arange(count)/48);poses.append(ps);row={}
 for n in ['B_Pelvis','B_Spine','B_Spine1','B_Spine2','B_L_UpperArm','B_L_Forearm','B_L_Hand','B_R_UpperArm','B_R_Forearm','B_R_Hand','Socket_SpearTip']:
  m=ps[:,g.names[n]];v=np.diff(m[:,:3,3],axis=0)*48;acc=np.linalg.norm(np.diff(v,axis=0)*48,axis=1);av=Rotation.from_matrix(m[1:,:3,:3]@m[:-1,:3,:3].transpose(0,2,1)).as_rotvec()*48*180/np.pi;aa=np.linalg.norm(np.diff(av,axis=0)*48,axis=1)
  row[n]={'linear_velocity_m_s':np.linalg.norm(v,axis=1).tolist(),'linear_acceleration_m_s2':acc.tolist(),'angular_velocity_deg_s':np.linalg.norm(av,axis=1).tolist(),'angular_acceleration_deg_s2':aa.tolist(),'drive_max_linear_acceleration_m_s2':float(acc[31:42 if label=='round6'else 45].max()),'drive_max_angular_acceleration_deg_s2':float(aa[31:42 if label=='round6'else 45].max())}
 out['metrics'][label]=row
pre=float(abs(poses[0][:33]-poses[1][:33]).max());recovery=float(abs(poses[0][45:]-poses[1][43:]).max());assert pre<2e-6 and recovery<2e-6,(pre,recovery)
movement=np.linalg.norm(np.diff(poses[1][:,:,:3,3],axis=0),axis=2).max(axis=1)
out['hold_check']={'frame_intervals':list(range(32,55)),'maximum_joint_displacement_per_interval_m':movement[32:].tolist(),'static_intervals_after_frame32':np.flatnonzero(movement[32:]<1e-5).tolist()};assert not out['hold_check']['static_intervals_after_frame32']
out['invariants']={'binary_prefix_identical':True,'other_eight_clips_identical':True,'geometry_skin_material_images_identical':True,'both_props_byte_identical':True,'before_frame33_max_matrix_difference':pre,'entire_recovery_max_matrix_difference':recovery,'bindings_only_six_attack_event_values_changed':True}
(P/'review/round6_motion_diagnostic.json').write_text(json.dumps(out,indent=2)+'\n');print('DIAGNOSTIC',out['invariants'],out['hold_check'])
