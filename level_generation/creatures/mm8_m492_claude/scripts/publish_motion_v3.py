"""Publish the attack arc while preserving every other clip and all body data."""
from pathlib import Path
import hashlib,json,shutil,sys
P=Path(__file__).resolve().parents[1];BASE=P/'work/before_motion_v3';OUT=P/'review/motion_v3'
sys.path.insert(0,str(P/'scripts'))
from publish_motion_v2 import fingerprint,transplant,read_glb,write_glb
source,binary=read_glb(P/'work/motion_v3_clips.glb');changed=('Attack','Cast');reports=[]
for animation in source['animations']:
 animation['channels']=[c for c in animation['channels'] if not source['nodes'][c['target']['node']].get('name','').startswith('MouthFire')]
for record in json.loads((P/'review/motion_v2/preservation.json').read_text()):
 path=BASE/record['path']
 doc,data=read_glb(path);kept=['geometry']+[a['name'] for a in doc['animations'] if a['name'] not in changed]
 before={name:fingerprint(doc,data,name) for name in kept}
 doc,data=transplant(doc,bytearray(data),source,binary,changed)
 assert before=={name:fingerprint(doc,data,name) for name in kept},path
 for name in changed:assert fingerprint(doc,data,name)==fingerprint(source,binary,name)
 dest=P/path.relative_to(BASE);write_glb(dest,doc,data)
 reports.append({'path':str(dest.relative_to(P)),'preserved':before,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()})
assert len(reports)==6
shutil.copy2(P/'work/motion_v3.blend',P/'dragon_master.blend')
(OUT/'preservation.json').write_text(json.dumps(reports,indent=2)+'\n')
v=P/'review/viewer/manifest.json';m=json.loads(v.read_text());m.update(revision='motion-v3',default_clip='Attack')
for model in m['models']:
 name=model['url'].split('?')[0];sha=hashlib.sha256((v.parent/name).read_bytes()).hexdigest();model.update(url=name+'?v='+sha[:12],sha256=sha,revision='motion-v3')
for name in changed:m['clips'][name]['provenance']='Single upper-left to lower-right head sweep; hold the strike side through the rise, then settle to centre. Gameplay release remains 1.25s.'
v.write_text(json.dumps(m,indent=2)+'\n');print('Published motion-v3; Hit, Death, other clips and body data preserved.')
