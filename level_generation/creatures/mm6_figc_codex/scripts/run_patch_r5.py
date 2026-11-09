import sys,json,copy,hashlib,numpy as np
from pathlib import Path
from scipy.spatial.transform import Rotation
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P.parents[2]/'tools'))
from build_actor_lods import read_glb,write_glb,append_accessor,accessor_bytes
from merge_head_material import accessor_array
s=json.loads((P/'work/round5/running_world.json').read_text());C=np.array([[1,0,0,0],[0,0,1,0],[0,-1,0,0],[0,0,0,1.]])
def matrix(n):
 m=np.eye(4);m[:3,:3]=Rotation.from_quat(n.get('rotation',[0,0,0,1])).as_matrix()@np.diag(n.get('scale',[1]*3));m[:3,3]=n.get('translation',[0]*3);return m
paths=['export/mm6_figc.glb','export/mm6_figc_lod0.glb','export/mm6_figc_portable.glb']+[f'review/viewer/mm6_figc_{t}.glb' for t in 'abc']
proof={}
for path in paths:
 d,b=read_glb(P/'review/round5/before'/path);orig=copy.deepcopy(d);b=bytearray(b);original=bytes(b)
 parents={c:i for i,n in enumerate(d['nodes'])for c in n.get('children',[])};rest={}
 def globalrest(i):
  if i not in rest:rest[i]=(globalrest(parents[i])if i in parents else np.eye(4))@matrix(d['nodes'][i])
  return rest[i]
 for i,n in enumerate(d['nodes']):
  if n.get('name') in s['rest']:assert np.max(abs(globalrest(i)-C@np.array(s['rest'][n['name']])))<1e-5,(n['name'],globalrest(i),C@np.array(s['rest'][n['name']]))
 a=next(a for a in d['animations']if a['name']=='Running');ti=append_accessor(d,b,{'componentType':5126,'type':'SCALAR','count':97,'min':[0.0],'max':[.8]},np.array(s['times'],dtype='<f4').tobytes());samplers=[];channels=[]
 for ch in a['channels']:
  i=ch['target']['node'];n=d['nodes'][i]['name'];kind=ch['target']['path']
  if n not in s['rest'] or kind=='scale':
   sam=copy.deepcopy(a['samplers'][ch['sampler']]);arr=accessor_array(d,b,sam['output']).copy();arr[-1]=arr[0];sam['output']=append_accessor(d,b,d['accessors'][sam['output']],arr.tobytes());channels.append(dict(ch,sampler=len(samplers)));samplers.append(sam);continue
  vals=[]
  for pose in s['poses']:
   par=parents.get(i);pn=d['nodes'][par].get('name')if par is not None else None
   pm=C@np.array(pose[pn])if pn in pose else (globalrest(par)if par is not None else np.eye(4))
   m=np.linalg.inv(pm)@C@np.array(pose[n])
   v=m[:3,3]if kind=='translation'else Rotation.from_matrix(m[:3,:3]).as_quat()
   if kind=='rotation'and vals and np.dot(v,vals[-1])<0:v=-v
   vals.append(v)
  vals[-1]=vals[0];arr=np.array(vals,dtype='<f4');ai=append_accessor(d,b,{'componentType':5126,'type':'VEC3'if kind=='translation'else 'VEC4','count':97},arr.tobytes())
  channels.append(dict(ch,sampler=len(samplers)));samplers.append({'input':ti,'output':ai,'interpolation':'LINEAR'})
 a['samplers']=samplers;a['channels']=channels
 # Original payload stays intact; only Running references newly appended arrays.
 assert bytes(b[:len(original)])==original
 for key in ['meshes','nodes','skins','materials','images','textures']:assert d.get(key)==orig.get(key)
 for old,new in zip(orig['animations'],d['animations']):
  if old['name']!='Running':assert old==new
 write_glb(P/path,d,b)
 proof[path]={'before':hashlib.sha256((P/'review/round5/before'/path).read_bytes()).hexdigest(),'after':hashlib.sha256((P/path).read_bytes()).hexdigest(),'original_binary_payload_preserved':True,'non_running_animation_definitions_preserved':True,'loop_end_equals_start':True}
for path in ['export/mm6_figc_axe.glb','export/mm6_figc_shield.glb','integration/actors.yml']:
 assert (P/path).read_bytes()==(P/'review/round5/before'/path).read_bytes();proof[path]={'unchanged':True,'sha256':hashlib.sha256((P/path).read_bytes()).hexdigest()}
(P/'review/round5/artifact_parity.json').write_text(json.dumps(proof,indent=2))
f=P/'review/viewer/manifest.json';m=json.loads(f.read_text());m.update(revision='mm6_figc_codex_review5',runtime_artifact_sha256=proof[paths[0]]['after'])
for row in m['models']:
 path=P/'review/viewer'/f"mm6_{row['id']}.glb";h=hashlib.sha256(path.read_bytes()).hexdigest();row.update(sha256=h,url=path.name+'?v='+h[:12],revision='mm6_figc_codex_review5')
f.write_text(json.dumps(m,indent=2)+'\n')
print('Running patched; all prior binary payloads and other clips preserved',proof[paths[0]]['after'])
