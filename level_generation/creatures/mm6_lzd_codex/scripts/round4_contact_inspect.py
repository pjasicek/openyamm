import sys,json,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P.parent/'claude_shared/gates'))
from run_gates import *
g=Glb(P/'export/mm6_lzd.glb');cfg=json.loads((P/'gates.json').read_text());report=Report(cfg);meshes=load_meshes(g);m=next(x for x in meshes if x.label.endswith('colour0'));configure_mesh(m,cfg,report);acts={a['name']:a for a in g.doc['animations']};props=load_props(cfg,P,g,report)
def names(ids):
 return [(int(i),[(m.bone_names[j],round(float(w),3))for j,w in zip(m.joints[i],m.weights[i])if w>.1])for i in ids]
for clip,t,side,index in [('Attack',.375,'L',482),('Running',.7083333333,'R',417)]:
 pose=g.pose(acts[clip],np.array([t]))[0];points=m.posed(pose);surface=m.surfaces[side].build(points);i=np.flatnonzero(m.contact_samples[side])[index];hit,n,face,dist=surface.tree.find_nearest(Vector(points[i]));ids=m.weld_first[surface.faces[face]];print('CONTACT',clip,points[i],names([i]),'SURFACE',names(ids),[list(points[j])for j in ids],flush=True)
pose=g.pose(acts['Attack'],np.array([.4166666667]))[0];points=m.posed(pose);surface=Surface(m,m.solid&~m.regions['hand_L']).build(points);p=props[0];pp=transform(pose[g.names['Bow']]@np.linalg.inv(C),p['meshes'][0].rest);hit,n,face,dist=surface.tree.find_nearest(Vector(pp[1242]));print('BOW',pp[1242],names(m.weld_first[surface.faces[face]]),flush=True)
for m in meshes:
 if '/colour'not in m.label:continue
 configure_mesh(m,cfg,report);pts=m.posed(g.pose(acts['Standing'],np.array([0.]))[0]);print('FEET',m.label,{s:float(np.degrees(np.arctan2((pts[toe].mean(0)-pts[heel].mean(0))[0],-(pts[toe].mean(0)-pts[heel].mean(0))[1])))for s,(ids,heel,toe)in m.feet.items()},flush=True)
