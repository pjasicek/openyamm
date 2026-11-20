"""Plant the fitted loop against the shipped LOD soles, using the shared mesh evaluator."""
import sys,json,math
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
sys.path.insert(0,str(P.parent/'claude_shared/gates'));import run_gates as g
W=P/'work/round5';source=json.loads((W/'running_world.json').read_text());config=json.loads((P/'gates.json').read_text())
glb=g.Glb(P/'export/mm6_figc.glb');meshes=[m for m in g.load_meshes(glb)if '/colour' in m.label];report=g.Report(config)
for m in meshes:g.configure_mesh(m,config,report)
fit=json.loads((P/'review/round5/motion_fit.json').read_text());offsets=[]
for i,pose in enumerate(source['poses']):
 matrices=glb.rest.copy()
 for n,M in pose.items():matrices[glb.names[n]]=np.array(M)
 lows=[]
 for m in meshes:
  points=m.posed(matrices);lows.append(min(points[ids,2].min()for ids,heel,toe in m.feet.values()))
 lifts=[]
 for side in [0,.5]:
  phase=(i/96+fit['phase_offset']+side)%1
  lifts.append(0 if phase<.47 else .14*math.sin(math.pi*(phase-.47)/.53)**1.25)
 dz=config['floor_m']-.00128+min(lifts)*.35-min(lows);offsets.append(dz)
 for M in pose.values():M[2][3]+=dz
source['poses'][-1]=source['poses'][0]
(W/'running_world.json').write_text(json.dumps(source))
(P/'review/round5/sole_fit.json').write_text(json.dumps({'method':'Shared Glb/Mesh evaluator; root correction against lowest shipped colour-LOD sole, retaining planned brief flight','ground_fit_m':-.00128,'flight_root_gain':.35,'root_z_corrections_m':offsets},indent=2))
print('SOLE FIT',min(offsets),max(offsets))
