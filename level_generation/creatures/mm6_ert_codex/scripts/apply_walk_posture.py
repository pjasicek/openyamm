"""Replace seven Walking rotation tracks, preserving every other glTF byte and track."""
import json,struct,hashlib,shutil
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1];out=P/'review/walk_posture_v2'
names=set(json.loads((out/'correction.json').read_text())['bones'])
assert json.loads((out/'deformation_audit.json').read_text())['unchanged_other_clips']==6

def read(path):
 raw=path.read_bytes();n=struct.unpack_from('<I',raw,12)[0];assert len(raw)==struct.unpack_from('<I',raw,8)[0]
 return raw,json.loads(raw[20:20+n]),28+n

def channels(doc):
 a=next(a for a in doc['animations'] if a['name']=='Walking')
 return {(doc['nodes'][c['target']['node']]['name'],c['target']['path']):(a['samplers'][c['sampler']],doc['nodes'][c['target']['node']]) for c in a['channels']}

def span(doc,base,index):
 a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']]
 size={'SCALAR':1,'VEC4':4}[a['type']]*4;assert a['componentType']==5126 and v.get('byteStride',size)==size and 'sparse' not in a
 start=base+v.get('byteOffset',0)+a.get('byteOffset',0);return start,start+a['count']*size

raw,src,base=read(out/'candidate.glb');sc=channels(src);report=[]
paths=sorted((P/'export').glob('*.glb'))+[P/f'review/viewer/mm6_ert_{tier}.glb' for tier in 'abc']+[Path('assets_dev/worlds/mm6/models/mm6_ert.glb')]
for path in paths:
 original,doc,offset=read(path)
 if not doc.get('animations'):continue
 dc=channels(doc);result=bytearray(original);changed=[]
 for n in sorted(names):
  ss,sn=sc[n,'rotation'];ds,dn=dc[n,'rotation']
  for k in ['translation','rotation','scale','matrix']:assert sn.get(k)==dn.get(k),(path,n,'bind pose changed')
  s0,s1=span(src,base,ss['input']);d0,d1=span(doc,offset,ds['input']);assert raw[s0:s1]==original[d0:d1],(path,n,'time changed')
  s0,s1=span(src,base,ss['output']);d0,d1=span(doc,offset,ds['output']);assert s1-s0==d1-d0
  for action in doc['animations']:
   for ch in action['channels']:
    sm=action['samplers'][ch['sampler']]
    if sm['output']==ds['output']:assert action['name']=='Walking' and doc['nodes'][ch['target']['node']]['name']==n
  result[d0:d1]=raw[s0:s1];changed.append((d0,d1))
 restored=bytearray(result)
 for a,b in changed:restored[a:b]=original[a:b]
 assert restored==original
 path.write_bytes(result);assert path.read_bytes()==result
 report.append({'path':str(path),'replaced_tracks':len(changed),'sha256':hashlib.sha256(result).hexdigest(),'unrelated_bytes_unchanged':True})
shutil.copy2(out/'candidate.blend',P/'export/mm6_ert.blend')
m= P/'review/viewer/manifest.json';manifest=json.loads(m.read_text());manifest['revision']='ert_walk_posture_v2'
for model in manifest['models']:
 file=P/'review/viewer'/('mm6_'+model['id']+'.glb');model.update(revision='ert_walk_posture_v2',sha256=hashlib.sha256(file.read_bytes()).hexdigest(),url=file.name+'?v=walk_posture_v2')
manifest['model_sha256']=manifest['models'][0]['sha256'];manifest['clips']['Walking']['provenance']='Owned heavy walk; shoulder/spine posture corrected to the idle silhouette, unchanged gait and 2.675 m stride'
m.write_text(json.dumps(manifest,indent=2)+'\n')
shutil.copytree('/tmp/ert-walk-before',out/'viewer_before',dirs_exist_ok=True)
(out/'animation_patch.json').write_text(json.dumps(report,indent=2));print('PATCHED',len(report),'GLBs; only seven Walking rotation tracks changed.')
