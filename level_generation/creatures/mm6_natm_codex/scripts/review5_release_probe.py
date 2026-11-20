import sys,json,numpy as np,itertools
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'claude_shared/gates'));import run_gates as S
g=S.Glb(P/'export/mm6_natm.glb');cfg=json.loads((P/'gates.json').read_text());m=S.load_meshes(g)[0];S.configure_mesh(m,cfg,S.Report(cfg));pm=S.load_meshes(S.Glb(P/'review/round5_dense_spear.glb'))[0];a=next(a for a in g.doc['animations']if a['name']=='Attack');pose=g.pose(a,np.array([46/48]))[0];pp=S.transform(pose[g.names['Spear']]@np.linalg.inv(S.C),pm.rest);surface=S.Surface(m,m.solid&~m.regions['hand_R']);rows=[]
for delta in itertools.product([-.02,-.01,0,.01,.02],repeat=3):
 p=pose.copy()
 for n,i in g.names.items():
  if n=='B_L_Hand'or n.startswith('B_L_Finger'):p[i,:3,3]+=delta
 surface.build(m.posed(p));depth,_=S.penetration(surface,pp);rows.append([depth,np.linalg.norm(delta),delta])
rows.sort();print('BEST_RELEASE_OFFSETS',rows[:20]);(P/'review/round5_release_probe.json').write_text(json.dumps(rows,indent=2))
