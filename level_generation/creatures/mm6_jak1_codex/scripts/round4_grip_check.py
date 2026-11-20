import sys,json,numpy as np
from pathlib import Path
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'claude_shared/gates'));import run_gates as G
config=json.loads((P/'gates.json').read_text());report=G.Report(config);body=G.Glb(P/'export/mm6_jak1.glb');props=G.load_props(config,P,body,report);prop=props[0];rows=[]
for level,mesh in enumerate([m for m in G.load_meshes(body)if '/colour'in m.label]):
 G.configure_mesh(mesh,config,report)
 specs={s:G.grip_points(mesh,s,config)for s in ['L','R']}
 for name,animation,lo,hi in body.clips():
  times=G.sample_grid(lo,hi,48);poses=body.pose(animation,times)
  for hand in prop['hands']:
   side=hand['side'];tri,bary,groups,_=specs[side];gap=np.zeros(6);depth=0.;samples=0
   for t,pose in zip(times,poses):
    if not G.held_samples(prop,hand,name,t):continue
    points=mesh.posed(pose);world=np.einsum('sk,tkj->tsj',bary,points[tri]).reshape(-1,3);matrix=pose[body.names['Staff']];local=G.transform(G.C@np.linalg.inv(matrix),world)
    surface=prop['grip_surfaces'][side][level]
    gap=np.maximum(gap,[surface.gap(local[mask])*1000 for mask in groups])
    dist,_=prop['solid_surfaces'][level].signed(local);depth=max(depth,max(0,-float(dist.min()))*1000);samples+=1
   if samples:rows.append({'lod':level,'clip':name,'side':side,'max_gap_mm':float(gap.max()),'gaps_mm':gap.tolist(),'depth_mm':depth,'pass':bool(gap.max()<=3 and depth<=3)})
(P/'review/round4/grip_check.json').write_text(json.dumps(rows,indent=2));print(json.dumps([r for r in rows if not r['pass']],indent=2),flush=True);print('GRIP',sum(r['pass']for r in rows),'/',len(rows),flush=True)
