"""Stage animation-only viewer variants; retain accepted appearance and previous clips."""
from pathlib import Path
import copy, hashlib, json, sys, struct
import numpy as np
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parent/'claude_shared'))
from region_variants import read_glb, write_glb
OPTIONS='--attack-options' in sys.argv
out=P/('review/attack_options' if OPTIONS else 'review/motion_preview'); viewer=P/'review/viewer'
revision='mm6_fgt_attack_options' if OPTIONS else 'mm6_fgt_motion_preview'
source,source_binary=read_glb(out/'motion.glb')
source_joints={i for skin in source['skins'] for i in skin['joints']}
metadata=json.loads((out/'motion_sources.json').read_text())
if OPTIONS:
 selected={'AttackRPG5','AttackRPG6','AttackOutward'}
 source['animations']=[a for a in source['animations'] if a['name'] in selected]
 metadata={n:info for n,info in metadata.items() if n in selected}
 contacts=json.loads((out/'body_contacts.json').read_text())
 shoulders=json.loads((out/'shoulder_gate.json').read_text())
 assert set(metadata)==selected
 assert all(not contacts[n] and not shoulders[n]['crossings'] for n in selected)
manifest=json.loads((viewer/'manifest.json').read_text())
if not (out/'manifest_before.json').exists():
 (out/'manifest_before.json').write_text(json.dumps(manifest,indent=2)+'\n')
