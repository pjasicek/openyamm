from pathlib import Path
import sys,json,numpy as np,hashlib
sys.path.insert(0,'tools')
from build_actor_lods import read_glb,accessor_bytes
from normal_map_convention import convert
p=Path('level_generation/creatures/mm8_m608_codex');source=p/'export/mm8_m608.glb';d,b=read_glb(source)
def a(i):
 x=d['accessors'][i];return np.frombuffer(accessor_bytes(d,b,i),dtype={5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}[x['componentType']]).reshape(x['count'],-1)
report=[]
used={n['mesh'] for n in d['nodes'] if 'mesh' in n}
for node in d['nodes']+[{'name':m['name'],'mesh':i} for i,m in enumerate(d['meshes']) if i not in used]:
 if 'mesh' not in node:continue
 for prim in d['meshes'][node['mesh']]['primitives']:
  attrs=prim['attributes'];pos=a(attrs['POSITION']);idx=a(prim['indices']).reshape(-1,3);v=pos[idx];cross=np.cross(v[:,1]-v[:,0],v[:,2]-v[:,0]);area=np.linalg.norm(cross,axis=1)
  inverted=0
  if 'NORMAL' in attrs:inverted=int((np.einsum('ij,ij->i',cross,a(attrs['NORMAL'])[idx].mean(axis=1)) < -1e-10).sum())
  uvbad=0
  if 'TEXCOORD_0' in attrs:
   uv=a(attrs['TEXCOORD_0'])[idx];e=uv[:,1]-uv[:,0];f=uv[:,2]-uv[:,0];uvbad=int(((abs(e[:,0]*f[:,1]-e[:,1]*f[:,0])<1e-12)&(area>1e-10)).sum())
  report.append({'node':node['name'],'triangles':len(idx),'degenerate_geometry':int((area<1e-10).sum()),'uv_degenerate':uvbad,'opposite_normals':inverted})
  assert inverted==0,(node['name'],inverted)
  if node['name'] in ['Juggernaut','Rubble']:assert uvbad==0,(node['name'],uvbad)
normals=convert(source,source,check=True,threshold=.15);assert all(not x[2] for x in normals)
(p/'work/static_audit.json').write_text(json.dumps({'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'primitives':report,'normal_convention':normals},indent=2));print(json.dumps(report))
