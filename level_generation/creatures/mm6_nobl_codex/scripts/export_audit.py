"""Validate packaged Swordsman geometry, variants, materials and installation."""
import sys,json,hashlib,numpy as np
from pathlib import Path
p=Path(__file__).resolve().parents[1];repo=p.parents[2];sys.path.insert(0,str(repo/'tools'))
from merge_head_material import read_glb,accessor_array,image_of
expected={'Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget'}
report={}
for name in ['mm6_nobl','mm6_nobl_sword']:
 path=p/'export'/f'{name}.glb';d,b=read_glb(path)
 assert {v['name'] for v in d['extensions']['KHR_materials_variants']['variants']}=={'nobl_a','nobl_b','nobl_c'}
 base=next(m for m in d['meshes'] if 'openyamm_lods' in m.get('extras',{}));levels=[base]+[d['meshes'][i] for i in base['extras']['openyamm_lods']]
 tris=[sum(d['accessors'][pr['indices']]['count']//3 for pr in m['primitives']) for m in levels]
 for mesh in d['meshes']:
  for pr in mesh['primitives']:
   for key in ['POSITION','NORMAL','TEXCOORD_0']:
    if key in pr['attributes']:assert np.isfinite(accessor_array(d,b,pr['attributes'][key])).all()
   if 'WEIGHTS_0' in pr['attributes']:
    wa=d['accessors'][pr['attributes']['WEIGHTS_0']];w=accessor_array(d,b,pr['attributes']['WEIGHTS_0'])
    if wa.get('normalized') and w.dtype.kind in 'ui':w=w.astype(float)/np.iinfo(w.dtype).max
    total=w.sum(1)
    if 'WEIGHTS_1' in pr['attributes']:
     wa1=d['accessors'][pr['attributes']['WEIGHTS_1']];w1=accessor_array(d,b,pr['attributes']['WEIGHTS_1'])
     if wa1.get('normalized') and w1.dtype.kind in 'ui':w1=w1.astype(float)/np.iinfo(w1.dtype).max
     total+=w1.sum(1)
    assert np.max(abs(total-1))<1e-4,(mesh.get('name'),float(np.max(abs(total-1))))
    assert 'WEIGHTS_2' not in pr['attributes']
    if mesh is base:assert 'WEIGHTS_1' not in pr['attributes']
 for material in d['materials']:
  assert material['pbrMetallicRoughness']['metallicFactor']==0
  assert material['extras']['openyamm_specular_mask']
  assert len(material['extras']['openyamm_region_ramps'])==2
 if name=='mm6_nobl':
  assert {a['name'] for a in d['animations']}==expected
  assert any(n.get('name')=='Sword' for n in d['nodes'])
  durations={a['name']:max(d['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in d['animations']}
  sizes=[image_of(d,b,i)[0].size for i in range(len(d['textures']))]
  assert all(size==(2080,1024) for size in sizes)
 else:
  for pr in base['primitives']:
   uv=accessor_array(d,b,pr['attributes']['TEXCOORD_0']);m=d['materials'][pr['material']]
   im,_=image_of(d,b,m['extras']['openyamm_region_mask']['index']);im=np.asarray(im)
   x=np.clip((uv[:,0]*im.shape[1]).astype(int),0,im.shape[1]-1);y=np.clip((uv[:,1]*im.shape[0]).astype(int),0,im.shape[0]-1)
   assert im[y,x,:2].max()==0,'sword inherits garment palette'
 report[name]={'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'triangles':tris,'materials':len(d['materials']),'images':len(d['images']),'joints':len(d.get('skins',[{'joints':[]}])[0]['joints'])}
assert sum(report[n]['triangles'][0] for n in report)<=10000
report['clips_seconds']=durations
(p/'work/export_audit.json').write_text(json.dumps(report,indent=1));print(json.dumps(report,indent=1))