manifest=json.loads((out/'manifest_before.json').read_text())
report={}
for tier in 'abc':
 path=viewer/(f'mm6_fgt_motion_{tier}.glb' if OPTIONS else f'mm6_fgt_{tier}.glb');doc,binary=read_glb(path)
 original=copy.deepcopy(doc);old_binary=bytes(binary);binary=bytearray(binary)
 modified=set();changes=[];fit={'standing_max_error_m':0}
 if not OPTIONS:
  fit=json.loads((out/'shoulder_fit.json').read_text());changes=fit['changes']
  before=np.array([[c['before'][0],c['before'][2],-c['before'][1]] for c in changes])
  modified=set();seen=set();matched=set()
  def access(index):
   a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']]
   components={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
   fmt={5121:'B',5123:'H',5126:'f'}[a['componentType']]
   size=struct.calcsize('<'+fmt)*components
   return a,v.get('byteOffset',0)+a.get('byteOffset',0),v.get('byteStride',size),fmt,components
  def put(index,vertex,values):
   a,start,stride,fmt,components=access(index);offset=start+stride*vertex
   data=struct.pack('<'+fmt*components,*values);binary[offset:offset+len(data)]=data
   modified.update(range(offset,offset+len(data)))
  for node in doc['nodes']:
   if 'mesh' not in node or 'skin' not in node:continue
   joints=doc['skins'][node['skin']]['joints'];bone_index={doc['nodes'][j]['name']:i for i,j in enumerate(joints)}
   for primitive in doc['meshes'][node['mesh']]['primitives']:
    attrs=primitive['attributes']
    if 'JOINTS_0' not in attrs:continue
    a,start,stride,fmt,components=access(attrs['POSITION'])
    positions=np.ndarray((a['count'],3),dtype='<f4',buffer=old_binary,offset=start,strides=(stride,4))
    for ci,change in enumerate(changes):
     ids=np.where(np.linalg.norm(positions-before[ci],axis=1)<2e-6)[0]
     for vi in ids:
      key=(attrs['POSITION'],int(vi))
      if key in seen:continue
      seen.add(key);matched.add(ci)
      x,y,z=change['after'];put(attrs['POSITION'],int(vi),(x,z,-y))
      if 'NORMAL' in attrs:
       x,y,z=change['normal'];put(attrs['NORMAL'],int(vi),(x,z,-y))
      weights=list(change['weights'].items());weights+= [(weights[0][0],0)]*(4-len(weights))
      put(attrs['JOINTS_0'],int(vi),[bone_index[n] for n,w in weights])
      put(attrs['WEIGHTS_0'],int(vi),[w for n,w in weights])
  assert len(matched)==len(changes),(len(matched),len(changes))
 target_joints={i for skin in doc['skins'] for i in skin['joints']}
 node_map={i:next(j for j in target_joints if doc['nodes'][j]['name']==source['nodes'][i]['name']) for i in source_joints}
 accessors={};views={}
 def accessor(index):
  if index in accessors:return accessors[index]
  value=copy.deepcopy(source['accessors'][index]); assert 'sparse' not in value
  vi=value['bufferView']
  if vi not in views:
   v=copy.deepcopy(source['bufferViews'][vi]); start=v.get('byteOffset',0)
   data=source_binary[start:start+v['byteLength']]
   binary.extend(b'\0'*(-len(binary)%4));v['byteOffset']=len(binary);v['buffer']=0
   binary.extend(data);views[vi]=len(doc['bufferViews']);doc['bufferViews'].append(v)
  value['bufferView']=views[vi];accessors[index]=len(doc['accessors']);doc['accessors'].append(value)
  return accessors[index]
 for animation in source['animations']:
  name=animation['name']
  if not OPTIONS:
   old=next(a for a in doc['animations'] if a['name']==name)
   old['name']=name+'Previous'
  else:assert name not in [a['name'] for a in doc['animations']]
  new=copy.deepcopy(animation)
  for sampler in new['samplers']:
   sampler['input']=accessor(sampler['input']);sampler['output']=accessor(sampler['output'])
  for channel in new['channels']:channel['target']['node']=node_map[channel['target']['node']]
  doc['animations'].append(new)
 target=viewer/(f'mm6_fgt_attacks_{tier}.glb' if OPTIONS else f'mm6_fgt_motion_{tier}.glb');write_glb(target,doc,binary)
 check,raw=read_glb(target)
 assert all(a==b or i in modified for i,(a,b) in enumerate(zip(raw[:len(old_binary)],old_binary)))
 for key in ('nodes','meshes','skins','materials','images','textures','samplers'):
  assert check.get(key)==original.get(key),key
 for old in original['animations']:
  name=old['name']+('Previous' if not OPTIONS and old['name'] in metadata else '')
  new=copy.deepcopy(next(a for a in check['animations'] if a['name']==name));new['name']=old['name']
  assert new==old,old['name']
 sha=hashlib.sha256(target.read_bytes()).hexdigest()
 model=manifest['models']['abc'.index(tier)]
 model.update(url=target.name+'?v='+sha[:12],sha256=sha,revision=revision)
 report[tier]={'sha256':sha,'preserved_original_binary_bytes':len(old_binary)-len(modified),'shoulder_vertices_updated':len(changes),'standing_max_error_m':fit['standing_max_error_m'],'unchanged_existing_animations':len(original['animations'])}
labels={'AttackRPG5':'Attack A — RPG rising swing', 'AttackRPG6':'Attack B — RPG downward swing',
        'AttackInward':'Attack C — Mixamo inward slash', 'AttackOutward':'Attack C — Mixamo outward slash'}
for name,info in metadata.items():
 if OPTIONS:
  manifest['clips'][name]=copy.deepcopy(manifest['clips']['Attack'])
  manifest['clips'][name].update(duration=info['duration'],label=labels[name],provenance=info['clip']+'; upright planted stance, source swing at 30 fps. Audition.')
  continue
 old=copy.deepcopy(manifest['clips'][name]);old['label']=name+' — previous';manifest['clips'][name+'Previous']=old
 manifest['clips'][name].update(duration=info['duration'],label=name+' — upright preview',provenance=(info['clip']+'; fitted Thug rig and retained mace grip. Viewer preview.'))
manifest.update(revision=revision,model=('mm6_fgt_attacks_a.glb' if OPTIONS else 'mm6_fgt_motion_a.glb'),default_clip=('AttackRPG6' if OPTIONS else 'Running'))
if OPTIONS:
 manifest['clips']['Running']['label']='Running — approved'
 manifest['clips']['Attack']['label']='Attack — earlier Mixamo preview'
(viewer/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(out/'preservation.json').write_text(json.dumps(report,indent=2)+'\n')
html=viewer/'index.html';s=html.read_text().replace('<title>MM6 Goblin v2 review</title>','<title>MM6 Thug motion review</title>')
s=s.replace('Source-frame rig, fitted hands, solved mace grip and native backhand attack. Backward death with a released mace. Native sprites are shown beside each animation.', 'Motion preview: upright run and standing horizontal mace attack. Select the previous clips to compare. Standing appearance and remaining animations are retained; shoulder attachment fitted for the wider sweep.')
if OPTIONS:
 s=s.replace('Motion preview: upright run and standing horizontal mace attack. Select the previous clips to compare. Standing appearance and remaining animations are retained; shoulder attachment fitted for the wider sweep.', 'Attack auditions from the RPG and updated Mixamo libraries. Running is approved. Select attacks A–C to compare their standing swings; earlier attacks remain available.')
html.write_text(s)
print(json.dumps(report,indent=2))
