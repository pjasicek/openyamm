"""Replace three clips without rebuilding the already-reviewed geometry, textures or far LODs."""
import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT.parents[2]/'tools'))
from build_actor_lods import read_glb,write_glb

CLIPS={'Bite','Pounce','Hit'}
src,sbin=read_glb(PROJECT/'export/hes_hound_raw.glb')
doc,binary=read_glb(PROJECT/'work/before_motion_v2/export/hes_hound.glb')
before=copy.deepcopy(doc)
original=binary
binary=bytearray(binary)
nodes={n.get('name'):i for i,n in enumerate(doc['nodes'])}

def data(d,b,index):
    a=d['accessors'][index];v=d['bufferViews'][a['bufferView']]
    assert a['componentType']==5126 and 'byteStride' not in v
    count={'SCALAR':1,'VEC3':3,'VEC4':4}[a['type']]
    offset=v.get('byteOffset',0)+a.get('byteOffset',0)
    return np.frombuffer(b,'<f4',a['count']*count,offset).reshape(a['count'],count),a['type']

def append(values,kind):
    binary.extend(b'\0'*(-len(binary)%4));raw=values.astype('<f4').tobytes()
    doc['bufferViews'].append(dict(buffer=0,byteOffset=len(binary),byteLength=len(raw)));binary.extend(raw)
    a=dict(bufferView=len(doc['bufferViews'])-1,componentType=5126,count=len(values),type=kind)
    if kind=='SCALAR':a.update(min=values.min(0).tolist(),max=values.max(0).tolist())
    doc['accessors'].append(a)
    return len(doc['accessors'])-1

for n in src['nodes']:
    if n.get('name') in nodes and 'mesh' not in n:
        old=doc['nodes'][nodes[n['name']]]
        for key,default in [('translation',[0,0,0]),('rotation',[0,0,0,1]),('scale',[1,1,1])]:
            assert np.allclose(n.get(key,default),old.get(key,default),atol=1e-5),(n['name'],key)
report={}
for name in sorted(CLIPS):
    a=next(a for a in src['animations'] if a['name']==name)
    target=next(a for a in doc['animations'] if a['name']==name)
    samplers=[];channels=[];duration=0.
    for channel in a['channels']:
        joint=src['nodes'][channel['target']['node']]['name'];sampler=a['samplers'][channel['sampler']]
        time,_=data(src,sbin,sampler['input']);values,kind=data(src,sbin,sampler['output'])
        duration=max(duration,float(time[-1,0]))
        samplers.append(dict(input=append(time,'SCALAR'),output=append(values,kind),
                             interpolation=sampler.get('interpolation','LINEAR')))
        channels.append(dict(sampler=len(samplers)-1,target=dict(node=nodes[joint],path=channel['target']['path'])))
    old_channels={(c['target']['node'],c['target']['path']) for c in target['channels']}
    assert old_channels=={(c['target']['node'],c['target']['path']) for c in channels}
    target.update(channels=channels,samplers=samplers)
    report[name]=dict(duration=duration,channels=len(channels))

# Existing meshes, material variants, images, skeleton and the other six clips keep their exact data.
assert bytes(binary[:len(original)])==original
for key in ['meshes','materials','textures','images','skins','nodes']:
    assert doc[key]==before[key],key
for old,new in zip(before['animations'],doc['animations']):
    if old['name'] not in CLIPS:assert old==new,old['name']
path=PROJECT/'export/hes_hound.glb'
write_glb(path,doc,bytes(binary))
subprocess.run([sys.executable,str(PROJECT/'scripts/compact_glb.py'),str(path),str(path)],check=True)
report['preserved']='All geometry, skin weights, materials, images, far LODs and the other six clips'
report['runtime_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
(PROJECT/'review/motion_v2_preservation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
