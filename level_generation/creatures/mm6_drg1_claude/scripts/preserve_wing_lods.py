import sys,copy
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'));import build_actor_lods as L
f=P/'export/mm6_drg1_lods.glb';d,b=L.read_glb(f);b=bytearray(b);node=next(n for n in d['nodes'] if n.get('name')=='Body');base=d['meshes'][node['mesh']];wing=next(p for p in base['primitives'] if d['materials'][p['material']]['name']=='DrakeWings_A')
for index in base['extras']['openyamm_lods']:
 m=d['meshes'][index]
 for i,p in enumerate(m['primitives']):
  if d['materials'][p['material']]['name']=='DrakeWings_A':m['primitives'][i]=copy.deepcopy(wing)
# Regenerate merged shadow primitives after retaining the intact membranes.
for level,index in enumerate([node['mesh']]+base['extras']['openyamm_lods']):d['meshes'][base['extras']['openyamm_shadow_lods'][level]]=L.merge_shadow(d,b,d['meshes'][index])
L.write_glb(f,d,b);print('Intact wing membranes retained in every LOD')
