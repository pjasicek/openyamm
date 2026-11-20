"""Select the reviewed reduction and ground it before building runtime LODs."""
import copy,json,sys
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parents[2]/'tools'))
from build_actor_lods import read_glb,write_glb,accessor_bytes,append_accessor
report={}
for name,level,height in [('egg_cluster',1,.75),('brood_sac',2,1.2),('ganglion',2,1.5)]:
 doc,raw=read_glb(P/'work'/('hes_'+name+'_reduction_study.glb'));binary=bytearray(raw)
 node=next(n for n in doc['nodes'] if n.get('name')=='BroodBody')
 original=doc['meshes'][node['mesh']]
 chosen=copy.deepcopy(doc['meshes'][original['extras']['openyamm_lods'][level-1]])
 positions=[np.frombuffer(accessor_bytes(doc,binary,q['attributes']['POSITION']),np.float32).reshape(-1,3).copy() for q in chosen['primitives']]
 lo=min(a[:,1].min() for a in positions);hi=max(a[:,1].max() for a in positions)
 assert np.isfinite([lo,hi]).all() and hi>lo
 factor=height/(hi-lo)
 for q,a in zip(chosen['primitives'],positions):
  a[:,1]-=lo;a*=factor
  acc=copy.deepcopy(doc['accessors'][q['attributes']['POSITION']]);acc['min']=a.min(0).tolist();acc['max']=a.max(0).tolist()
  q['attributes']['POSITION']=append_accessor(doc,binary,acc,a.tobytes())
  weights=np.frombuffer(accessor_bytes(doc,binary,q['attributes']['WEIGHTS_0']),np.float32).reshape(-1,4)
  assert np.allclose(weights.sum(1),1) and np.allclose(weights[:,0],1)
 chosen.pop('extras',None);chosen['name']='BroodBody';node['mesh']=0;doc['meshes']=[chosen]
 write_glb(P/'export'/('hes_'+name+'_lod0.glb'),doc,binary)
 report[name]={'authored_triangles':sum(doc['accessors'][q['indices']]['count']//3 for q in original['primitives']),
               'lod0_triangles':sum(doc['accessors'][q['indices']]['count']//3 for q in chosen['primitives']),
               'selected_ratio':[.8,.6,.4][level-1],'height':height,'ground_adjustment':float(lo),'uniform_size_adjustment':float(factor),
               'reason':'Next lower study loses small resin tips and egg curvature.' if name=='egg_cluster' else '40% study visibly facets the organic lobes and support bends.'}
(P/'review/lod0_selection.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
