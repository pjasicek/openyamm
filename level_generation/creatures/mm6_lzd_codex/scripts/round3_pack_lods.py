"""Attach measured lower meshes to the LOD0 document without resampling its animations or images."""
import sys,json,struct
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P.parents[2]/'tools'))
from build_actor_lods import read_glb,write_glb,accessor_bytes,append_accessor,merge_shadow
E=P/'export';d,raw=read_glb(E/'mm6_lzd_lod0.glb');b=bytearray(raw);node=next(n for n in d['nodes']if n.get('name')=='Lizard');base=node['mesh'];names=[d['nodes'][i]['name']for i in d['skins'][node['skin']]['joints']];ib=list(struct.iter_unpack('<16f',accessor_bytes(d,b,d['skins'][node['skin']]['inverseBindMatrices'])));mats={m['name']:i for i,m in enumerate(d['materials'])};indices=[]
for level in range(1,4):
 low,lb=read_glb(E/f'mm6_lzd_level{level}.glb');ln=next(n for n in low['nodes']if n.get('name')=='Lizard');sk=low['skins'][ln['skin']];remap=[names.index(low['nodes'][i]['name'])for i in sk['joints']];matrices=list(struct.iter_unpack('<16f',accessor_bytes(low,lb,sk['inverseBindMatrices'])));assert max(abs(x-y)for i,m in zip(remap,matrices)for x,y in zip(ib[i],m))<1e-4
 mesh={'name':f'Lizard_LOD{level}','primitives':[]}
 for prim in low['meshes'][ln['mesh']]['primitives']:
  attrs={}
  for semantic,idx in prim['attributes'].items():
   packed=accessor_bytes(low,lb,idx);acc=low['accessors'][idx]
   if semantic.startswith('JOINTS_'):
    code={5121:'B',5123:'H'}[acc['componentType']];values=[remap[v[0]]for v in struct.iter_unpack('<'+code,packed)];packed=struct.pack('<'+code*len(values),*values)
   attrs[semantic]=append_accessor(d,b,acc,packed)
  ix=prim['indices'];mesh['primitives'].append({'attributes':attrs,'indices':append_accessor(d,b,low['accessors'][ix],accessor_bytes(low,lb,ix)),'material':mats[low['materials'][prim['material']]['name']]})
 indices.append(len(d['meshes']));d['meshes'].append(mesh)
shadows=[]
for ix in [base]+indices:
 m=merge_shadow(d,b,d['meshes'][ix]);shadows.append(len(d['meshes']));d['meshes'].append(m)
d['meshes'][base].setdefault('extras',{}).update(openyamm_lods=indices,openyamm_shadow_lods=shadows)
write_glb(E/'mm6_lzd_lods.glb',d,b);counts=[sum(d['accessors'][p['indices']]['count']//3 for p in d['meshes'][i]['primitives'])for i in [base]+indices]
(E/'lods.json').write_text(json.dumps({'triangles':counts,'colour_meshes':[base]+indices,'shadow_meshes':shadows,'method':'independent measured candidates, silhouette IoU >= .995 and SSIM >= .98 at 800/550/220/88 px; identical levels retained when no safe cut exists'},indent=2));print('MEASURED LODS',counts)
