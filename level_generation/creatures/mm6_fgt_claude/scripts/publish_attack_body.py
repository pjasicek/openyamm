"""Publish only the new lower-body and spine channels; preserve accepted arm timing and appearance."""
from pathlib import Path
import copy,hashlib,json,sys
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'claude_shared'))
from region_variants import read_glb,write_glb
OUT=P/'review/attack_body';VIEW=P/'review/viewer';CLIP='AttackRPG6'
info=json.loads((OUT/'motion_sources.json').read_text())[CLIP]
assert not json.loads((OUT/'body_contacts.json').read_text())[CLIP]
assert not json.loads((OUT/'shoulder_gate.json').read_text())[CLIP]['crossings']
source,source_binary=read_glb(OUT/'motion.glb');new_action=next(a for a in source['animations'] if a['name']==CLIP)
changed=set(info['changed_bones'])
new_channels={(source['nodes'][c['target']['node']]['name'],c['target']['path']):c for c in new_action['channels']}
report={}
for tier in 'abc':
 path=VIEW/f'mm6_fgt_windup_{tier}.glb';doc,raw=read_glb(path);original=copy.deepcopy(doc);binary=bytearray(raw)
 animation=next(a for a in doc['animations'] if a['name']==CLIP);before=copy.deepcopy(animation)
 accessor_map={};view_map={}
 def accessor(index):
  if index in accessor_map:return accessor_map[index]
  a=copy.deepcopy(source['accessors'][index]);assert 'sparse' not in a
  vi=a['bufferView']
  if vi not in view_map:
   v=copy.deepcopy(source['bufferViews'][vi]);start=v.get('byteOffset',0)
   binary.extend(b'\0'*(-len(binary)%4));v['buffer']=0;v['byteOffset']=len(binary)
   binary.extend(source_binary[start:start+v['byteLength']]);view_map[vi]=len(doc['bufferViews']);doc['bufferViews'].append(v)
  a['bufferView']=view_map[vi];accessor_map[index]=len(doc['accessors']);doc['accessors'].append(a)
  return accessor_map[index]
 altered=[]
 for c in animation['channels']:
  key=(doc['nodes'][c['target']['node']]['name'],c['target']['path'])
  if key[0] not in changed or (key[1]!='rotation' and key!=('B_Pelvis','translation')):continue
  nc=new_channels[key];sampler=copy.deepcopy(new_action['samplers'][nc['sampler']])
  times=source['accessors'][sampler['input']]
  assert abs(times['max'][0]-info['duration'])<1e-6
  sampler['input']=accessor(sampler['input']);sampler['output']=accessor(sampler['output'])
  c['sampler']=len(animation['samplers']);animation['samplers'].append(sampler);altered.append(key)
 assert len(altered)==len(changed)+1,(len(altered),changed)
 for old,c in zip(before['channels'],animation['channels']):
  key=(doc['nodes'][c['target']['node']]['name'],c['target']['path'])
  if key not in altered:
   assert c==old and animation['samplers'][c['sampler']]==before['samplers'][old['sampler']]
 target=VIEW/f'mm6_fgt_body_{tier}.glb';write_glb(target,doc,binary)
 check,b=read_glb(target);assert bytes(b[:len(raw)])==bytes(raw)
 for key in ('nodes','meshes','skins','materials','images','textures','samplers'):
  assert check.get(key)==original.get(key),key
 assert [a for a in check['animations'] if a['name']!=CLIP]==[a for a in original['animations'] if a['name']!=CLIP]
 report[tier]={'path':str(target.relative_to(P)),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
  'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'unchanged_clips':12,
  'unchanged_attack_channels':len(animation['channels'])-len(altered),'changed_channels':altered,
  'preserved_binary_bytes':len(raw)}
(OUT/'preservation.json').write_text(json.dumps(report,indent=2)+'\n')
if not (OUT/'manifest_before.json').exists():(OUT/'manifest_before.json').write_bytes((VIEW/'manifest.json').read_bytes())
manifest=json.loads((OUT/'manifest_before.json').read_text());manifest.update(revision='mm6_fgt_attack_body',model='mm6_fgt_body_a.glb',default_clip=CLIP)
for model,tier in zip(manifest['models'],'abc'):
 model.update(url=Path(report[tier]['path']).name+'?v='+report[tier]['sha256'][:12],sha256=report[tier]['sha256'],revision=manifest['revision'])
manifest['clips'][CLIP].update(label='Attack B — weight shift and footwork',provenance='Accepted faster RPG downward swing. Short lead-foot step, hip weight transfer, rear heel pivot and recovery; arm and grip channels retained.')
(VIEW/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
html=VIEW/'index.html';s=html.read_text();s=s.replace('Selected RPG downward swing: 30% shorter windup through original frame 28 at 48 fps. Strike and recovery retain their speed. Running is approved.', 'Selected RPG downward swing with the accepted faster windup, a short preparation step, hip weight transfer and rear-foot pivot on release. Running is approved.')
html.write_text(s)
print(json.dumps(report,indent=2))
