"""Check source/cooked delivery geometry, skin limits, variants and preserved animation channels."""
import hashlib,json,sys
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1];R=P.parents[2];sys.path.insert(0,str(R/'tools'))
import merge_head_material as M
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def channels(d,b):
 out={}
 for a in d.get('animations',[]):
  for c in a['channels']:
   s=a['samplers'][c['sampler']];key=(a['name'],d['nodes'][c['target']['node']]['name'],c['target']['path'])
   out[key]=(M.accessor_array(d,b,s['input']),M.accessor_array(d,b,s['output']))
 return out
reference=channels(*M.read_glb(P/'export/mm8_m632_runtime_lod0.glb'))
report={}
for name in ('mm8_m632.glb','mm8_m632_crossbow.glb'):
 for scope,root in [('export',P/'export'),('source',R/'assets_source/worlds/mm8/models'),('runtime',R/'assets_dev/worlds/mm8/models')]:
  path=root/name;d,b=M.read_glb(path);meshes=[]
  for m in d['meshes']:
   total=vertices=max_weights=0;weight_error=0.
   for p in m['primitives']:
    attrs=p['attributes'];co=M.accessor_array(d,b,attrs['POSITION']);ix=M.accessor_array(d,b,p['indices']).reshape(-1,3)
    assert np.isfinite(co).all() and ix.min()>=0 and ix.max()<len(co)
    tri=co[ix];areas=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)/2
    assert areas.min()>1e-12,(name,m['name'],'degenerate')
    for semantic,i in attrs.items():assert np.isfinite(M.accessor_array(d,b,i)).all(),semantic
    if 'WEIGHTS_0' in attrs:
     w=np.concatenate([M.accessor_array(d,b,attrs[k]) for k in ('WEIGHTS_0','WEIGHTS_1') if k in attrs],axis=1)
     j=np.concatenate([M.accessor_array(d,b,attrs[k]) for k in ('JOINTS_0','JOINTS_1') if k in attrs],axis=1)
     max_weights=max(max_weights,int((w>1e-6).sum(1).max()));weight_error=max(weight_error,float(np.abs(w.sum(1)-1).max()))
     assert max_weights<=8 and weight_error<1e-5 and w.min()>=0 and j.max()<59
    total+=len(ix);vertices+=len(co)
   meshes.append(dict(name=m['name'],triangles=total,vertices=vertices,max_weights=max_weights,weight_sum_error=weight_error))
  variants=[v['name'] for v in d['extensions']['KHR_materials_variants']['variants']]
  assert variants==['m632_a','m632_b','m632_c']
  if name=='mm8_m632.glb':
   assert len(d['skins'][0]['joints'])==59
   actual=channels(d,b);assert actual.keys()==reference.keys()
   assert all(np.array_equal(x,y) for k in actual for x,y in zip(actual[k],reference[k]))
   clips={a['name']:max(d['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in d['animations']}
   assert len(clips)==8
  else:assert not d.get('skins') and not d.get('animations')
  for i in d['images']:
   if 'uri' in i:assert (path.parent/i['uri']).is_file(),i
  if scope=='source':assert sha(path)==sha(P/'export'/name)
  report[f'{scope}/{name}']=dict(sha256=sha(path),bytes=path.stat().st_size,meshes=meshes,variants=variants,animations_equal_to_master=name=='mm8_m632.glb')
(P/'review/delivery_checks.json').write_text(json.dumps(report,indent=2)+'\n')
print('DELIVERY PASS: six source/export/runtime files; all LODs, eight weights, three variants and preserved animations')
