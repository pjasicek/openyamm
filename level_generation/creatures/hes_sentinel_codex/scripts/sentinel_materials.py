"""Apply shared region variants, per-tier metal response and factor-only muzzle emission."""
import copy,json,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];R=P.parents[2]
sys.path[:0]=[str(R/'tools'),str(R/'level_generation/creatures/claude_shared')]
from region_variants import apply_variants,_compact
from build_actor_lods import read_glb,write_glb
src,dst=map(Path,sys.argv[1:]);apply_variants(src,dst,P/'textures/sentinel_ramps.json')
d,b=read_glb(dst)
energy=next(i for i,m in enumerate(d['materials']) if m['name']=='Sentinel_Energy')
copies=[]
for tier,color in zip('ABC',[(.95,.18,.008),(.95,.22,.01),(1,.42,.07)]):
 m=copy.deepcopy(d['materials'][energy]);m['name']='Sentinel_Energy_'+tier;m['emissiveFactor']=list(color)
 m.pop('emissiveTexture',None);m.setdefault('extras',{}).update(openyamm_bloom=True,openyamm_edge_darkening=0)
 copies.append(len(d['materials']));d['materials'].append(m)
for mesh in d['meshes']:
 for p in mesh['primitives']:
  if p['material']==energy:
   p['material']=copies[0];p.setdefault('extensions',{})['KHR_materials_variants']={'mappings':[{'material':mi,'variants':[i]} for i,mi in enumerate(copies)]}
mask=None
for m in d['materials']:
 n=m.get('name','');p=m.get('pbrMetallicRoughness',{});e=m.setdefault('extras',{})
 if n.startswith('Sentinel_Armour'):p['metallicFactor']=.85 if n.endswith('_C') else 0
 elif n.startswith('Sentinel_Trim'):p['metallicFactor']=.85
 elif n.startswith('Sentinel_Resin'):p['metallicFactor']=0
 if 'openyamm_region_mask' in e:
  if mask is None:mask=e['openyamm_region_mask']
  e['openyamm_region_mask']=copy.deepcopy(mask)
  e['openyamm_edge_darkening']=.35
 assert 'emissiveTexture' not in m
# One shared mask image, including across the separate material classes.
d,b=_compact(d,b);write_glb(dst,d,b)
assert len([i for i in d['images'] if 'region_mask' in i.get('name','')])==1
print('Shared tiers and factor-only emission:',dst)
