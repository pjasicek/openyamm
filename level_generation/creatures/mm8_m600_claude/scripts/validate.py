"""Creature-specific export gates using the shared runtime glTF pose evaluator."""
from pathlib import Path
import runpy,json,numpy as np,hashlib
P=Path(__file__).resolve().parents[1];G=runpy.run_path(str(P.parent/'claude_shared/gates/run_gates.py'),run_name='nightmare_gates')
a=G['Glb'](P/'export/mm8_m600.glb');meshes=G['load_meshes'](a);body=[m for m in meshes if m.label.startswith('Nightmare/')]
assert len(body)==8
expect={'Standing':3.,'Walking':1.,'Attack':1.,'Hit':.625,'Death':.75,'Dead':1.,'Fidget':.625}
assert {n for n,_,_,_ in a.clips()}==set(expect)
for mesh in a.doc['meshes']:
 for primitive in mesh['primitives']:
  w=a.accessor(primitive['attributes']['WEIGHTS_0']);assert np.isfinite(w).all() and (w>=0).all() and np.max(abs(w.sum(1)-1))<1e-4
report={'sha256':hashlib.sha256((P/'export/mm8_m600.glb').read_bytes()).hexdigest(),'meshes':{},'clips':{}}
for m in body:
 q=m.rest[m.faces];area=np.linalg.norm(np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]),axis=1)/2
 assert np.isfinite(m.rest).all() and (m.weights>1e-6).sum(1).max()<=4
 report['meshes'][m.label]={'triangles':len(m.faces),'tiny_faces':int((area<1e-10).sum()),'minimum_area':float(area.min())}
 assert np.count_nonzero(area<1e-10)<5,(m.label,'degenerate')
for name,clip,start,end in a.clips():
 assert abs(end-expect[name])<1e-5
 times=np.linspace(start,end,round(end*48)+1);poses=a.pose(clip,times);rows=[]
 for m in body:
  floor=1e9;p99=0.;mx=0.;endpoint=[]
  for t,pose in zip(times,poses):
   q=m.posed(pose);assert np.isfinite(q).all();floor=min(floor,float(q[:,2].min()))
   ratio=np.linalg.norm(q[m.edges[:,0]]-q[m.edges[:,1]],axis=1)/m.lengths;p99=max(p99,float(np.percentile(ratio,99)));mx=max(mx,float(ratio.max()))
   if t in [start,end]:endpoint.append(q)
  loop=float(np.linalg.norm(endpoint[0]-endpoint[-1],axis=1).max())
  rows.append({'lod':m.label,'floor_min':floor,'stretch_p99':p99,'stretch_max':mx,'endpoint_delta':loop})
  assert floor>-.009,(name,m.label,'floor',floor)
  assert p99<2 and mx<4.5,(name,m.label,'stretch',p99,mx)
  if name in ['Standing','Walking','Dead']:assert loop<.0005,(name,m.label,'loop',loop)
 report['clips'][name]=rows
 print(name,[(r['lod'],round(r['floor_min'],4),round(r['stretch_max'],2)) for r in rows],flush=True)
# The corpse is precisely the death endpoint; the delivered asset has no baked effects.
clips={n:c for n,c,_,_ in a.clips()};pd=a.pose(clips['Death'],np.array([.75]))[0];pc=a.pose(clips['Dead'],np.array([0.,1.]))
for m in body:assert np.max(np.linalg.norm(m.posed(pd)-m.posed(pc[0]),axis=1))<1e-5
assert len(a.doc['skins'][0]['joints'])==58
assert not any(n.get('name','').startswith(('MouthGlow','MouthFlame','Glow','Flame')) for n in a.nodes)
assert all(m.get('alphaMode','OPAQUE')=='OPAQUE' and 'KHR_materials_unlit' not in m.get('extensions',{}) for m in a.doc['materials'])
report['status']='PASS';(P/'review/export_gates.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS: seven clips, four colour and four shadow LODs, held corpse, no baked effects')
