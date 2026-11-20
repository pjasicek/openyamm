from pathlib import Path
import sys,json,numpy as np
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p.parent/'claude_shared/gates'))
from run_gates import Glb,Mesh,Surface
mfile=p/'export/mm8_m520.glb';glb=Glb(mfile);ni=glb.names['Cyclops'];mesh=Mesh(glb,glb.nodes[ni]['mesh'],ni,'Cyclops/colour0');cfg=json.loads((p/'gates.json').read_text());mask=mesh.select(cfg['regions']['loincloth']);surface=Surface(mesh,mask,cap=True,opening={'axis':[0,0,-1]}).build(mesh.rest)
print('CLOTH_TOPOLOGY',surface.closed,'loops',[len(v) for v in surface.loops],'opening',surface.opening,'plane',surface.plane,flush=True)
points=np.array([[0,0,1.25],[-.0363824,.2028777,1.2012334],[0,.25,1.2],[0,-.20,1.2],[0,0,1.35],[.17,0,1.3]])
print('CLOTH_POINTS',points.tolist(),'inside',surface.exact_inside(points,(.811107,.357913,.463187)).tolist(),'signed',surface.signed(points,containment=True)[0].tolist(),flush=True)
