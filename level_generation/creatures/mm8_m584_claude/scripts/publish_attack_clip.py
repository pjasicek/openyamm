"""Patch only Attack buffers; retain the accepted mesh, LODs, textures and five other clips."""
from pathlib import Path
import copy,hashlib,json,shutil,sys
import numpy as np
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2];sys.path.insert(0,str(ROOT/'tools'))
from merge_head_material import read_glb,write_glb,accessor_array
W=P/'work/attack_revision_1';sd,sb=read_glb(W/'attack_source.glb')
source=next(a for a in sd['animations'] if a['name']=='Attack')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
report=[]
paths=[P/'export'/n for n in ('raven_runtime_lod0_raw.glb','raven_prepared.glb','raven_lods.glb','raven_variants.glb','raven_materials.glb','raven_body.glb','mm8_m584.glb')]+[P/f'review/viewer/raven_{t}.glb' for t in 'abc']
for p in paths:
 backup=W/'glb_baseline'/p.name;backup.parent.mkdir(exist_ok=True)
 if not backup.exists():shutil.copyfile(p,backup)
 d,b=read_glb(backup);original=copy.deepcopy(d);original_binary=bytes(b)
 nodes={n['name']:i for i,n in enumerate(d['nodes']) if 'name' in n}
 mapping={i:nodes[n['name']] for i,n in enumerate(sd['nodes']) if n.get('name') in nodes}
 old=next(a for a in d['animations'] if a['name']=='Attack');new=copy.deepcopy(source);cache={}
 for sampler in new['samplers']:
  for key in ('input','output'):
   idx=sampler[key]
   if idx not in cache:
    a=copy.deepcopy(sd['accessors'][idx]);values=accessor_array(sd,sb,idx);packed=np.ascontiguousarray(values).tobytes()
    b.extend(b'\0'*(-len(b)%4));view={'buffer':0,'byteOffset':len(b),'byteLength':len(packed)};b.extend(packed)
    d['bufferViews'].append(view);a.pop('byteOffset',None);a['bufferView']=len(d['bufferViews'])-1
    d['accessors'].append(a);cache[idx]=len(d['accessors'])-1
   sampler[key]=cache[idx]
 for c in new['channels']:
  si=c['target']['node'];di=mapping[si]
  for key in ('matrix','translation','rotation','scale'):
   assert sd['nodes'][si].get(key)==d['nodes'][di].get(key),(p,key,sd['nodes'][si]['name'])
  c['target']['node']=di
 d['animations'][d['animations'].index(old)]=new
 assert bytes(b[:len(original_binary)])==original_binary
 for key in ('nodes','meshes','skins','materials','textures','images','extensions'):
  assert d.get(key)==original.get(key),(p,key)
 assert [a for a in d['animations'] if a['name']!='Attack']==[a for a in original['animations'] if a['name']!='Attack']
 assert abs(max(float(accessor_array(d,b,s['input']).max()) for s in new['samplers'])-35/30)<1e-6
 write_glb(p,d,b)
 report.append({'path':str(p.relative_to(P)),'before_sha256':sha(backup),'after_sha256':sha(p),'static_data_and_five_other_clips_identical':True,'original_binary_prefix_identical':True})
(W/'export_preservation.json').write_text(json.dumps(report,indent=2)+'\n')
mfile=P/'review/viewer/manifest.json';m=json.loads(mfile.read_text());m['revision']='raven_attack_diagonal_v3';m['default_clip']='Attack'
for row in m['models']:
 p=P/'review/viewer'/f"{row['id']}.glb";row.update(revision=m['revision'],sha256=sha(p),url=f'{p.name}?v={sha(p)[:12]}')
m['clips']['Attack']['provenance']='Body-led right-high to left-low slash; backward anticipation, fast diagonal release and forward follow-through. Impact 26/30 seconds.'
m['clips']['Attack']['anchors']=[{'time':t,'label':label,'phase':phase,'source_images':['../../native/native_a_v0_matte.png']} for t,label,phase in ((.65,'Wind-up','Lean back and coil to the right.'),(26/30,'Slash','Drive across the body to the left.'),(.98,'Follow-through','Carry the shoulders forward through the cut.'))]
mfile.write_text(json.dumps(m,indent=2)+'\n')
p=P/'work/package_check.json';data=json.loads(p.read_text());data['mm8_m584.glb']['sha256']=sha(P/'export/mm8_m584.glb');p.write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps(report,indent=2))
