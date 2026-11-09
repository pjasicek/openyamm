"""Audit every body LOD and all clips with all eight runtime skin-weight slots."""
import json,sys
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parent/'claude_shared/floor'))
from glb_pose import Glb,Model
g=Glb(P/'export/hes_ashkite.glb');model=Model(g)
body=next(i for i,n in enumerate(g.json['nodes']) if n.get('name')=='Ashkite')
indices=[g.json['nodes'][body]['mesh']]+g.json['meshes'][0]['extras']['openyamm_lods']
report={}
for level,index in enumerate(indices):
 primitive=g.json['meshes'][index]['primitives'][0];a=primitive['attributes']
 joints=np.concatenate([g.accessor(a[k]).astype(np.int64) for k in ['JOINTS_0','JOINTS_1'] if k in a],axis=1)
 weights=np.concatenate([g.accessor(a[k]) for k in ['WEIGHTS_0','WEIGHTS_1'] if k in a],axis=1)
 assert np.max(np.abs(weights.sum(axis=1)-1))<1e-4
 weights=weights/weights.sum(axis=1,keepdims=True)
 model.primitives=[{'node':body,'positions':g.accessor(a['POSITION']),'triangles':g.accessor(primitive['indices']).astype(np.int64).reshape(-1,3),'skinned':True,'joints':joints,'weights':weights}]
 record={'triangles':len(model.primitives[0]['triangles']),'max_influences':int((weights>1e-6).sum(axis=1).max()),'vertices_over_four':int(np.count_nonzero((weights>1e-6).sum(axis=1)>4)),'clips':{}}
 assert record['max_influences']<=8
 for clip in model.clips:
  times=model.clip_times(clip);times=sorted(set(times+[(a+b)/2 for a,b in zip(times,times[1:])]))
  low=float('inf');high=-float('inf')
  for t in times:
   points=model.skinned_positions(model.world(model.sample(clip,t)))[0][0]
   assert np.isfinite(points).all()
   low=min(low,float(points[:,1].min()));high=max(high,float(points[:,1].max()))
  record['clips'][clip]={'min_y':low,'max_y':high}
  assert low>-.025,(level,clip,low)
 report[str(level)]=record
(P/'review/lod_clip_gates.json').write_text(json.dumps(report,indent=2)+'\n')
print('All LODs and clips pass floor/finite gates:',{k:min(c['min_y'] for c in v['clips'].values()) for k,v in report.items()})
