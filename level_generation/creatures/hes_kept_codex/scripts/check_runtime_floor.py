"""Evaluate the assembled runtime GLBs at 120 Hz, including all eight skin weights and rigid props."""
import sys,json,hashlib
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'claude_shared/floor'));from glb_pose import Glb,Model
report={}
for ident in ('kept_a','kept_b','kept_c','freed_m','freed_f'):
 path=P/'review/viewer'/f'{ident}.glb';g=Glb(path);m=Model(g);attrs=[]
 for node in m.order:
  n=g.json['nodes'][node]
  if 'mesh' in n:attrs.extend(p['attributes'] for p in g.json['meshes'][n['mesh']]['primitives'])
 assert len(attrs)==len(m.primitives)
 for p,a in zip(m.primitives,attrs):
  if p['skinned']:
   p['weights']=np.concatenate([g.accessor(a[k]) for k in ('WEIGHTS_0','WEIGHTS_1') if k in a],axis=1).astype(float);p['weights']/=p['weights'].sum(1,keepdims=True)
   p['joints']=np.concatenate([g.accessor(a[k]) for k in ('JOINTS_0','JOINTS_1') if k in a],axis=1).astype(int)
 row={}
 for clip in m.clips:
  times=m.clip_times(clip);times=np.linspace(times[0],times[-1],int(round((times[-1]-times[0])*120))+1);low=np.array([m.lowest(clip,t) for t in times]);limit=-.002 if ident.startswith('kept_') and clip=='Death' else -.02
  assert low.min()>=limit,(ident,clip,float(low.min()),limit)
  row[clip]={'samples':len(times),'lowest_m':float(low.min()),'largest_lowest_m':float(low.max()),'time_of_lowest':float(times[low.argmin()])}
 report[ident]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'clips':row};print('RUNTIME_FLOOR',ident,min(r['lowest_m'] for r in row.values()),flush=True)
(P/'review/runtime_floor.json').write_text(json.dumps({'pass':True,'sample_hz':120,'outfits':report},indent=2)+'\n')
