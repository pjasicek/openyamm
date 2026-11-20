"""Runtime contract and preservation checks; no game launch."""
import sys,json,io,hashlib
from pathlib import Path
import numpy as np
from PIL import Image
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p.parents[2]/'tools'));import build_actor_lods as G
file=p/'export/mm6_mnk1.glb';doc,buf=G.read_glb(file);base,binary=G.read_glb(p/'export/mm6_mnk1_lod0.glb')
node=next(n for n in doc['nodes'] if n.get('name')=='Monk');mesh=doc['meshes'][node['mesh']];skin=doc['skins'][node['skin']]
assert len(skin['joints'])<=128
variants=doc['extensions']['KHR_materials_variants']['variants'];assert [v['name'] for v in variants]==['mnk1_a','mnk1_b','mnk1_c']
assert [a['name'] for a in doc['animations']]==[a['name'] for a in base['animations']] and len(doc['animations'])==9
samples=[]
for a,b in zip(doc['animations'],base['animations']):
 assert a['channels']==b['channels']
 for s,t in zip(a['samplers'],b['samplers']):
  for key in ['input','output']:
   ours=G.accessor_bytes(doc,buf,s[key]);assert ours==G.accessor_bytes(base,binary,t[key]);samples.append(ours)
for primitive,original in zip(mesh['primitives'],base['meshes'][0]['primitives']):
 for sem,accessor in original['attributes'].items():assert G.accessor_bytes(doc,buf,primitive['attributes'][sem])==G.accessor_bytes(base,binary,accessor)
 assert G.accessor_bytes(doc,buf,primitive['indices'])==G.accessor_bytes(base,binary,original['indices'])
report={'file':str(file.relative_to(p)),'bytes':file.stat().st_size,'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'skin_joints':len(skin['joints']),'variants':[v['name'] for v in variants],'animation_sha256':hashlib.sha256(b''.join(samples)).hexdigest(),'geometry_animation_preserved':True,'colour_lod_triangles':[],'shadow_lod_triangles':[],'images':[],'max_weight_error':0}
for kind,key in [('colour_lod_triangles','openyamm_lods'),('shadow_lod_triangles','openyamm_shadow_lods')]:
 indices=([node['mesh']] if key=='openyamm_lods' else [])+mesh['extras'][key]
 assert len(indices)==4
 for mi in indices:
  m=doc['meshes'][mi];report[kind].append(sum(doc['accessors'][q['indices']]['count']//3 for q in m['primitives']))
  for q in m['primitives']:
   at=q['attributes'];weights=[]
   for slot in range(2):
    if f'WEIGHTS_{slot}' not in at:continue
    weights.append(np.frombuffer(G.accessor_bytes(doc,buf,at[f'WEIGHTS_{slot}']),np.float32).reshape(-1,4))
    ai=at[f'JOINTS_{slot}'];indices=np.frombuffer(G.accessor_bytes(doc,buf,ai),{5121:np.uint8,5123:np.uint16}[doc['accessors'][ai]['componentType']]);assert indices.max()<len(skin['joints'])
   w=np.concatenate(weights,axis=1);assert w.shape[1]<=8
   err=float(abs(w.sum(1)-1).max());report['max_weight_error']=max(report['max_weight_error'],err);assert err<1e-5 and (w>=0).all()
   assert len(q['extensions']['KHR_materials_variants']['mappings'])==3
for im in doc['images']:
 view=doc['bufferViews'][im['bufferView']];data=buf[view.get('byteOffset',0):view.get('byteOffset',0)+view['byteLength']];pixels=Image.open(io.BytesIO(data));report['images'].append({'name':im.get('name'), 'size':list(pixels.size),'mode':pixels.mode});assert pixels.format=='PNG'
assert sorted(tuple(i['size']) for i in report['images'])==[(1024,1024)]*3+[(2048,2048)]
for mat in doc['materials']:
 assert mat['extras']['openyamm_specular']==0 and mat['pbrMetallicRoughness']['metallicFactor']==0
 info=mat['pbrMetallicRoughness']['metallicRoughnessTexture'];im=doc['images'][doc['textures'][info['index']]['source']];view=doc['bufferViews'][im['bufferView']];raw=buf[view.get('byteOffset',0):view.get('byteOffset',0)+view['byteLength']]
 assert np.array_equal(np.array(Image.open(io.BytesIO(raw))),np.array(Image.open(p/'textures/mnk1_orm_1k.png')))
report['pass']=True;(p/'review/runtime_validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
# Local LOD previews: mutate only the visible mesh reference; runtime files remain untouched.
for level,mi in enumerate([node['mesh']]+mesh['extras']['openyamm_lods']):
 node['mesh']=mi;G.write_glb(p/f'work/review_lod{level}.glb',doc,buf)
