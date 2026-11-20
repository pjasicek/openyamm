"""Height diagnostics from the shared runtime evaluator; no new pass/fail gate implementation."""
import sys,json
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P.parent/'claude_shared/gates'))
from run_gates import Glb,sample_grid,Report,load_props,bone_gates
config=json.loads((P/'gates.json').read_text());g=Glb(P/'export/mm6_lzd.glb');report=Report(config)
props=load_props(config,P,g,report);a=next(a for n,a,start,end in g.clips()if n=='Walking');times=sample_grid(0,.8,48);pose=g.pose(a,times)
bone_gates(g,pose,times,'Walking',config,report,props)
print('BONE_FAILURES', [r for r in report.rows.values() if r['status'] in ['FAIL','UNVERIFIED']])
result={'runtime_sha256':g.sha256,'sample_hz':48,'shared_runner_limitation':'Runner has arm angular jitter gates but no pelvis/spine/head translation jitter gate. The height traces below are diagnostics, not a new custom gate.','versions':{}}
poses={}
for label,path in [('before',P/'review/round6/baseline/export/mm6_lzd.glb'),('after',P/'export/mm6_lzd.glb')]:
 obj=Glb(path);clip=next(a for n,a,start,end in obj.clips()if n=='Walking');m=obj.pose(clip,times);poses[label]=(obj,m);summary={}
 for name in ['B_Pelvis','B_Spine','B_Spine2','B_Head']:
  z=m[:,obj.names[name],2,3];dt=np.diff(times);v=np.diff(z)/dt;acc=np.diff(v)/((dt[1:]+dt[:-1])/2)
  summary[name]={'height_range_m':[float(z.min()),float(z.max())],'peak_abs_velocity_m_s':float(max(abs(v))),'peak_abs_acceleration_m_s2':float(max(abs(acc))),'samples':[{'time_s':float(t),'height_m':float(h)}for t,h in zip(times,z)],'velocity_m_s':v.tolist(),'acceleration_m_s2':acc.tolist()}
 result['versions'][label]=summary
before,bm=poses['before'];after,am=poses['after']
result['foot_path_max_difference_m']={s:float(np.linalg.norm(bm[:,before.names[f'B_{s}_Foot'],:3,3]-am[:,after.names[f'B_{s}_Foot'],:3,3],axis=1).max())for s in 'LR'}
result['loop_endpoint_max_matrix_difference']=float(abs(am[0]-am[-1]).max())
result['shoulder_pitch_amplitude_deg']=25
(P/'review/round6/motion_diagnostics.json').write_text(json.dumps(result,indent=2))
print({k:{n:{x:v for x,v in z.items()if x not in ['samples','velocity_m_s','acceleration_m_s2']}for n,z in d.items()}for k,d in result['versions'].items()})
