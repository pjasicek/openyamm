from pathlib import Path
import sys,json
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'));from merge_head_material import read_glb,write_glb,compact
src=P/'export/mm6_dwa1_lod0.glb';d,b=read_glb(src)
for mat in d['materials']:
 prefix={'Dwarf_A':'dwa1_','DwarfHead_A':'dwa1_head_','DwarfAxe_A':'axe/'}[mat['name'].split('.')[0]];mat['pbrMetallicRoughness']['metallicFactor']=0;mat['extras']={'openyamm_specular':1,'openyamm_specular_mask':True};idx=mat['pbrMetallicRoughness']['metallicRoughnessTexture']['index'];im=d['images'][d['textures'][idx]['source']];payload=(P/'textures'/f'{prefix}metal_rough_1k.png').read_bytes();b.extend(bytes((-len(b)%4)));im['bufferView']=len(d['bufferViews']);d['bufferViews'].append({'buffer':0,'byteOffset':len(b),'byteLength':len(payload)});b.extend(payload)
write_glb(P/'work/material_packed.glb',*compact(d,b))
from prepare_actor_glb import prepare
prepare(P/'work/material_packed.glb',P/'export/mm6_dwa1_runtime_lod0.glb')
