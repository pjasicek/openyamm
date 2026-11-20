"""Final-pose authoring evidence; this does not replace missing shared acceptance gates."""
import sys,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'claude_shared/gates'));import run_gates as S
new=S.Glb(P/'export/mm6_natm.glb');old=S.Glb(P/'work/review_round3_before/export/mm6_natm.glb');out={'classification':'Authoring diagnostics, not shared-gate PASS','source_sha256':new.sha256,'head':{},'retime':{}}
for role,a,lo,hi in new.clips():
 if role in ['Attack','Cast','Fidget']:
  times=np.linspace(lo,hi,round((hi-lo)*48)+1);poses=new.pose(a,times);i=new.names['B_Head'];axis=np.linalg.inv(new.rest[i,:3,:3])@np.array([0,-1,0]);v=np.einsum('nij,j->ni',poses[:,i,:3,:3],axis);v/=np.linalg.norm(v,axis=1)[:,None];out['head'][role]={'max_forward_angle_deg':float(np.degrees(np.arccos(np.clip(-v[:,1],-1,1))).max()),'max_yaw_deg':float(abs(np.degrees(np.arctan2(v[:,0],-v[:,1]))).max()),'max_pitch_deg':float(abs(np.degrees(np.arcsin(v[:,2]))).max())}
 if role in ['Death','Dead']:
  oa,ol,oh=next((aa,ll,hh)for rr,aa,ll,hh in old.clips()if rr==role);nn=new.pose(a,np.array([hi]))[0];oo=old.pose(oa,np.array([oh]))[0];names=sorted(set(new.names)&set(old.names));out['retime'][role]={'old_duration_s':float(oh-ol),'new_duration_s':float(hi-lo),'maximum_endpoint_matrix_delta':float(max(abs(nn[new.names[n]]-oo[old.names[n]]).max()for n in names))}
(P/'review/round3_final_diagnostics.json').write_text(json.dumps(out,indent=2));print('FINAL_DIAGNOSTICS',out,flush=True)
