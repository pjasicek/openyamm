"""Replace only Walking channels, preserving every mesh/map and accepted clip byte-for-byte."""
import sys,json,copy,hashlib
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P.parents[2]/'tools'))
from build_actor_lods import read_glb,write_glb,append_accessor,accessor_bytes
base=P/'review/round6/baseline';samples=json.loads((P/'work/round6/walking_local.json').read_text());times=list(map(float,samples));rows=list(samples.values());receipt={}
def clip_bytes(d,b,a):
 return {(d['nodes'][c['target']['node']]['name'],c['target']['path']):tuple(accessor_bytes(d,b,a['samplers'][c['sampler']][k])for k in ['input','output'])for c in a['channels']}
for folder in ['export','review/viewer']:
 for old in (base/folder).glob('*.glb'):
  d,b=read_glb(old);walk=next((a for a in d.get('animations',[])if a['name']=='Walking'),None)
  if not walk:continue
  old_clips={a['name']:clip_bytes(d,b,a)for a in d['animations']if a['name']!='Walking'}
  blob=bytearray(b);ti=append_accessor(d,blob,{'componentType':5126,'type':'SCALAR','count':len(times),'min':[0.],'max':[.8]},np.array(times,dtype='<f4').tobytes())
  for c in walk['channels']:
   name=d['nodes'][c['target']['node']]['name'];kind=c['target']['path']
   if name not in rows[0]:continue
   arr=np.array([r[name][kind]for r in rows],dtype='<f4')
   if kind=='rotation':
    for i in range(1,len(arr)):
     if np.dot(arr[i-1],arr[i])<0:arr[i]*=-1
   idx=append_accessor(d,blob,{'componentType':5126,'type':'VEC4'if kind=='rotation'else'VEC3','count':len(arr)},arr.tobytes())
   c['sampler']=len(walk['samplers']);walk['samplers'].append({'input':ti,'output':idx,'interpolation':'LINEAR'})
  for a in d['animations']:
   if a['name']!='Walking':assert clip_bytes(d,blob,a)==old_clips[a['name']]
  target=P/folder/old.name;write_glb(target,d,blob)
  receipt[str(target.relative_to(P))]={'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'bytes':target.stat().st_size,'other_clips_identical':True,'existing_binary_prefix_identical':bytes(blob[:len(b)])==b}
(P/'review/round6/exports.json').write_text(json.dumps(receipt,indent=2))
m=json.loads((base/'review/viewer/manifest.json').read_text());m['revision']='mm6_lzd_codex_round6';m['model_sha256']=receipt['review/viewer/mm6_lzd_a.glb']['sha256']
for item in m['models']:
 filename=item['url'].split('?')[0];h=receipt['review/viewer/'+filename]['sha256'];item.update(revision=m['revision'],sha256=h,url=filename+'?v='+h[:12])
m['clips']['Walking']['provenance']='Accepted foot trajectory; smooth two-step pelvis bob and 25 degree shoulder counter-swing.'
(P/'review/viewer/manifest.json').write_text(json.dumps(m,indent=2))
print(json.dumps(receipt,indent=2))
