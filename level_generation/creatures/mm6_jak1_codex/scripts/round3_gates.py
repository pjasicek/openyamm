"""Shared final-GLB gates, with every mesh sampled at 48 Hz (stricter than its adaptive 24 Hz default)."""
import sys,json
from pathlib import Path
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'claude_shared/gates'));import run_gates as shared
original_grid=shared.sample_grid
shared.sample_grid=lambda start,end,hz:original_grid(start,end,max(hz,48))
assert len(shared.sample_grid(0,1,24))==49
sys.argv=['gates','--',str(P/'export/mm6_jak1.glb'),'--config',str(P/'gates.json'),'--out',str(P/'review/round3/shared_gates')]
shared.main()
file=P/'review/round3/shared_gates/gates.json';result=json.loads(file.read_text());result['sampling_override']='Project wrapper raises every sample_grid request to at least 48 Hz; no thresholds or measured geometry altered.'
for row in result['sampling']:row['mesh_base_hz']=48
file.write_text(json.dumps(result,indent=2))
