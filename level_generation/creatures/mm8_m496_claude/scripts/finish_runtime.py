"""Link authored LODs and the runtime unlit/scroll contracts; preserve native shared palette 496."""
from pathlib import Path
import sys,subprocess,json,hashlib,copy,shutil
P=Path(__file__).resolve().parents[1];REPO=P.parents[2];sys.path.insert(0,str(REPO/'tools'))
from build_actor_lods import read_glb,write_glb
from prepare_actor_glb import prepare
source=P/'export/mm8_m496_raw.glb';prepared=P/'export/mm8_m496_prepared.glb';target=P/'export/mm8_m496.glb'
prepare(source,prepared);d,b=read_glb(prepared)
assert len(d['skins'])==1
names=[m['name'] for m in d['meshes']]
for base in ['Body','Flame','Tongues','Burst','Ash']:
 lods=[names.index(base+'_LOD'+str(i)) for i in [1,2,3]];mesh=d['meshes'][names.index(base)];mesh.setdefault('extras',{})['openyamm_lods']=lods
 if base=='Body':mesh['extras']['openyamm_shadow_lods']=lods
 for n in d['nodes']:
  if n.get('mesh') in lods:n.pop('mesh');n.pop('skin',None)
for m in d['materials']:
 name=m['name'];kind=name.split('_')[-1];pbr=m['pbrMetallicRoughness'];pbr.update(metallicFactor=0,roughnessFactor=1,baseColorFactor=[1,1,1,1]);m.pop('emissiveFactor',None);m.pop('emissiveTexture',None);m['extensions']={'KHR_materials_unlit':{}};m['extras']={'openyamm_specular':0.,'openyamm_edge_darkening':0.};m['doubleSided']=kind in ['Burst','Ash'];m['alphaMode']='OPAQUE' if kind=='Body' else 'OPAQUE' if kind=='Ash' else 'BLEND'
 if kind=='Flame':m['extras']['openyamm_uv_scroll']=[0.,.5]
 samplers=d.setdefault('samplers',[]);samplers.append({'magFilter':9729,'minFilter':9987,'wrapS':10497 if kind=='Flame' else 33071,'wrapT':10497 if kind=='Flame' else 33071});d['textures'][pbr['baseColorTexture']['index']]['sampler']=len(samplers)-1
 if kind=='Burst':m.pop('alphaCutoff',None)
d['extensionsUsed']=['KHR_materials_unlit'];d.pop('extensionsRequired',None)
assert len({n.get('name') for n in d['nodes']})==len(d['nodes'])
for i,mesh in enumerate(d['meshes']):
 for key in ['openyamm_lods','openyamm_shadow_lods']:
  chain=mesh.get('extras',{}).get(key,[]);assert i not in chain and len(chain)==len(set(chain))
write_glb(target,d,b)
subprocess.run([sys.executable,str(REPO/'tools/model_hide_collapsed_meshes.py'),str(target),'--write',str(target)],check=True)
d,b=read_glb(target);assert len([n for n in d['nodes'] if 'mesh' in n])==5
v=P/'review/viewer';v.mkdir(parents=True,exist_ok=True)
for suffix,scale in [('a',1.),('b',1.75/1.299988),('c',2/1.299988)]:
 doc=copy.deepcopy(d);scene=doc['scenes'][doc.get('scene',0)];doc['nodes'].append({'name':'NativeTierScale','children':scene['nodes'],'scale':[scale]*3});scene['nodes']=[len(doc['nodes'])-1];write_glb(v/f'mm8_m496_{suffix}.glb',doc,b)
print('FINISHED',target,hashlib.sha256(target.read_bytes()).hexdigest())
