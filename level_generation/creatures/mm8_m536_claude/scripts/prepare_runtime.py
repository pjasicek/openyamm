import sys,json,struct,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];E=P/'export';sys.path.insert(0,str(Path('tools').resolve()))
from prepare_actor_glb import prepare
from build_actor_lods import read_glb,write_glb
prepare(E/'mm8_m536_lod0.glb',E/'mm8_m536_runtime_lod0.glb')
doc,binary=read_glb(E/'mm8_m536_runtime_lod0.glb');binary=bytearray(binary)
lods=[]
for name in ['FlameTail_LOD1','FlameTail_LOD2']:
 n=next(n for n in doc['nodes'] if n.get('name')==name);lods.append(n.pop('mesh'));n.pop('skin',None)
tail=next(n for n in doc['nodes'] if n.get('name')=='FlameTail');doc['meshes'][tail['mesh']].setdefault('extras',{})['openyamm_lods']=lods
used=doc.setdefault('extensionsUsed',[])
if 'KHR_materials_unlit' not in used:used.append('KHR_materials_unlit')
for m in doc['materials']:
 if m['name'] in ['EfreetiFlame','EfreetiFringe']:
  m['alphaMode']='BLEND';m['doubleSided']=False;m['extensions']={'KHR_materials_unlit':{}};m.pop('emissiveTexture',None);m.pop('emissiveFactor',None)
  m['extras']={'openyamm_specular':0.0,'openyamm_edge_darkening':0.0,'openyamm_uv_scroll':[0.0,-.35]}
  pbr=m['pbrMetallicRoughness'];pbr.update(metallicFactor=0.0,roughnessFactor=1.0);pbr.pop('metallicRoughnessTexture',None);pbr['baseColorFactor']=[1,1,1,1]
  t=doc['textures'][pbr['baseColorTexture']['index']];samplers=doc.setdefault('samplers',[]);t['sampler']=len(samplers);samplers.append({'magFilter':9729,'minFilter':9987,'wrapS':10497,'wrapT':10497})
for mesh in doc['meshes']:
 if mesh['name'].startswith('FlameTail'):
  assert all('COLOR_0' in p['attributes'] for p in mesh['primitives']),mesh['name']
# The exporter emits an unused white COLOR_0 before the authored alpha attribute.
for mesh in doc['meshes']:
 if mesh['name'].startswith('FlameTail'):
  for p in mesh['primitives']:
   attrs=p['attributes'];attrs['COLOR_0']=attrs.pop('COLOR_1')
audit=json.loads((P/'work/animation_audit.json').read_text())
for a in doc['animations']:
 end=max(doc['accessors'][s['input']]['max'][0] for s in a['samplers'])
 assert abs(end-audit[a['name']]['duration'])<1e-5,(a['name'],end)
write_glb(E/'mm8_m536_runtime_lod0.glb',doc,binary)
