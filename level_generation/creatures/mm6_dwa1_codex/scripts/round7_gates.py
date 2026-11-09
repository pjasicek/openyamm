"""Invoke the shared runner unchanged, filtering its clip inventory to the requested Running scope."""
import sys,json,time
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
sys.path.insert(0,str(P.parent/'claude_shared/gates'));import run_gates as g
original=g.Glb.clips
g.Glb.clips=lambda self:[c for c in original(self)if c[0]=='Running']
config=json.loads((P/'gates.json').read_text());g.validate_config(config)
for label,path in [('baseline',P/'work/round7_before/export/mm6_dwa1.glb'),('final',P/'export/mm6_dwa1.glb')]:
 out=P/'review/round7'/label;out.mkdir(exist_ok=True);r=g.Report(config);start=time.perf_counter()
 g.run(path,config,P,out,r);status=r.write(out,time.perf_counter()-start,None);print('SHARED',label,status,flush=True)

# Supplemental requested pelvis/head jitter measurement; the shared runner checks arm acceleration only.
import numpy as np,hashlib
asset=P/'export/mm6_dwa1.glb';glb=g.Glb(asset);clip,animation,start,end=glb.clips()[0];times=g.sample_grid(start,end,48);poses=glb.pose(animation,times);other=glb.pose(animation,start+(times-start+(end-start)/2)%(end-start));dt=np.diff(times);results={}
for name,acc_limit,sym_limit in [('B_Pelvis',4.,.0005),('B_Head',20.,.015)]:
 z=poses[:,glb.names[name],2,3];v=np.diff(z)/dt;acc=np.diff(v)/((dt[1:]+dt[:-1])/2);asym=max(abs(z-other[:,glb.names[name],2,3]))
 results[name]={'height_min_max_m':[float(z.min()),float(z.max())],'max_vertical_step_m':float(abs(np.diff(z)).max()),'max_vertical_acceleration_m_s2':float(abs(acc).max()),'half_cycle_height_difference_m':float(asym),'acceleration_limit_m_s2':acc_limit,'symmetry_limit_m':sym_limit,'pass':bool(abs(acc).max()<=acc_limit and asym<=sym_limit)}
(P/'review/round7/jitter.json').write_text(json.dumps({'runtime_sha256':hashlib.sha256(asset.read_bytes()).hexdigest(),'sample_hz':48,'limits_basis':'Analytic 12 mm two-step bob has 2.96 m/s2 peak acceleration; allow 4 pelvis and 20 head. Half-cycle symmetry tolerances 0.5 mm pelvis and 15 mm head.','bones':results,'pass':all(x['pass']for x in results.values())},indent=2))
print('PELVIS_HEAD_JITTER',results,flush=True)
