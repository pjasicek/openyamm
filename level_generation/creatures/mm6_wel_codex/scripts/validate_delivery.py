"""Validate installed geometry, exact animation preservation and tier/attachment contracts."""
from pathlib import Path
import sys,json,hashlib,io
import numpy as np
from PIL import Image
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'))
from merge_head_material import read_glb,accessor_array
reports=[];o,ob=read_glb(P/'export/mm6_wel_runtime_lod0.glb')
for name in ['mm6_wel','mm6_wel_trident']:
 source=P/'export'/f'{name}.glb';installed=P.parents[2]/'assets_source/worlds/mm6/models'/source.name
 assert source.read_bytes()==installed.read_bytes()
 for path in [source,P.parents[2]/'assets_dev/worlds/mm6/models'/source.name]:
  d,b=read_glb(path);variants=[v['name'] for v in d['extensions']['KHR_materials_variants']['variants']];assert variants==['wel_a','wel_b','wel_c']
  assert all('KHR_materials_unlit' not in m.get('extensions',{}) for m in d['materials'])
  base=next((m for m in d['meshes'] if 'openyamm_lods' in m.get('extras',{})),d['meshes'][0]);chain=[d['meshes'].index(base)]+base.get('extras',{}).get('openyamm_lods',[]);counts=[]
  for idx in chain:
   mesh=d['meshes'][idx];counts.append(sum(d['accessors'][p['indices']]['count']//3 for p in mesh['primitives']))
   for p in mesh['primitives']:
    assert len(p['extensions']['KHR_materials_variants']['mappings'])==3
    pos=accessor_array(d,b,p['attributes']['POSITION']);indices=accessor_array(d,b,p['indices']);assert np.isfinite(pos).all() and indices.max()<len(pos)
    if 'JOINTS_0' in p['attributes']:
     w=accessor_array(d,b,p['attributes']['WEIGHTS_0']);j=accessor_array(d,b,p['attributes']['JOINTS_0'])
     if 'WEIGHTS_1' in p['attributes']:w=np.concatenate([w,accessor_array(d,b,p['attributes']['WEIGHTS_1'])],1);j=np.concatenate([j,accessor_array(d,b,p['attributes']['JOINTS_1'])],1)
     assert np.isfinite(w).all() and np.max(abs(w.sum(1)-1))<.001 and j.max()<80
  assert all(a>b for a,b in zip(counts,counts[1:]))
  sizes=[]
  for img in d['images']:
   v=d['bufferViews'][img['bufferView']];off=v.get('byteOffset',0);sizes.append(Image.open(io.BytesIO(b[off:off+v['byteLength']])).size)
  if name=='mm6_wel':
   names={n.get('name') for n in d['nodes']};assert {'Socket_Trident_Head','Trident','Socket_Palm_Left','Socket_Eye_Right'}<=names;assert len(d['skins'])==1 and len(d['skins'][0]['joints'])==80
   assert len(base['extras']['openyamm_shadow_lods'])==4
   assert sum(size==(2080,1024) for size in sizes)==4
   assert len(d['animations'])==9
   foam=next(m for m in d['materials'] if m.get('name')=='Foam');assert foam['alphaMode']=='MASK'
   for a in o['animations']:
    c=next(x for x in d['animations'] if x['name']==a['name']);assert len(a['samplers'])==len(c['samplers'])
    for x,y in zip(a['samplers'],c['samplers']):
     for key in ['input','output']:assert np.array_equal(accessor_array(o,ob,x[key]),accessor_array(d,b,y[key]))
  else:assert not d.get('skins') and not d.get('animations')
  reports.append({'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'triangles':counts,'variants':variants,'image_sizes':sizes,'animation_samples_retained':True if name=='mm6_wel' else 'rigid attachment'})
(P/'review/checks').mkdir(exist_ok=True);(P/'review/checks/delivery.json').write_text(json.dumps(reports,indent=2)+'\n');print(json.dumps(reports))
