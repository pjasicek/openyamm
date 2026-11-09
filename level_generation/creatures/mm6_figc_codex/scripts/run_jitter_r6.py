"""Reuse shared angular jitter gates for torso bones; record positional derivatives as diagnostics."""
import sys,json,copy,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P.parent/'claude_shared/gates'));import run_gates as g
config=json.loads((P/'gates.json').read_text());names=['B_Pelvis','B_Spine','B_Spine1','B_Spine2','B_Neck','B_Head'];aliases=dict(zip([f'B_{s}_{n}'for s in 'LR'for n in ['UpperArm','Forearm','Hand']],names));result={}
for revision,file in [('before',P/'review/round6/before/export/mm6_figc.glb'),('after',P/'export/mm6_figc.glb')]:
 gb=g.Glb(file);clip=next(a for a in gb.doc['animations']if a['name']=='Running');duration=max(float(gb.accessor(s['input']).max()) for s in clip['samplers']);times=g.sample_grid(0,duration,48);pose=gb.pose(clip,times);cfg=copy.deepcopy(config);cfg['bones']=aliases;report=g.Report(cfg)
 g.bone_gates(gb,pose,times,'Running',cfg,report,[])
 rows=[r for r in report.rows.values()if r['gate']in ['rotation_step_deg','angular_acceleration_deg_s2'] and r['region']in aliases]
 for r in rows:r['region']=aliases[r['region']]
 result[revision]={'sha256':gb.sha256,'shared_angular_jitter':rows,'vertical':{}}
 for n in names:
  z=pose[:,gb.names[n],2,3];dt=np.diff(times);v=np.diff(z)/dt;acc=np.diff(v)/((dt[1:]+dt[:-1])/2)
  result[revision]['vertical'][n]={'times_s':times.tolist(),'height_m':z.tolist(),'velocity_m_s':v.tolist(),'acceleration_m_s2':acc.tolist(),'max_abs_velocity_m_s':float(abs(v).max()),'max_abs_acceleration_m_s2':float(abs(acc).max()),'frame7_to8_delta_mm':float((z[8]-z[7])*1000),'endpoint_delta_mm':float((z[-1]-z[0])*1000)}
result['note']='Angular measurements invoke unmodified shared bone_gates with bone aliases, retaining only its jitter rows. The current shared runner has no positional-velocity/acceleration gate; vertical series are diagnostic measurements, not a claimed shared positional gate.'
(P/'review/round6/running_jitter.json').write_text(json.dumps(result,indent=2))
for rev in ['before','after']:
 print(rev,{n:{k:v for k,v in result[rev]['vertical'][n].items()if k.startswith('max_')or k.startswith('frame7')}for n in ['B_Pelvis','B_Head']})
print('SHARED_TORSO_JITTER',[(r['region'],r['gate'],r['worst'],r['status'])for r in result['after']['shared_angular_jitter']])
