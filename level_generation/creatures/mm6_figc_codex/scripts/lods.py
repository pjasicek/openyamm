"""Merge measured lower-LOD geometry while retaining the LOD0 rig and animations, with separate rebaked textures per LOD."""
import copy,json,struct,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'))
from build_actor_lods import read_glb,write_glb,accessor_bytes,append_accessor,merge_shadow
E=P/'export';R=P/'review/round3';d,raw=read_glb(E/'mm6_figc_runtime_lod0.glb');binary=bytearray(raw)
node=next(n for n in d['nodes'] if n.get('name')=='FighterChain');base=node['mesh'];skin=d['skins'][node['skin']];joints=[d['nodes'][i]['name'] for i in skin['joints']];bind=list(struct.iter_unpack('<16f',accessor_bytes(d,raw,skin['inverseBindMatrices'])));materials={m['name']:i for i,m in enumerate(d['materials'])};lods=[]
for level in range(1,4):
 src,payload=read_glb(R/f'export_lod{level}/mm6_figc_lod0.glb');n=next(n for n in src['nodes'] if n.get('name')=='FighterChain');s=src['skins'][n['skin']];remap=[joints.index(src['nodes'][i]['name']) for i in s['joints']]
 for i,m in zip(remap,struct.iter_unpack('<16f',accessor_bytes(src,payload,s['inverseBindMatrices']))):assert max(abs(a-b) for a,b in zip(bind[i],m))<1e-4,'Bind space changed'
 for key,default in [('translation',[0,0,0]),('rotation',[0,0,0,1]),('scale',[1,1,1])]:assert max(abs(a-b) for a,b in zip(node.get(key,default),n.get(key,default)))<1e-4
 # Every LOD owns UVs, so its embedded images and materials must travel with its geometry.
 image_offset=len(d.get('images',[]));texture_offset=len(d.get('textures',[]));sampler_offset=len(d.get('samplers',[]));material_offset=len(d.get('materials',[]))
 for image in src.get('images',[]):
  image=copy.deepcopy(image);v=src['bufferViews'][image['bufferView']];start=v.get('byteOffset',0);data=payload[start:start+v['byteLength']];binary.extend(b'\0'*(-len(binary)%4));image['bufferView']=len(d['bufferViews']);d['bufferViews'].append({'buffer':0,'byteOffset':len(binary),'byteLength':len(data)});binary.extend(data);d.setdefault('images',[]).append(image)
 d.setdefault('samplers',[]).extend(copy.deepcopy(src.get('samplers',[])))
 for tex in src.get('textures',[]):
  tex=copy.deepcopy(tex);tex['source']+=image_offset
  if 'sampler' in tex:tex['sampler']+=sampler_offset
  d.setdefault('textures',[]).append(tex)
 def remap_textures(value):
  if isinstance(value,dict):
   for key,item in value.items():
    if key=='index':value[key]=item+texture_offset
    else:remap_textures(item)
  elif isinstance(value,list):
   for item in value:remap_textures(item)
 for mat in src['materials']:
  mat=copy.deepcopy(mat);mat['name']=mat['name'].replace('_A',f'_LOD{level}_A');remap_textures(mat);d['materials'].append(mat)
 mesh={'name':f'FighterChain_LOD{level}','primitives':[]}
 for p in src['meshes'][n['mesh']]['primitives']:
  attrs={}
  for semantic,index in p['attributes'].items():
   a=src['accessors'][index];packed=accessor_bytes(src,payload,index)
   if semantic.startswith('JOINTS_'):
    code={5121:'B',5123:'H'}[a['componentType']];v=[remap[x[0]] for x in struct.iter_unpack('<'+code,packed)];packed=struct.pack('<'+code*len(v),*v)
   attrs[semantic]=append_accessor(d,binary,a,packed)
  i=p['indices'];mesh['primitives'].append({'attributes':attrs,'indices':append_accessor(d,binary,src['accessors'][i],accessor_bytes(src,payload,i)),'material':material_offset+p['material']})
 lods.append(len(d['meshes']));d['meshes'].append(mesh)
shadows=[]
for index in [base]+lods:
 shadows.append(len(d['meshes']));d['meshes'].append(merge_shadow(d,binary,d['meshes'][index]))
d['meshes'][base].setdefault('extras',{}).update(openyamm_lods=lods,openyamm_shadow_lods=shadows)
counts=[sum(d['accessors'][p['indices']]['count']//3 for p in d['meshes'][i]['primitives']) for i in [base]+lods];selected=json.loads((R/'final_selection.json').read_text());assert counts==[selected[str(i)]['triangles'] for i in range(4)],counts
assert all(a>b for a,b in zip(counts,counts[1:]));assert all(a<=b for a,b in zip(counts,[15427,7712,2771,903]))
write_glb(E/'mm6_figc_lods.glb',d,binary);(E/'lods.json').write_text(json.dumps({'triangles':counts,'colour_meshes':[base]+lods,'shadow_meshes':shadows,'method':'measured eight-view reduction at switch distances','original_rig_clips_retained':True,'textures_rebaked_per_lod':True},indent=2)+'\n');print('MEASURED_LODS',counts)
