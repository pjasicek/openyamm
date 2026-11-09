import bpy,sys,runpy,json,numpy as np
from pathlib import Path
from mathutils import Vector,kdtree
P=Path(__file__).resolve().parents[1];g=runpy.run_path(str(P.parent/'claude_shared/gates/run_gates.py'),run_name='diagnostic');cfg=json.loads((P/'gates.json').read_text());report=g['Report'](cfg)
a=g['Glb'](P/'export/mm8_m576.glb');mesh=g['load_meshes'](a)[0];g['configure_mesh'](mesh,cfg,report)
bpy.ops.wm.open_mainfile(filepath=str(P/'work/master_textured_uv.blend'));b=bpy.data.objects['Body'];tree=kdtree.KDTree(len(b.data.vertices))
for v in b.data.vertices:tree.insert(v.co,v.index)
tree.balance();pieces=b.data.attributes['piece'].data
for side,ids in [('L',[382,195]),('R',[78])]:
 selected=np.flatnonzero(mesh.contact_samples[side])
 for index in ids:
  i=int(selected[index]);p=mesh.rest[i];_,j,dist=tree.find(Vector(p));print('CONTACT SAMPLE',side,index,'meshvertex',i,'rest',p.tolist(),'authorvertex',j,'piece',pieces[j].value,'distance',dist,'weights',[(b.vertex_groups[e.group].name,e.weight) for e in b.data.vertices[j].groups])
# Grip file node axes are encoded by the Blender glTF exporter; report its actual near-shaft geometry.
prop=g['Glb'](P/'export/mm8_m576_trident.glb');pm=g['load_meshes'](prop)[0];print('PROP REST BOUNDS',pm.rest.min(0),pm.rest.max(0))

for name,time,side in [('Attack',.125,'L'),('Fidget',.145833333,'L'),('Hit',0,'R'),('Death',2.416666667,'L')]:
 clip=next(row[1] for row in a.clips() if row[0]==name);pose=a.pose(clip,np.array([time]))[0];points=mesh.posed(pose);surface=mesh.surfaces[side].build(points);selected=points[mesh.contact_samples[side]];depth,index=g['penetration'](surface,selected);point=selected[index];loc,nrm,face,distance=surface.tree.find_nearest(Vector(point));verts=mesh.weld_first[surface.faces[face]];rest=mesh.rest[verts].mean(0);_,j,_=tree.find(Vector(rest));print('WORST CONTACT',name,time,side,'depth',depth,'point',point,'hit',loc,'target piece',pieces[j].value,'rest',rest,flush=True)
