import runpy,json,numpy as np,bpy
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree
p=Path(__file__).resolve().parents[1];g=runpy.run_path(str(p.parents[2]/'level_generation/creatures/claude_shared/gates/run_gates.py'),run_name='diagnostic')
config=json.loads((p/'gates.json').read_text());G=g['Glb'](p/'export/m468_full.glb');m=g['load_meshes'](G)[0];g['configure_mesh'](m,config,g['Report'](config));clips={n:a for n,a,_,_ in G.clips()}
bpy.ops.wm.open_mainfile(filepath=str(p/'work/full_repaired.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];co=np.array([tuple(v.co) for v in body.data.vertices]);pv=np.array([a.value for a in body.data.attributes['piece'].data]);kd=KDTree(len(co))
for i,c in enumerate(co):kd.insert(c,i)
kd.balance()
def info(i):
 _,j,_=kd.find(Vector(m.rest[i]));return {'export_vertex':int(i),'master_vertex':j,'piece':int(pv[j]),'rest':co[j].tolist(),'weights':[(body.vertex_groups[e.group].name,round(e.weight,3)) for e in body.data.vertices[j].groups if e.weight>.01]}

x=json.loads((p/'review/full_gates/gates.json').read_text())
for r in x['gates']:
 if r['status']=='FAIL' and r['gate']=='arm_stretch_max':print('EDGE',r['clip'],r['time_s'],[info(i) for i in r['detail']['edge']])
