"""Replace only changed animation streams; preserve accepted geometry, materials and LOD weights."""
import sys,copy,json,hashlib,runpy,shutil
from pathlib import Path
import numpy as np
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'))
from merge_head_material import read_glb,write_glb,accessor_array,compact
from scipy.spatial import cKDTree
weights=json.loads((P/'work/round3_weight_changes.json').read_text());co=np.array(weights['positions']);co=co[:,[0,2,1]];co[:,2]*=-1;tree=cKDTree(co);mask=set(weights['vertices'])
source=P/'work/round3_animation.glb'
shutil.copy2(P/'export/mm6_dwa1_lod0.glb',source)
s,sb=read_glb(source);changed={'Walking','Running'};evidence={}
def patch(base,dest):
 d,b=read_glb(base);old=copy.deepcopy(d);ob=bytes(b);nodes={n['name']:i for i,n in enumerate(d['nodes'])if 'name'in n};cache={}
 def acc(i):
  if i in cache:return cache[i]
  a=copy.deepcopy(s['accessors'][i]);v=s['bufferViews'][a['bufferView']];assert 'sparse'not in a
  data=accessor_array(s,sb,i).tobytes();b.extend(bytes(-len(b)%4));a['bufferView']=len(d['bufferViews']);a.pop('byteOffset',None)
  d['bufferViews'].append({'buffer':0,'byteOffset':len(b),'byteLength':len(data)});b.extend(data)
  cache[i]=len(d['accessors']);d['accessors'].append(a);return cache[i]
 for k,a in enumerate(d['animations']):
  if a['name']not in changed:continue
  new=copy.deepcopy(next(x for x in s['animations']if x['name']==a['name']))
  for channel in new['channels']:
   sn=s['nodes'][channel['target']['node']];ni=nodes[sn['name']];dn=d['nodes'][ni]
   for key,default in [('translation',[0,0,0]),('rotation',[0,0,0,1]),('scale',[1,1,1])]:assert np.allclose(sn.get(key,default),dn.get(key,default),atol=1e-5),(sn['name'],key)
   channel['target']['node']=ni
  for sampler in new['samplers']:
   sampler['input']=acc(sampler['input']);sampler['output']=acc(sampler['output'])
  d['animations'][k]=new
 # Only explicit authoring-mask vertices change; all accepted positions, UVs and topology stay byte-identical.
 joints={d['nodes'][ni]['name']:i for i,ni in enumerate(d['skins'][0]['joints'])};count=0
 for mesh in d['meshes']:
  for q in mesh['primitives']:
   attrs=q['attributes'];pos=accessor_array(d,b,attrs['POSITION']);dist,nn=tree.query(pos)
   selected=[i for i,j in enumerate(nn)if j in mask and dist[i]<1e-5]
   for semantic in ['WEIGHTS_0','JOINTS_0']:
    ai=attrs[semantic];array=accessor_array(d,b,ai).copy()
    for i in selected:
     entries=sorted(weights['weights'][int(nn[i])].items(),key=lambda x:-x[1])[:4];array[i]=0
     for k,(n,w)in enumerate(entries):array[i,k]=w if semantic=='WEIGHTS_0' else joints[n]
    accessor=d['accessors'][ai];view=d['bufferViews'][accessor['bufferView']];offset=view.get('byteOffset',0)+accessor.get('byteOffset',0);assert not view.get('byteStride');b[offset:offset+array.nbytes]=array.tobytes()
   count+=len(selected)
 assert count>500,count
 for om,nm in zip(old['meshes'],d['meshes']):
  assert om==nm
  for q in om['primitives']:
   for i in [q['indices'],*[v for k,v in q['attributes'].items()if not k.startswith(('WEIGHTS_','JOINTS_'))]]:assert np.array_equal(accessor_array(old,ob,i),accessor_array(d,b,i))
 write_glb(dest,*compact(d,b));evidence[str(dest.relative_to(P))]={'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'geometry':'exact'}
backup=P/'work/round3_before'
for rel in ['export/mm6_dwa1_lod0.glb','export/mm6_dwa1_runtime_lod0.glb']:patch(backup/rel,P/rel)
(P/'review/round3/lod0_package.json').write_text(json.dumps({'changed_clips':sorted(changed),'files':evidence},indent=2)+'\n')
