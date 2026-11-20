from pathlib import Path
import sys,json,numpy as np
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p.parent/'claude_shared/gates'))
from run_gates import Glb,Mesh,Surface,Report,configure_mesh
cfg=json.loads((p/'gates.json').read_text());g=Glb(Path('/tmp/m520-focus-body.glb'));ni=g.names['Cyclops'];m=Mesh(g,g.nodes[ni]['mesh'],ni,'Cyclops/colour0');configure_mesh(m,cfg,Report(cfg))
name,surface,mask,containment=m.cloth[0];ids=np.flatnonzero(mask);rows=[]
for clip,t in [('Standing',0),('Attack',.25),('Dead',0)]:
 a=next(a for n,a,start,end in g.clips() if n==clip);pose=g.pose(a,np.array([t]))[0];co=m.posed(pose);surf=surface.build(co);signed,faces=surf.signed(co[ids],False)
 for j in np.argsort(signed)[:12]:
  vi=int(ids[j]);row={'clip':clip,'time':t,'index':vi,'rest':m.rest[vi].tolist(),'posed':co[vi].tolist(),'signed_mm':float(signed[j]*1000)};hit=surf.tree.find_nearest(__import__('mathutils').Vector(co[vi]));row['nearest_cap']=hit[2] in surf.caps;row['nearest_face']=hit[2];row['nearest_world']=list(hit[0]);rows.append(row);print(row,flush=True)
(p/'work/cloth_v7_points.json').write_text(json.dumps(rows,indent=2))
