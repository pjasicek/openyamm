"""Retain verified body LODs when body geometry and bind data are unchanged."""
from pathlib import Path
import sys,copy,json
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'))
from build_actor_lods import read_glb,write_glb,append_accessor,accessor_bytes
old,ob=read_glb(P/'work/preplume_lods.glb');d,b=read_glb(P/'export/mm8_m572_prepared.glb');b=bytearray(b)
oldnode=next(n for n in old['nodes'] if n.get('name')=='Body');node=next(n for n in d['nodes'] if n.get('name')=='Body')
os=old['skins'][oldnode['skin']];ns=d['skins'][node['skin']]
assert [old['nodes'][i]['name'] for i in os['joints']]==[d['nodes'][i]['name'] for i in ns['joints']]
assert accessor_bytes(old,ob,os['inverseBindMatrices'])==accessor_bytes(d,b,ns['inverseBindMatrices'])
om=old['meshes'][oldnode['mesh']];nm=d['meshes'][node['mesh']]
for op,np in zip(om['primitives'],nm['primitives']):
 for key in op['attributes']:assert accessor_bytes(old,ob,op['attributes'][key])==accessor_bytes(d,b,np['attributes'][key]),key
 assert accessor_bytes(old,ob,op['indices'])==accessor_bytes(d,b,np['indices'])
for key in ['openyamm_lods','openyamm_shadow_lods']:
 indices=[]
 for i in om['extras'][key]:
  mesh=copy.deepcopy(old['meshes'][i])
  for p in mesh['primitives']:
   p['material']=next(j for j,m in enumerate(d['materials']) if m['name']==old['materials'][p['material']]['name'])
   for k,i in list(p['attributes'].items()):p['attributes'][k]=append_accessor(d,b,old['accessors'][i],accessor_bytes(old,ob,i))
   i=p['indices'];p['indices']=append_accessor(d,b,old['accessors'][i],accessor_bytes(old,ob,i))
  indices.append(len(d['meshes']));d['meshes'].append(mesh)
 nm.setdefault('extras',{})[key]=indices
write_glb(P/'export/mm8_m572_lods.glb',d,b);print('Body geometry, weights and bind matrices unchanged; retained all body colour/shadow LODs.')
