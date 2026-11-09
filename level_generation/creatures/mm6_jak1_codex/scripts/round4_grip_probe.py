import sys,json,numpy as np
from pathlib import Path
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'claude_shared/gates'));import run_gates as G
config=json.loads((P/'gates.json').read_text());report=G.Report(config);body=G.Glb(P/'export/mm6_jak1.glb')
old=G.Glb(P/'review/round4/before/export/mm6_jak1_staff.glb');new=G.Glb(P/'export/mm6_jak1_staff.glb')
surfaces={}
for key,glb in [('old',old),('new',new)]:
 surfaces[key]=[G.Surface(m,np.ones(len(m.rest),bool)).build(m.rest)for m in G.load_meshes(glb)]
clip,animation,lo,hi=next(c for c in body.clips()if c[0]=='Attack');times=G.sample_grid(lo,hi,48);poses=body.pose(animation,times);rows=[];arrays={}
for level,mesh in enumerate([m for m in G.load_meshes(body)if '/colour'in m.label]):
 G.configure_mesh(mesh,config,report)
 for side in ['L','R']:
  tri,bary,groups,signature=G.grip_points(mesh,side,config);all_local=[]
  for t,pose in zip(times,poses):
   if side=='L'and not(.6304761433488056<=t<=1.5836276337245487):continue
   points=mesh.posed(pose);matrix=pose[body.names['Staff']]
   world=np.einsum('sk,tkj->tsj',bary,points[tri]).reshape(-1,3)
   local=G.transform(G.C@np.linalg.inv(matrix),world);all_local.append(local)
  local=np.concatenate(all_local);arrays[f'lod{level}_{side}']=local
  for key in surfaces:
   dist,_=surfaces[key][level].signed(local);i=np.argmin(dist)
   rows.append({'lod':level,'side':side,'surface':key,'depth_mm':max(0,-float(dist[i]))*1000,'worst_point_Zup':local[i].tolist(),'radius_mm':float(np.linalg.norm(local[i,[0,2]]))*1000,'axial_z_raw':-float(local[i,1])})
np.savez_compressed(P/'work/round4/grip_samples.npz',**arrays)
(P/'review/round4/grip_probe.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2),flush=True)
