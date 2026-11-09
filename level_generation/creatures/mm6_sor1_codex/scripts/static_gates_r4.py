"""Thin entry point to the shared runner's static checks; no creature-specific gate implementation."""
from pathlib import Path
import sys,json,time
sys.dont_write_bytecode=True
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p.parent/'claude_shared/gates'))
from run_gates import Glb,Report,static_gates
out=p/'review/round4/shared_gates';out.mkdir(exist_ok=True);config=json.loads((p/'review/round4/static_config.json').read_text());report=Report(config);start=time.perf_counter()
for asset,file in [('body','mm6_sor1.glb'),('staff','mm6_sor1_staff.glb')]:static_gates(Glb(p/'export'/file),report,asset)
status=report.write(out,time.perf_counter()-start);assert status=='PASS',status;print('SHARED STATIC GATES',status,flush=True)
