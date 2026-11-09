"""Attach the measured native LOD geometry to the unchanged LOD0 rig and animation buffers."""
import sys,copy,struct,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'))
from build_actor_lods import read_glb,write_glb,accessor_bytes,append_accessor,merge_shadow
E=P/'export';d,b=read_glb(E/'mm6_min1_runtime_lod0.glb');binary=bytearray(b);node=next(n for n in d['nodes'] if n.get('name')=='Minotaur');base=node['mesh'];skin=d['skins'][node['skin']];names=[d['nodes'][j]['name'] for j in skin['joints']];binds=list(struct.iter_unpack('<16f',accessor_bytes(d,b,skin['inverseBindMatrices'])));materials={m['name']:i for i,m in enumerate(d['materials'])};indices=[]
for level in range(1,4):
 s,payload=read_glb(E/f'mm6_min1_geometry_lod{level}.glb');sn=next(n for n in s['nodes'] if n.get('name')=='Minotaur');sk=s['skins'][sn['skin']];remap=[names.index(s['nodes'][j]['name']) for j in sk['joints']];ms=list(struct.iter_unpack('<16f',accessor_bytes(s,payload,sk['inverseBindMatrices'])))
 assert all(abs(a-b)<1e-4 for i,m in zip(remap,ms) for a,b in zip(binds[i],m)),'LOD bind-space mismatch'
 for k,default in [('translation',[0,0,0]),('rotation',[0,0,0,1]),('scale',[1,1,1])]:assert all(abs(a-b)<1e-4 for a,b in zip(node.get(k,default),sn.get(k,default)))
 mesh={'name':f'Minotaur_LOD{level}','primitives':[]}
 for primitive in s['meshes'][sn['mesh']]['primitives']:
  attrs={}
  for semantic,index in primitive['attributes'].items():
   ac=s['accessors'][index];packed=accessor_bytes(s,payload,index)
   if semantic.startswith('JOINTS_'):
    code={5121:'B',5123:'H'}[ac['componentType']];values=[remap[v[0]] for v in struct.iter_unpack('<'+code,packed)];packed=struct.pack('<'+code*len(values),*values)
   attrs[semantic]=append_accessor(d,binary,ac,packed)
  index=primitive['indices'];mesh['primitives'].append({'attributes':attrs,'indices':append_accessor(d,binary,s['accessors'][index],accessor_bytes(s,payload,index)),'material':materials[s['materials'][primitive['material']]['name']]})
 indices.append(len(d['meshes']));d['meshes'].append(mesh)
shadows=[]
for i in [base]+indices:
 shadow=merge_shadow(d,binary,d['meshes'][i]);shadows.append(len(d['meshes']));d['meshes'].append(shadow)
d['meshes'][base].setdefault('extras',{}).update(openyamm_lods=indices,openyamm_shadow_lods=shadows)
counts=[sum(d['accessors'][p['indices']]['count']//3 for p in d['meshes'][i]['primitives']) for i in [base]+indices];assert all(a>b for a,b in zip(counts,counts[1:]))
write_glb(E/'mm6_min1_lods.glb',d,binary);(E/'lods.json').write_text(json.dumps({'triangles':counts,'colour_meshes':[base]+indices,'shadow_meshes':shadows,'method':'Protected planar dissolution and collapse; measured at 700 px and 550/220/88 projected switch diameters.','curve':'review/round1/reduction/curve.json','original_geometry_rig_clips_images_retained':True},indent=2));print('MEASURED LODS',counts)
