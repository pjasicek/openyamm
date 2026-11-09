"""Focused exported-asset checks: LOD chains, PBR, shared tier maps, skin weights and clip keys."""
import sys,json,hashlib,io,importlib.util
from pathlib import Path
import numpy as np
from PIL import Image
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2];sys.path.insert(0,str(ROOT/'tools'));from merge_head_material import read_glb,accessor_array
spec=importlib.util.spec_from_file_location('winding',ROOT/'level_generation/decorations/mm8_3d/animated/scripts/check_winding.py');W=importlib.util.module_from_spec(spec);spec.loader.exec_module(W)
report={}
for stem in ('body','sac'):
 path=P/'export'/('hes_gloamer.glb' if stem=='body' else 'hes_gloamer_sac.glb');d,b=read_glb(path);row={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size};assert W.check(path)==0
 for mi,m in enumerate(d['meshes']):
  for key in ('openyamm_lods','openyamm_shadow_lods'):
   chain=m.get('extras',{}).get(key,[]);assert mi not in chain and len(chain)==len(set(chain)) and all(0<=i<len(d['meshes']) for i in chain)
  for p in m['primitives']:
   a=p['attributes'];pos=accessor_array(d,b,a['POSITION']);assert np.isfinite(pos).all();idx=accessor_array(d,b,p['indices']);assert idx.max()<len(pos) and idx.size%3==0
   tri=pos[idx.reshape(-1,3)];assert (np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)>1e-12).all()
   for attr in ('NORMAL','TEXCOORD_0'):
    if attr in a:assert np.isfinite(accessor_array(d,b,a[attr])).all()
   if 'WEIGHTS_0' in a:
    ws=[accessor_array(d,b,a[k]).astype(float) for k in a if k.startswith('WEIGHTS_')]
    for k,arr in zip([k for k in a if k.startswith('WEIGHTS_')],ws):
     if d['accessors'][a[k]].get('normalized'):arr/=255 if d['accessors'][a[k]]['componentType']==5121 else 65535
    weights=np.concatenate(ws,axis=1);assert np.max(abs(weights.sum(1)-1))<2e-5;assert (weights>1e-6).sum(1).max()<=8
 for m in d['materials']:
  assert not m.get('doubleSided',False) and m.get('alphaMode','OPAQUE')=='OPAQUE'
  assert 'emissiveTexture' not in m
  if 'baseColorTexture' in m.get('pbrMetallicRoughness',{}):assert m.get('extras',{}).get('openyamm_specular_mask') is True
 row['materials']=len(d['materials']);row['images']=[]
 for im in d.get('images',[]):
  v=d['bufferViews'][im['bufferView']];pixels=Image.open(io.BytesIO(b[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]));row['images'].append(list(pixels.size))
 if 'skins' in d:
  row['bones']=len(d['skins'][0]['joints']);node=next(n for n in d['nodes'] if n.get('name')=='Gloamer' and 'mesh' in n);m=d['meshes'][node['mesh']];chain=[node['mesh']]+m['extras']['openyamm_lods'];row['triangles']=[sum(d['accessors'][p['indices']]['count']//3 for p in d['meshes'][i]['primitives']) for i in chain];assert len(chain)==4 and all(a>b for a,b in zip(row['triangles'],row['triangles'][1:]));row['clips']={}
  for a in d['animations']:
   duration=0
   for s in a['samplers']:
    t=accessor_array(d,b,s['input']).ravel();o=accessor_array(d,b,s['output']);assert np.isfinite(t).all() and np.isfinite(o).all() and (np.diff(t)>0).all();duration=max(duration,float(t.max()-t.min()))
   for c in a['channels']:
    if c['target']['path']=='rotation':
     q=accessor_array(d,b,a['samplers'][c['sampler']]['output']);assert np.max(abs(np.linalg.norm(q,axis=1)-1))<.002
   row['clips'][a['name']]=duration
  if stem=='body':
   variants=d['extensions']['KHR_materials_variants']['variants'];assert [v['name'] for v in variants]==['gloamer_a','gloamer_b','gloamer_c']
   for p in m['primitives']:
    mats=[d['materials'][x['material']] for x in p['extensions']['KHR_materials_variants']['mappings']];assert len({x['pbrMetallicRoughness']['baseColorTexture']['index'] for x in mats})==1
    assert len({x['normalTexture']['index'] for x in mats})==1;assert len({x['pbrMetallicRoughness']['metallicRoughnessTexture']['index'] for x in mats})==1
 else:
  base=d['nodes'][0]['mesh'];chain=[base]+d['meshes'][base].get('extras',{}).get('openyamm_lods',[]);row['triangles']=[sum(d['accessors'][p['indices']]['count']//3 for p in d['meshes'][i]['primitives'])for i in chain]
 report[stem]=row

assert set(report['body']['clips'])=={'Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget','Cast'}
(P/'review/runtime_validation.json').write_text(json.dumps({'pass':True,'files':report},indent=2)+'\n');print('RUNTIME_VALID',[(k,r['triangles']) for k,r in report.items()])
