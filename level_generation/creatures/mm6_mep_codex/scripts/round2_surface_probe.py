import sys,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'claude_shared/gates'));from run_gates import Glb,load_meshes,Surface,penetration
G=Glb(P/'export/mm6_mep.glb');cfg=json.loads((P/'gates.json').read_text())['cloth'][-1];rows=[]
for mesh in load_meshes(G)[:4]:
 for name,spec in [('waist',cfg['surface'])]:
  try:surface=Surface(mesh,mesh.select(spec),cap=True,opening=cfg['opening'])
  except ValueError as e:rows.append({'lod':mesh.label,'selection':name,'setup_error':str(e)});continue
  samples=mesh.select(cfg['samples']);ids=np.flatnonzero(samples)
  for role,time in [('Standing',.5208333333333334),('Standing',1.2916666666666665),('Walking',.5208333333333334),('Death',2.583333333333333),('Fidget',2.625)]:
   anim=next(a for a in G.doc['animations'] if a['name']==role);pose=G.pose(anim,np.array([time]))[0];pts=mesh.posed(pose);surface.build(pts,pose);depth,i=penetration(surface,pts[samples],containment=cfg['containment']);i=0 if i is None else i;v=pts[ids[i]];near,n,f,dist=surface.tree.find_nearest(v)
   rows.append({'lod':mesh.label,'selection':name,'clip':role,'time':time,'depth':float(depth),'rest_point':mesh.rest[ids[i]].tolist(),'posed_point':v.tolist(),'normal':list(n),'nearest':list(near),'face':f,'is_cap':f in surface.caps,'cap_count':len(surface.caps)})
(P/'review/round2/surface_probe.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
