import runpy,json,numpy as np,bpy
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree
p=Path(__file__).resolve().parents[1];g=runpy.run_path(str(p.parents[2]/'level_generation/creatures/claude_shared/gates/run_gates.py'),run_name='diagnostic')
config=json.loads((p/'gates.json').read_text());G=g['Glb'](p/'export/m468_pilot.glb');m=g['load_meshes'](G)[0];g['configure_mesh'](m,config,g['Report'](config));clips={n:a for n,a,_,_ in G.clips()}
bpy.ops.wm.open_mainfile(filepath=str(p/'work/pilot_fitted.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];co=np.array([tuple(v.co) for v in body.data.vertices]);pv=np.array([a.value for a in body.data.attributes['piece'].data]);kd=KDTree(len(co))
for i,c in enumerate(co):kd.insert(c,i)
kd.balance()
def info(i):
 _,j,_=kd.find(Vector(m.rest[i]));return {'export_vertex':int(i),'master_vertex':j,'piece':int(pv[j]),'rest':co[j].tolist(),'weights':[(body.vertex_groups[e.group].name,round(e.weight,3)) for e in body.data.vertices[j].groups if e.weight>.01]}
failed=[r for r in json.loads((p/'review/pilot_gates/gates.json').read_text())['gates'] if r['status']=='FAIL' and r['gate']=='head_penetration_mm']
for role,t,region,j in [(r['clip'],r['time_s'],'head',r['detail']['sample_vertex']) for r in failed]:
 pose=G.pose(clips[role],np.array([t]))[0];points=m.posed(pose);mask=m.head_samples if region=='head' else m.contact_samples[region];ids=np.flatnonzero(mask);i=ids[j];surf=m.head_surface if region=='head' else m.surfaces[region];S=surf.build(points)
 print('CONTACT',role,t,region,info(i),'POSED',points[i].tolist(),'SURFACE_ATTRS',S.keys() if isinstance(S,dict) else type(S))
 if hasattr(S,'tree'):
  loc,n,face,dist=S.tree.find_nearest(Vector(points[i]));print('CLOSEST',list(loc),dist,[info(int(m.weld_first[k])) for k in S.faces[face]])
 if isinstance(S,dict):
  for key,v in S.items():
   if hasattr(v,'find_nearest'):print('NEAREST',key,v.find_nearest(Vector(points[i])))
for edge in [(6345,7442),(3877,10050)]:print('STRETCH_EDGE',[info(i) for i in edge])
