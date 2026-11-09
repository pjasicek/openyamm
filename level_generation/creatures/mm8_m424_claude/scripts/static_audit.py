import sys,json,hashlib
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2];sys.path.insert(0,str(ROOT/'tools'))
from merge_head_material import read_glb,accessor_array
report={}
for name in ['mm8_m424','mm8_m424_dagger']:
 p=P/'export'/f'{name}.glb';d,b=read_glb(p)
 assert hashlib.sha256(p.read_bytes()).digest()==hashlib.sha256((ROOT/'assets_source/worlds/mm8/models'/p.name).read_bytes()).digest()
 counts=[];maxweight=0
 for m in d['meshes']:
  counts.append(sum(d['accessors'][x['indices']]['count']//3 for x in m['primitives']))
  for prim in m['primitives']:
   a=prim['attributes'];pos=accessor_array(d,b,a['POSITION']);assert np.isfinite(pos).all()
   idx=accessor_array(d,b,prim['indices']);assert idx.max()<len(pos)
   if 'WEIGHTS_0' in a:
    w=accessor_array(d,b,a['WEIGHTS_0']);assert np.max(abs(w.sum(1)-1))<1e-5
    maxweight=max(maxweight,int((w>1e-6).sum(1).max()));assert 'WEIGHTS_1' not in a
 if name=='mm8_m424':
  assert len(d['skins'])==1 and len(d['animations'])==7
  assert len(d['meshes'][0]['primitives'])==1
  assert [v['name'] for v in d['extensions']['KHR_materials_variants']['variants']]==['m424_a','m424_b','m424_c']
  for a in d['animations']:
   for s in a['samplers']:
    for key in ['input','output']:assert np.isfinite(accessor_array(d,b,s[key])).all()
 else:assert not d.get('skins') and not d.get('animations')
 report[name]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size,'triangles_by_mesh':counts,'max_influences':maxweight}
assert report['mm8_m424']['triangles_by_mesh'][:4]==[11585,5791,2084,693]
(P/'work/static_audit.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
