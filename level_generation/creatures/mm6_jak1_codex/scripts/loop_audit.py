"""Validate end-to-start arm acceleration on the actual exported looping clips."""
import sys,numpy as np,json
from scipy.spatial.transform import Rotation
from pathlib import Path
sys.dont_write_bytecode=True;P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'claude_shared/gates'));import run_gates as s
g=s.Glb(P/'export/mm6_jak1.glb');out={}
for clip,a,lo,hi in g.clips():
 if clip not in ['Standing','Walking']:continue
 times=np.arange(-4,5)/48;poses=g.pose(a,np.mod(times,hi));rows={}
 for name in [f'B_{side}_{part}'for side in 'LR'for part in ['UpperArm','Forearm','Hand']]:
  r=Rotation.from_matrix(poses[:,g.names[name],:3,:3]);delta=(r[1:]*r[:-1].inv()).as_rotvec()*180/np.pi;rows[name]=float(np.linalg.norm(np.diff(delta*48,axis=0)*48,axis=1).max())
 out[clip]=rows
(P/'review/round2/loop_acceleration.json').write_text(json.dumps(out,indent=2));print(out);assert max(v for row in out.values()for v in row.values())<=20000
