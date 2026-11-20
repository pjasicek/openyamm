"""Prepare body LODs, authored fire LODs and native palette variants using the shared runtime tools."""
import sys,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];E=P/'export'
sys.path.insert(0,str(P.parents[2]/'tools'))
from merge_head_material import read_glb,write_glb
from prepare_actor_glb import prepare
sys.path.insert(0,str(P.parent/'claude_shared'))
from region_variants import apply_variants
source=E/'mm8_m572_lod0.glb';d,b=read_glb(source)
names=[m['name'] for m in d['meshes']];lods=[names.index('PhoenixFlames_LOD'+str(i)) for i in (1,2,3)]
d['meshes'][names.index('PhoenixFlames')].setdefault('extras',{})['openyamm_lods']=lods
for node in d['nodes']:
 if node.get('mesh') in lods:node.pop('mesh');node.pop('skin',None)
for m in d['materials']:
 if m['name'] not in ('Phoenix_Flame','Phoenix_Fringe'):continue
 m['alphaMode']='BLEND';m['doubleSided']=True;m['extensions']={'KHR_materials_unlit':{}}
 m.pop('emissiveTexture',None);m.pop('emissiveFactor',None)
 m['extras']={'openyamm_edge_darkening':0.,'openyamm_specular':0.,'openyamm_uv_scroll':[0.,0.]}
 pbr=m['pbrMetallicRoughness'];pbr['baseColorFactor']=[1,1,1,.80];pbr['metallicFactor']=0;pbr['roughnessFactor']=1
 texture=d['textures'][pbr['baseColorTexture']['index']];d.setdefault('samplers',[]).append({'magFilter':9729,'minFilter':9987,'wrapS':33071,'wrapT':33071});texture['sampler']=len(d['samplers'])-1
if 'KHR_materials_unlit' not in d.setdefault('extensionsUsed',[]):d['extensionsUsed'].append('KHR_materials_unlit')
write_glb(source,d,b);prepare(source,E/'mm8_m572_prepared.glb')
