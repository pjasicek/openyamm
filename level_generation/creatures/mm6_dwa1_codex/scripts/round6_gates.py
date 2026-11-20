"""Invoke the shared runner unchanged, filtering its clip inventory to the requested Running scope."""
import sys,json,time
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
sys.path.insert(0,str(P.parent/'claude_shared/gates'));import run_gates as g
original=g.Glb.clips
g.Glb.clips=lambda self:[c for c in original(self)if c[0]=='Running']
config=json.loads((P/'gates.json').read_text());g.validate_config(config)
for label,path in [('baseline',P/'work/round6_before/export/mm6_dwa1.glb'),('final',P/'export/mm6_dwa1.glb')]:
 out=P/'review/round6'/label;out.mkdir(exist_ok=True);r=g.Report(config);start=time.perf_counter()
 g.run(path,config,P,out,r);status=r.write(out,time.perf_counter()-start,None);print('SHARED',label,status,flush=True)
