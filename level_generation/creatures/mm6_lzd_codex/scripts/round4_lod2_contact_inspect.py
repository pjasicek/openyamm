import sys,json,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P.parent/'claude_shared/gates'));from run_gates import *
g=Glb(P/'export/mm6_lzd.glb');cfg=json.loads((P/'gates.json').read_text());report=Report(cfg);m=next(x for x in load_meshes(g)if x.label.endswith('colour2'));configure_mesh(m,cfg,report);acts={a['name']:a for a in g.doc['animations']};props=load_props(cfg,P,g,report);rows=json.loads((P/'review/round4/gates_distance_final/gates.json').read_text())['gates'];out=[]
for row in rows:
 if row['status']!='FAIL'or row['lod']!=m.label:continue
 pose=g.pose(acts[row['clip']],np.array([row['time_s']]))[0];points=m.posed(pose)
 if row['gate']=='prop_body_penetration_mm':
  pp=transform(pose[g.names['Bow']]@np.linalg.inv(C),props[0]['meshes'][2].rest);pt=pp[row['detail']['prop_vertex']];surface=Surface(m,m.solid).build(points)
 else:
  pt=points[np.flatnonzero(m.head_samples)[row['detail']['sample_vertex']]];surface=m.head_surface.build(points)
 hit,n,face,dist=surface.tree.find_nearest(Vector(pt));ids=m.weld_first[surface.faces[face]];item={'gate':row['gate'],'rest_surface_points':m.rest[ids].tolist(),'pose_surface_points':points[ids].tolist(),'query':list(pt),'normal':list(n),'distance':dist,'weights':[[(m.bone_names[j],float(w))for j,w in zip(m.joints[i],m.weights[i])if w>.1]for i in ids]};print(item,flush=True);out.append(item)
(P/'review/round4/lod2_contacts.json').write_text(json.dumps(out,indent=2))
