"""Check final buffers, shared-body invariants, all runtime bindings and per-clip gate evidence."""
import hashlib,json,sys
from pathlib import Path
import numpy as np
import yaml
P=Path(__file__).resolve().parents[1] if Path(__file__).parent.name=='scripts' else Path.cwd()/'level_generation/creatures/hes_drudge_codex'
ROOT=P.parents[2];sys.path.insert(0,str(ROOT/'level_generation/creatures/claude_shared/floor'))
from glb_pose import Glb,Model
original=Glb(ROOT/'level_generation/creatures/hes_kreegan_claude/export/hes_kreegan.glb')
assert hashlib.sha256((ROOT/'level_generation/creatures/hes_kreegan_claude/export/hes_kreegan.glb').read_bytes()).hexdigest()=='38cc3345adbebe78ee535f2430886ee52899270951767a938ede58094eafbc11'
def fingerprint(g,clip):
 a=next(a for a in g.json['animations'] if a['name']==clip);result=[]
 for c in a['channels']:
  s=a['samplers'][c['sampler']];result.append((g.json['nodes'][c['target']['node']]['name'],c['target']['path'],g.accessor(s['input']).tobytes(),g.accessor(s['output']).tobytes()))
 return sorted(result)
report={'shared_body_preserved':True,'source_clips_preserved':True,'models':{},'gates':{},'lods':{}}
for filename in ['hes_drudge.glb','hes_thrix.glb','hes_drudge_shoulder.glb','hes_drudge_slabs.glb','hes_drudge_scarf.glb']:
 path=P/'export'/filename;g=Glb(path);d=g.json
 assert all(v.get('byteOffset',0)+v['byteLength']<=len(g.bin) for v in d['bufferViews'])
 assert d['buffers'][0]['byteLength']<=len(g.bin)
 for mesh in d['meshes']:
  for prim in mesh['primitives']:
   pos=g.accessor(prim['attributes']['POSITION']);idx=g.accessor(prim['indices'])
   assert np.isfinite(pos).all() and idx.max()<len(pos) and idx.min()>=0
   for name,i in prim['attributes'].items():assert len(g.accessor(i))==len(pos),(filename,name)
 for m in d['materials']:assert 'emissiveTexture' not in m
 report['models'][filename]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'triangles':[sum(d['accessors'][p['indices']]['count']//3 for p in mesh['primitives']) for mesh in d['meshes'][:4]]}
 if filename in ['hes_drudge.glb','hes_thrix.glb']:
  assert d['nodes']==original.json['nodes'] and d['skins'][0]['joints']==original.json['skins'][0]['joints']
  assert np.array_equal(g.accessor(d['skins'][0]['inverseBindMatrices']),original.accessor(original.json['skins'][0]['inverseBindMatrices']))
  for own,old in zip(d['meshes'][0]['primitives'],original.json['meshes'][0]['primitives']):
   for attr in old['attributes']:assert np.array_equal(g.accessor(own['attributes'][attr]),original.accessor(old['attributes'][attr])),attr
   assert np.array_equal(g.accessor(own['indices']),original.accessor(old['indices']))
  for a in original.json['animations']:assert fingerprint(g,a['name'])==fingerprint(original,a['name']),a['name']
  if filename=='hes_thrix.glb':
   assert 'KHR_materials_variants' not in d.get('extensions',{})
   assert not any('openyamm_region_ramps' in mat.get('extras',{}) for mat in d['materials'])
  else:assert [v['name'] for v in d['extensions']['KHR_materials_variants']['variants']]==['hsd_a','hsd_b','hsd_c']
for name in ['drudge','thrix']:
 result=json.loads((P/f'work/lod_{name}/result.json').read_text());assert result['passed'];report['lods'][name]=result
initial=json.loads((P/'review/gates_initial.json').read_text())['clips'];final=json.loads((P/'review/gates_final.json').read_text())['clips']
all_gates=initial|final
bindings=yaml.safe_load((P/'integration/actors.yml').read_text())
for b in bindings:
 g=Glb(P/'export'/Path(b['model']).name);clips={a['name'] for a in g.json['animations']}
 bound=set(b['clips'].values())|{b['animation']['run']}
 for clip in bound:
  assert clip in clips;r=all_gates[clip]
  assert r['passes_stretch_wrist'] and r['body_floor_range_m'][0]>=-.003,clip
  for side in 'LR':assert r[side+'_hand_in_body_m']['value']<=.001,(clip,side)
  for key,v in r.items():
   if key.endswith('_head_clearance'):assert v['value']>=.005,(clip,key,v)
 for a in b.get('attachments',[]):assert any(n.get('name')==a['node'] for n in g.json['nodes'])
report['gates']={'bound_clips':sorted(set(bindings[0]['clips'].values())|{bindings[0]['animation']['run']}),'all_clips':all_gates,
 'inherited_unbound_warnings':{clip:r for clip,r in initial.items() if clip not in bindings[0]['clips'].values() and (r['body_floor_range_m'][0]<-.003 or max(r[s+'_hand_in_body_m']['value'] for s in 'LR')>.001)}}
manifest=json.loads((P/'review/viewer/manifest.json').read_text())
feedback=json.loads((P/'review/viewer'/manifest['feedback']).read_text())
assert isinstance(feedback,dict) and isinstance(feedback.get('findings'),list), 'Viewer feedback requires a findings array'
for model in manifest['models']:
 path=P/'review/viewer'/model['url'].split('?')[0];assert hashlib.sha256(path.read_bytes()).hexdigest()==model['sha256']
 g=Glb(path);assert set(manifest['clips'])=={a['name'] for a in g.json['animations']}
report['viewer']={'models':len(manifest['models']),'clips_each':len(manifest['clips']),'feedback_schema':'pass','browser_review':'integrator pending'}
(P/'review/validation.json').write_text(json.dumps(report,indent=2)+'\n')
print('VALIDATED: 5 runtime GLBs; unchanged shared LOD0, rig and 18 source clips; 8 bound clips; 5 viewer models; far LOD gates.')
