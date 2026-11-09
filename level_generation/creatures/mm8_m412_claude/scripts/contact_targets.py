import bpy,sys,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'claude_shared/gates'));import run_gates as G
j=json.loads((P/'review/gates_contacts/gates.json').read_text());g=G.Glb(P/'export/mm8_m412.glb');m=G.load_meshes(g)[0];cfg=json.loads((P/'gates.json').read_text());r=G.Report(cfg);G.configure_mesh(m,cfg,r);pg=G.Glb(P/'export/mm8_m412_cutlass.glb');pm=G.load_meshes(pg)[0]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/pirate_final.blend'));o=bpy.data.objects['Pirate'];co=np.array([v.co[:] for v in o.data.vertices]);pc=np.array([x.value for x in o.data.attributes['piece'].data])
for row in j['gates']:
 if row['lod']!='Pirate/colour0' or row['status']!='FAIL' or row['gate'] not in ['prop_body_penetration_mm','arm_body_penetration_mm']:continue
 clip=row['clip'];tm=row['time_s'];pose=g.pose(next(a for n,a,s,e in g.clips() if n==clip),np.array([tm]))[0];points=m.posed(pose)
 if row['gate']=='prop_body_penetration_mm':
  pi=row['detail']['prop_vertex'];pt=G.transform(pose[g.names['Sword']]@np.linalg.inv(G.C),pm.rest)[pi];surf=G.Surface(m,~m.regions['hand_R']).build(points);source='cutlass '+str(pm.rest[pi].tolist())
 else:
  side=row['region'];ix=np.where(m.contact_samples[side])[0][row['detail']['sample_vertex']];pt=points[ix];surf=m.surfaces[side].build(points);source='body P'+str(int(pc[np.argmin(np.linalg.norm(co-m.rest[ix],axis=1))]))
 loc,nrm,fi,dist=surf.tree.find_nearest(tuple(pt));ids=m.weld_first[surf.faces[fi]];vs=[int(np.argmin(np.linalg.norm(co-m.rest[i],axis=1))) for i in ids]
 print('TARGET',clip,tm,source,'-> pieces',pc[vs].tolist(),'nearest',list(loc),'depth',dist,'rest',m.rest[ids].tolist())
