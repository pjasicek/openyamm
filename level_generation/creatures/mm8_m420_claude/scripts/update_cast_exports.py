"""Replace only Attack/Cast samplers; retain exact delivered geometry, materials and seven other clips."""
import copy,hashlib,json,sys
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'claude_shared'));import region_variants as R
base=P/'review/dual_cast/baseline';source,sbin=R.read_glb(P/'export/mm8_m420_prepared.glb')
report={}
for path in ['export/mm8_m420.glb',*[str(f.relative_to(base)) for f in (base/'review/viewer').glob('mm8_*.glb')]]:
 doc,raw=R.read_glb(base/path);original=copy.deepcopy(doc);binary=bytearray(raw);nodes={n.get('name'):i for i,n in enumerate(doc['nodes'])};acmap={};bvmap={}
 def accessor(idx):
  if idx in acmap:return acmap[idx]
  a=copy.deepcopy(source['accessors'][idx]);assert 'sparse' not in a;vi=a['bufferView']
  if vi not in bvmap:
   v=copy.deepcopy(source['bufferViews'][vi]);assert v.get('buffer',0)==0;start=v.get('byteOffset',0);data=sbin[start:start+v['byteLength']]
   binary.extend(b'\0'*(-len(binary)%4));v['byteOffset']=len(binary);binary.extend(data);bvmap[vi]=len(doc['bufferViews']);doc['bufferViews'].append(v)
  a['bufferView']=bvmap[vi];acmap[idx]=len(doc['accessors']);doc['accessors'].append(a);return acmap[idx]
 for role in ['Attack','Cast']:
  src=next(x for x in source['animations'] if x['name']==role);a=copy.deepcopy(src)
  for sampler in a['samplers']:
   for k in ['input','output']:sampler[k]=accessor(sampler[k])
  for channel in a['channels']:
   si=channel['target']['node'];name=source['nodes'][si]['name'];assert name in nodes,name;di=nodes[name]
   for key,default in [('translation',[0,0,0]),('rotation',[0,0,0,1]),('scale',[1,1,1])]:assert np.max(abs(np.array(source['nodes'][si].get(key,default))-np.array(doc['nodes'][di].get(key,default))))<1e-6,(name,key)
   assert 'matrix' not in source['nodes'][si] and 'matrix' not in doc['nodes'][di]
   channel['target']['node']=di
  target=next(i for i,x in enumerate(doc['animations']) if x['name']==role);doc['animations'][target]=a
 for key in ['meshes','materials','textures','images','skins','nodes','extensions']:assert doc.get(key)==original.get(key),key
 assert binary[:len(raw)]==raw
 for a in original['animations']:
  if a['name'] not in ['Attack','Cast']:assert next(x for x in doc['animations'] if x['name']==a['name'])==a
 out=P/path;R.write_glb(out,doc,binary)
 report[path]={'baseline_sha256':hashlib.sha256((base/path).read_bytes()).hexdigest(),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'changed_clips':['Attack','Cast'],'preserved':'Exact meshes, skin, nodes, material/image payloads, seven unrelated clips and original binary buffer','added_bytes':len(binary)-len(raw)}
man=json.loads((P/'review/viewer/manifest.json').read_text());man['revision']='m420_dual_cast_v7'
for model in man['models']:
 model['revision']=man['revision'];model['sha256']=hashlib.sha256((P/'review/viewer'/model['url']).read_bytes()).hexdigest()
for name in ['Attack','Cast']:
 man['clips'][name]['duration']=1.75;man['clips'][name]['provenance']='Whole-body channel into release: hips lower, knees flex and torso turns with both arms; right staff grip and open left palm, 1.25 s release.'
(P/'review/viewer/manifest.json').write_text(json.dumps(man,indent=2)+'\n')
(P/'review/dual_cast/export_preservation.json').write_text(json.dumps(report,indent=2)+'\n')
print('Updated two clips in',len(report),'GLBs; all other payloads preserved.')
