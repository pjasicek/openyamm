"""Validate installed Ogre asset contracts, finite geometry, exact animation samples, material response and attachments."""
from pathlib import Path
import sys,json,numpy as np,hashlib
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p.parents[2]/'tools'))
import merge_head_material as M
names={'Standing','Walking','Running','Attack','Hit','Fidget','Death','Dead'}
report={}
def animation_hashes(d,b):
 return {a['name']:hashlib.sha256(b''.join(M.accessor_array(d,b,s[k]).tobytes() for s in a['samplers'] for k in ('input','output'))).hexdigest() for a in d.get('animations',[])}
source,sb=M.read_glb(p/'export/mm6_ogr_runtime_lod0.glb')
for stem in ('mm6_ogr','mm6_ogr_sword'):
 f=p/'export'/f'{stem}.glb';d,b=M.read_glb(f)
 for i,a in enumerate(d['accessors']):
  if a['componentType']==5126:assert np.isfinite(M.accessor_array(d,b,i)).all(),(stem,i)
 variants=d['extensions']['KHR_materials_variants']['variants'];assert [x['name'] for x in variants]==['ogr_a','ogr_b','ogr_c']
 triangles=[];maxweights=0
 for mesh in d['meshes']:
  count=0
  for prim in mesh['primitives']:
   count+=d['accessors'][prim['indices']]['count']//3
   ids=M.accessor_array(d,b,prim['indices']);pos=M.accessor_array(d,b,prim['attributes']['POSITION']);assert ids.max()<len(pos)
   weights=[M.accessor_array(d,b,i) for k,i in prim['attributes'].items() if k.startswith('WEIGHTS_')]
   if weights:
    w=np.concatenate(weights,axis=1);assert np.max(abs(w.sum(1)-1))<1e-4;maxweights=max(maxweights,int((w>1e-6).sum(1).max()))
  triangles.append(count)
 assert maxweights<=8
 for mat in d['materials']:
  assert mat['extras']['openyamm_specular_mask'] is True
  im,_=M.image_of(d,b,mat['pbrMetallicRoughness']['metallicRoughnessTexture']['index']);r=np.array(im)[...,0]
  assert r.max()==255
  if stem=='mm6_ogr':assert r.min()==0
 if stem=='mm6_ogr':
  assert set(animation_hashes(d,b))==names
  assert animation_hashes(d,b)==animation_hashes(source,sb),'post-process changed animation samples'
  for a in d['animations']:
   if a['name'] not in {'Standing','Walking','Running','Dead'}:continue
   for c in a['channels']:
    v=M.accessor_array(d,b,a['samplers'][c['sampler']]['output']);x,y=v[0].astype(float),v[-1].astype(float)
    if c['target']['path']=='rotation':
     angle=np.degrees(2*np.arccos(np.clip(abs(np.dot(x,y)/(np.linalg.norm(x)*np.linalg.norm(y))),0,1)))
     assert angle<.1,(a['name'],c['target'],angle)
    else:assert np.linalg.norm(x-y)<1e-5,(a['name'],c['target'])
  mesh=d['meshes'][next(n['mesh'] for n in d['nodes'] if n.get('name')=='Ogre')]
  assert len(mesh['extras']['openyamm_lods'])==3 and len(mesh['primitives'])==1
  assert any(n.get('name')=='Sword' for n in d['nodes'])
 else:assert not d.get('skins') and not d.get('animations')
 report[stem]={'bytes':f.stat().st_size,'triangles_by_mesh':triangles,'max_weights':maxweights,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
(p/'export/validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
