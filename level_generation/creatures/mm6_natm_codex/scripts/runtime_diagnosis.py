import sys,json,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P.parent/'claude_shared/gates'));import run_gates as G
cfg=json.loads((P/'gates.json').read_text());cfg['props'][0]['grip_surface']['bounds']=[[-.03,-.14,-.031],[.03,.14,.031]]
g=G.Glb(P/'export/mm6_natm.glb');rep=G.Report(cfg);props=G.load_props(cfg,P,g,rep);clips={n:(a,s,e)for n,a,s,e in g.clips()};a,s,e=clips['Standing'];pose=g.pose(a,np.array([0.]))[0]
h=pose[g.names['B_R_Hand'],:3,3];roots=[pose[g.names[f'B_R_Finger{i}'],:3,3]for i in range(5)];origin=.5*(h+np.mean(roots,axis=0));m=pose[g.names['Spear']];local=G.transform(np.linalg.inv(m),origin)
cfg['props'][0]['hands'][0]['grip_point']=[0,0,float(local[2])]
(P/'gates.json').write_text(json.dumps(cfg,indent=2))
out={'palm_origin_local':local.tolist(),'grip_point':cfg['props'][0]['hands'][0]['grip_point'],'lods':[]}
for mesh in G.load_meshes(g):
 if 'shadow'in mesh.label:continue
 G.configure_mesh(mesh,cfg,rep);points=mesh.posed(pose);level=int(mesh.label[-1]);row={'lod':level,'feet':{},'grip':{}}
 for side,(ids,heel,toe)in mesh.feet.items():
  v=points[toe].mean(0)-points[heel].mean(0);row['feet'][side]={'yaw':float(np.degrees(np.arctan2(v[0],-v[1]))),'heel':points[heel].mean(0).tolist(),'toe':points[toe].mean(0).tolist()}
 tris,bary,groups,_=G.grip_points(mesh,'R',cfg);world=np.einsum('sk,tkj->tsj',bary,points[tris]).reshape(-1,3);local=G.transform(G.C@np.linalg.inv(m),world);surface=props[0]['grip_surfaces']['R'][level];solid=props[0]['solid_surfaces'][level];ds,fs=solid.signed(local)
 row['grip']['penetration_mm']=float(max(0,-ds.min())*1000);row['grip']['inside_point']=local[np.argmin(ds)].tolist()
 for name,mask in zip(['palm','thumb','index','middle','ring','pinky'],groups):
  sub=local[mask];d=np.array([surface.tree.find_nearest(Vector(p))[3]for p in sub]);j=int(d.argmin());row['grip'][name]={'gap_mm':float(d[j]*1000),'point':sub[j].tolist()}
 for clip,frame in [('Cast',21),('Attack',19),('Death',29),('Hit',20)]:
  pp=g.pose(clips[clip][0],np.array([frame/48]))[0];vv=mesh.posed(pp);prop=props[1];pm=prop['meshes'][level];pv=G.transform(pp[g.names['Buckler']]@np.linalg.inv(G.C),pm.rest);surf=G.Surface(mesh,mesh.solid).build(vv);ds,fs=surf.signed(pv);j=int(ds.argmin());q,n,fi,d=surf.tree.find_nearest(Vector(pv[j]));ids=mesh.weld_first[surf.faces[fi]];rest=mesh.rest[ids].mean(0)
  row[clip]={'depth_mm':float(max(0,-ds[j])*1000),'prop_vertex':j,'local':G.transform(np.linalg.inv(G.C),pm.rest[j]).tolist(),'body_rest':rest.tolist(),'body_pos':list(q),'normal':list(n),'prop_pos':pv[j].tolist()}
 out['lods'].append(row)
(P/'review/runtime_diagnosis.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
