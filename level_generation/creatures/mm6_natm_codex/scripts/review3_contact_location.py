import sys,json,numpy as np,runpy
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'claude_shared/gates'));import run_gates as S
g=S.Glb(P/'export/mm6_natm.glb');cfg=json.loads((P/'gates.json').read_text());m=S.load_meshes(g)[0];S.configure_mesh(m,cfg,S.Report(cfg));a=next(a for a in g.doc['animations']if a['name']=='Attack')
for f in [42,44,49,60]:
 po=g.pose(a,np.array([f/48]))[0];p=m.posed(po);surf=m.surfaces['L'].build(p);depth,index=S.penetration(surf,p[m.contact_samples['L']]);vi=np.flatnonzero(m.contact_samples['L'])[index];hit=surf.tree.find_nearest(Vector(p[vi]));others=m.weld_first[surf.faces[hit[2]]];labels=lambda v:[(m.bone_names[j],float(w))for j,w in zip(m.joints[v],m.weights[v])if w>.1]
 print('CONTACT_LOCATION',f,depth,'sample',p[vi].tolist(),labels(vi),'surface',[labels(i)for i in others],flush=True)
runpy.run_path(str(P/'scripts/review3_skin_render.py'),run_name='__main__')
