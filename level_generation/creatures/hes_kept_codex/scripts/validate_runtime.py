"""Focused exported-asset checks: LOD chains, PBR, shared tier maps, skin weights and clip keys."""
import sys,json,hashlib,io,importlib.util
from pathlib import Path
import numpy as np
from PIL import Image
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2];sys.path.insert(0,str(ROOT/'tools'));from merge_head_material import read_glb,accessor_array
spec=importlib.util.spec_from_file_location('winding',ROOT/'level_generation/decorations/mm8_3d/animated/scripts/check_winding.py');W=importlib.util.module_from_spec(spec);spec.loader.exec_module(W)
report={}
for stem in ('m_ragged','m_enforcer','m_freed','f_freed','collar','pick','club'):
 path=P/'export'/f'hes_kept_{stem}.glb';d,b=read_glb(path);row={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size};assert W.check(path)==0
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
  row['bones']=len(d['skins'][0]['joints']);node=next(n for n in d['nodes'] if n.get('name')=='Kept' and 'mesh' in n);m=d['meshes'][node['mesh']];chain=[node['mesh']]+m['extras']['openyamm_lods'];row['triangles']=[sum(d['accessors'][p['indices']]['count']//3 for p in d['meshes'][i]['primitives']) for i in chain];assert len(chain)==4 and all(a>b for a,b in zip(row['triangles'],row['triangles'][1:]));row['clips']={}
  for a in d['animations']:
   duration=0
   for s in a['samplers']:
    t=accessor_array(d,b,s['input']).ravel();o=accessor_array(d,b,s['output']);assert np.isfinite(t).all() and np.isfinite(o).all() and (np.diff(t)>0).all();duration=max(duration,float(t.max()-t.min()))
   for c in a['channels']:
    if c['target']['path']=='rotation':
     q=accessor_array(d,b,a['samplers'][c['sampler']]['output']);assert np.max(abs(np.linalg.norm(q,axis=1)-1))<.002
   row['clips'][a['name']]=duration
  if stem=='m_ragged':
   variants=d['extensions']['KHR_materials_variants']['variants'];assert [v['name'] for v in variants]==['kept_a','kept_b','kept_c']
   for p in m['primitives']:
    mats=[d['materials'][x['material']] for x in p['extensions']['KHR_materials_variants']['mappings']];assert len({x['pbrMetallicRoughness']['baseColorTexture']['index'] for x in mats})==1
    assert len({x['normalTexture']['index'] for x in mats})==1;assert len({x['pbrMetallicRoughness']['metallicRoughnessTexture']['index'] for x in mats})==1
 else:
  base=d['nodes'][0]['mesh'];chain=[base]+d['meshes'][base].get('extras',{}).get('openyamm_lods',[]);row['triangles']=[sum(d['accessors'][p['indices']]['count']//3 for p in d['meshes'][i]['primitives'])for i in chain]
 if stem=='m_enforcer':
  node=next(n for n in d['nodes'] if n.get('name')=='KeptPlate');chain=[node['mesh']]+d['meshes'][node['mesh']]['extras']['openyamm_lods'];row['plate_triangles']=[sum(d['accessors'][p['indices']]['count']//3 for p in d['meshes'][i]['primitives'])for i in chain];row['core_triangles']=row['triangles'];row['triangles']=[x+y for x,y in zip(row['core_triangles'],row['plate_triangles'])]
 report[stem]=row
assert json.loads((P/'review/addons_v2/final_gates.json').read_text())['pass']
for name in ('hes_kept_m_ragged','hes_kept_m_enforcer','hes_kept_m_freed','hes_kept_f_freed'):assert json.loads((P/'work/lodrep'/(name+'_addons_v2' if name in ('hes_kept_m_ragged','hes_kept_m_enforcer') else name)/'result.json').read_text())['passed']
# Check the channels Blender can silently repack, and protect the accepted body/head art.
def pixels(d,b,tex):
 im=d['images'][d['textures'][tex['index']]['source']];v=d['bufferViews'][im['bufferView']]
 return np.array(Image.open(io.BytesIO(b[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']])))
def body_maps(path):
 d,b=read_glb(path);m=next(m for m in d['materials'] if m['name']=='KeptBody_A');q=m['pbrMetallicRoughness']
 return [pixels(d,b,x) for x in (q['baseColorTexture'],q['metallicRoughnessTexture'],m['normalTexture'])]
baseline=body_maps(P/'work/addons_v2/baseline/hes_kept_m_ragged.glb')
for stem in ('m_ragged','m_enforcer'):
 assert all(np.array_equal(a,b) for a,b in zip(baseline,body_maps(P/'export'/f'hes_kept_{stem}.glb')))
for part in ('collar','pick','club','plate'):
 path=P/'export'/('hes_kept_m_enforcer.glb' if part=='plate' else f'hes_kept_{part}.glb');d,b=read_glb(path)
 m=next(m for m in d['materials'] if m.get('name')==f'KeptV2_{part}');q=m['pbrMetallicRoughness']
 actual=pixels(d,b,q['metallicRoughnessTexture']);expected=np.array(Image.open(P/'textures/props_v2'/f'{part}_metal_rough.png'))
 assert np.array_equal(actual,expected) and np.all(actual[:,:,2]==0) and q['metallicFactor']==0
 assert np.all(actual[:,:,0]==(45 if part=='plate' else 77))
 if part!='plate':assert '_LOD' not in d['meshes'][d['nodes'][0]['mesh']]['name']
# The Enforcer contains exactly the A/B core plus its separate skinned plate.
da,ba=read_glb(P/'export/hes_kept_m_ragged.glb');dc,bc=read_glb(P/'export/hes_kept_m_enforcer.glb')
def core(d):return d['meshes'][next(n for n in d['nodes'] if n.get('name')=='Kept' and 'mesh' in n)['mesh']]['primitives']
assert len(core(da))==len(core(dc))
for pa,pc in zip(core(da),core(dc)):
 assert pa['attributes'].keys()==pc['attributes'].keys()
 for k in pa['attributes']:assert np.array_equal(accessor_array(da,ba,pa['attributes'][k]),accessor_array(dc,bc,pc['attributes'][k]))
 assert np.array_equal(accessor_array(da,ba,pa['indices']),accessor_array(dc,bc,pc['indices']))
for ident,count in {'kept_a':2,'kept_b':3,'kept_c':4,'freed_m':1,'freed_f':1}.items():
 d,b=read_glb(P/'review/viewer'/f'{ident}.glb');assert len(d['meshes'])==count
 assert {a['name'] for a in d['animations']}=={'Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget'}
paid=json.loads((P/'review/paid_provenance.json').read_text())
assert all(hashlib.sha256((P/r['path']).read_bytes()).hexdigest()==r['sha256'] for r in paid['records'])
contract={'pass':True,'accepted_body_head_maps_pixel_identical':True,'all_collared_tiers_share_identical_core':True,'packed_material_maps_exact':True,'zero_degenerate_triangles':True,'viewer_attachments_present':True,'paid_records_unchanged':len(paid['records'])}
(P/'review/addons_v2/export_contract.json').write_text(json.dumps(contract,indent=2)+'\n')

(P/'review/runtime_validation.json').write_text(json.dumps({'pass':True,'files':report},indent=2)+'\n');print('RUNTIME_VALID',[(k,r['triangles']) for k,r in report.items()])
