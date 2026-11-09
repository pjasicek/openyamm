from pathlib import Path
import sys,json,hashlib,numpy as np
p=Path(__file__).resolve().parents[1];root=p.parents[2];sys.path.insert(0,str(root/'tools'))
from merge_head_material import read_glb,accessor_array
report={}
for name in ['mm8_m460','mm8_m460_staff']:
 path=p/'export'/f'{name}.glb';d,b=read_glb(path);counts=[];maxweight=0
 for mesh in d['meshes']:
  counts.append(sum(d['accessors'][q['indices']]['count']//3 for q in mesh['primitives']))
  for q in mesh['primitives']:
   a=q['attributes'];pos=accessor_array(d,b,a['POSITION']);idx=accessor_array(d,b,q['indices']);assert np.isfinite(pos).all() and idx.max()<len(pos)
   if 'WEIGHTS_0' in a:
    w=accessor_array(d,b,a['WEIGHTS_0'])
    if 'WEIGHTS_1' in a:w=np.concatenate([w,accessor_array(d,b,a['WEIGHTS_1'])],axis=1)
    assert np.max(abs(w.sum(1)-1))<1e-5;assert 'WEIGHTS_2' not in a;maxweight=max(maxweight,int((w>1e-6).sum(1).max()))
  assert len(mesh['primitives'])==1,(name,mesh.get('name'))
 base=next(i for i,m in enumerate(d['meshes']) if 'openyamm_lods' in m.get('extras',{}));chain=[base]+d['meshes'][base]['extras']['openyamm_lods'];tri=[counts[i] for i in chain]
 assert len(chain)==4 and all(a>b for a,b in zip(tri,tri[1:])),tri
 if name=='mm8_m460':
  assert len(d['skins'])==1 and len(d['animations'])==8 and tri[0]==9811
  assert [v['name'] for v in d['extensions']['KHR_materials_variants']['variants']]==['m460_a','m460_b','m460_c']
  for a in d['animations']:
   for s in a['samplers']:
    for k in ['input','output']:assert np.isfinite(accessor_array(d,b,s[k])).all()
  for m in d['materials']:
   assert m.get('extras',{}).get('openyamm_specular_mask'),m['name']
 else:assert not d.get('skins') and not d.get('animations') and tri[0]==600
 installed=root/'assets_source/worlds/mm8/models'/path.name
 assert installed.exists() and hashlib.sha256(installed.read_bytes()).digest()==hashlib.sha256(path.read_bytes()).digest()
 report[name]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size,'colour_triangles':tri,'max_influences':maxweight}
(p/'work/static_audit.json').write_text(json.dumps(report,indent=2)+'\n');print('STATIC_AUDIT',report)
