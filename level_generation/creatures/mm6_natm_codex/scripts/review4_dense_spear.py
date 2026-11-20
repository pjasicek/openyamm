"""Tessellate the unchanged near spear surface for the shared runner's vertex collision sampling."""
import sys,json,copy,hashlib,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'));from merge_head_material import read_glb,write_glb,accessor_array,append_accessor,compact
source=P/'export/mm6_natm_spear.glb';d,b=read_glb(source);counts=[]
for level,mesh in enumerate(d['meshes']):
 for pr in mesh['primitives']:
  attrs={n:accessor_array(d,b,i)for n,i in pr['attributes'].items()};pos=attrs['POSITION'];tris=accessor_array(d,b,pr['indices']).reshape(-1,3);new={n:[]for n in attrs};ids=[];count=0
  for tri in tris:
   stack=[np.eye(3)]
   while stack:
    weights=stack.pop();xyz=weights@pos[tri];edges=[(0,1,2),(1,2,0),(2,0,1)];j,k,h=max(edges,key=lambda edge:np.linalg.norm(xyz[edge[0]]-xyz[edge[1]]))
    if np.linalg.norm(xyz[j]-xyz[k])>(.02+.004*level):
     mid=(weights[j]+weights[k])*.5;stack.extend([np.array([weights[j],mid,weights[h]]),np.array([mid,weights[k],weights[h]])]);continue
    for key,arr in attrs.items():new[key].extend(weights@arr[tri])
    ids.append([count,count+1,count+2]);count+=3
  positions,indices=np.unique(np.round(np.array(new['POSITION'],dtype=np.float32),7),axis=0,return_inverse=True)
  pr['attributes']={'POSITION':append_accessor(d,b,positions,{'componentType':5126,'type':'VEC3'},34962)}
  pr['indices']=append_accessor(d,b,indices[np.array(ids).ravel()].astype(np.uint32),{'componentType':5125,'type':'SCALAR'},34963);count=len(positions)
 counts.append({'lod':level,'vertices':count,'triangles':len(ids),'maximum_edge_m':.02+.004*level})
d,b=compact(d,b);write_glb(P/'review/round4_dense_spear.glb',d,b)
c=json.loads((P/'review/round4_probe.gates.json').read_text());c['props'][0]['file']='round4_dense_spear.glb';c['thresholds'].update(lod1_ratio=1,lod2_ratio=1,lod3_ratio=1);(P/'review/round4_dense.gates.json').write_text(json.dumps(c,indent=2));(P/'review/round4_dense_provenance.json').write_text(json.dumps({'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'surface':'Unchanged surfaces of all four spear LODs, longest-edge coplanar subdivision at 20/24/28/32 mm. Runtime prop unchanged. Probe triangle-ratio limits are 1 because subdivision measures contact; production triangle budgets are validated separately on the actual assets.','lods':counts},indent=2));print('DENSE_SPEAR',counts,flush=True)
