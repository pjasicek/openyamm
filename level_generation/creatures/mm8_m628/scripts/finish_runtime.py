"""Shared palette variants and merged head atlas; the flexing bow remains an animated primitive."""
import sys,json,subprocess,hashlib
from pathlib import Path
P=Path(__file__).resolve().parents[1];R=P.parents[2];sys.path.insert(0,str(R/'tools'))
from merge_head_material import read_glb,write_glb,compact
from build_actor_lods import accessor_bytes
E=P/'export';path=E/'mm8_m628.glb'
subprocess.run([sys.executable,str(P.parent/'claude_shared/region_variants.py'),str(E/'mm8_m628_lods.glb'),str(path),
    str(P/'textures/m628_ramps.json'),'--extra','SkeletonArcher','openyamm_specular=1','--extra','SkeletonArcher','openyamm_specular_mask=true',
    '--extra','SkeletonArcher','pbr.metallicFactor=0'],check=True)
d,b=read_glb(path);parked=[]
for i,m in enumerate(list(d['meshes'])):
    if len(m['primitives'])!=3:continue
    props=[p for p in m['primitives']if 'Bow'in d['materials'][p['material']]['name']];assert len(props)==1
    m['primitives'].remove(props[0]);parked.append((i,len(d['meshes'])));d['meshes'].append({'name':f'BowReservoir_{i}','primitives':props})
assert len(parked)==4
write_glb(path,d,b)
subprocess.run([sys.executable,str(R/'tools/merge_head_material.py'),str(path),str(path)],check=True)
d,b=read_glb(path)
for original,reservoir in parked:d['meshes'][original]['primitives']+=d['meshes'][reservoir]['primitives']
for _,reservoir in reversed(parked):assert reservoir==len(d['meshes'])-1;d['meshes'].pop()
write_glb(path,*compact(d,b));d,b=read_glb(path)
node=next(n for n in d['nodes']if n.get('name')=='SkeletonArcher');indices=[node['mesh']]+d['meshes'][node['mesh']]['extras']['openyamm_lods']
assert all(len(d['meshes'][i]['primitives'])==2 for i in indices)
assert [v['name']for v in d['extensions']['KHR_materials_variants']['variants']]==['m628_a','m628_b','m628_c']
def channels(doc,bin):return {a['name']:{(doc['nodes'][c['target']['node']]['name'],c['target']['path']):
    tuple(accessor_bytes(doc,bin,a['samplers'][c['sampler']][k])for k in ['input','output'])for c in a['channels']}for a in doc['animations']}
raw,rb=read_glb(E/'mm8_m628_raw.glb');assert channels(d,b)==channels(raw,rb),'Post-processing changed animation keys'
report={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size,'images':len(d['images']),
    'triangles':[sum(d['accessors'][p['indices']]['count']//3 for p in d['meshes'][i]['primitives'])for i in indices],
    'draws_per_lod':2,'animation_samples_identical':True,'bow_storage':'Skinned primitive: grip, elastic limbs, string, nocked arrow and native mounted carrier require independent motion.'}
(E/'runtime_receipt.json').write_text(json.dumps(report,indent=2));print('RUNTIME',report)
