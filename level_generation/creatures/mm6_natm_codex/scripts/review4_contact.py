import sys,json,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'claude_shared/gates'));import run_gates as S
g=S.Glb(P/'export/mm6_natm.glb');cfg=json.loads((P/'gates.json').read_text());ms=S.load_meshes(g);a=next(a for a in g.doc['animations']if a['name']=='Attack')
for name,level,f in [('spear',3,54),('spear',2,54)]:
 ps=S.load_meshes(S.Glb(P/'review/round4_dense_spear.glb'));
 m=ms[level];S.configure_mesh(m,cfg,S.Report(cfg));po=g.pose(a,np.array([f/48]))[0];p=m.posed(po);surf=S.Surface(m,m.solid&(~m.regions['hand_R'] if name=='spear' else np.ones(len(m.rest),bool))).build(p);prop=S.transform(po[g.names[name.capitalize()]]@np.linalg.inv(S.C),ps[level].rest);depth,index=S.penetration(surf,prop);hit=surf.tree.find_nearest(Vector(prop[index]));others=m.weld_first[surf.faces[hit[2]]];labels=lambda v:[(m.bone_names[j],float(w))for j,w in zip(m.joints[v],m.weights[v])if w>.1]
 print('BUCKLER_CONTACT',level,f,depth,'sample',index,prop[index].tolist(),'prop_rest',ps[level].rest[index].tolist(),'surface',[labels(i)for i in others],'surface_rest',m.rest[others].tolist(),'normal',list(hit[1]),flush=True)
