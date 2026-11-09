"""Finalize the existing runtime contract without changing geometry, skin or clip samples."""
import sys,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];E=P/'export'
sys.path.insert(0,str(P.parents[2]/'tools'));from merge_head_material import read_glb,write_glb
from prepare_actor_glb import prepare
sys.path.insert(0,str(P.parent/'claude_shared'));import region_variants as R
source=E/'mm8_m492_lod0.glb';d,b=read_glb(source)
fire=next(m for m in d['materials'] if m['name']=='DragonDeathFire');fire['alphaMode']='BLEND';fire['doubleSided']=True
fire.pop('emissiveTexture',None);fire.pop('emissiveFactor',None) # Unlit base colour already carries the flame.
fire.setdefault('extensions',{})['KHR_materials_unlit']={};fire['extras']={'openyamm_edge_darkening':0.0,'openyamm_specular':0.0}
d.setdefault('extensionsUsed',[])
if 'KHR_materials_unlit' not in d['extensionsUsed']:d['extensionsUsed'].append('KHR_materials_unlit')
for a in d['animations']:
 for c in a['channels']:
  if d['nodes'][c['target']['node']].get('name','').startswith('MouthFire') and c['target']['path']=='scale':a['samplers'][c['sampler']]['interpolation']='STEP'
write_glb(source,d,b);prepare(source,E/'mm8_m492_prepared.glb')
