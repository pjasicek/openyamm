from pathlib import Path
import sys
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'claude_shared'))
from region_variants import apply_variants
sys.path.insert(0,str(P.parents[2]/'tools'))
from build_actor_lods import read_glb,write_glb
source=P/'export/mm8_m492_lods.glb';d,b=read_glb(source);b=bytearray(b)
fire=next(m for m in d['materials'] if m.get('name')=='DragonDeathFire');fire.pop('emissiveTexture',None);fire.pop('emissiveFactor',None)
mat=next(m for m in d['materials'] if m.get('name')=='Dragon_A')
# Refresh authoritative paint without repeating geometry reduction after a material-only refinement.
for label,info in [('basecolor',mat['pbrMetallicRoughness']['baseColorTexture']),('normal',mat['normalTexture']),('metal_rough',mat['pbrMetallicRoughness']['metallicRoughnessTexture'])]:
 image=d['images'][d['textures'][info['index']]['source']];raw=(P/'textures'/f'dragon_{label}_2k.png').read_bytes();b+=b'\0'*(-len(b)%4)
 image['bufferView']=len(d['bufferViews']);d['bufferViews'].append({'buffer':0,'byteOffset':len(b),'byteLength':len(raw)});b+=raw
source=P/'export/mm8_m492_lods_textured.glb';write_glb(source,d,b)
apply_variants(source,P/'export/mm8_m492.glb',P/'textures/dragon_ramps.json',[('Dragon_','openyamm_specular',1.),('Dragon_','openyamm_specular_mask',True)])
