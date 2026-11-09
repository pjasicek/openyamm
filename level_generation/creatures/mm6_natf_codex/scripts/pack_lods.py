"""Pack independently rebaked colour LODs, preserving each level's maps and tier materials."""
import json,copy,struct,sys,numpy as np
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p.parents[2]/'tools'))
from build_actor_lods import read_glb,write_glb,append_accessor,accessor_bytes,merge_shadow
out=p/'export'
def pack(kind,node_name):
 doc,data=read_glb(out/f'mm6_natf_{kind}_lod0.glb');buf=bytearray(data);node=next(n for n in doc['nodes'] if n.get('name')==node_name);base=node['mesh'];lods=[]
 if kind=='body':
  skin=doc['skins'][node['skin']];names=[doc['nodes'][i]['name'] for i in skin['joints']];bind=np.frombuffer(accessor_bytes(doc,buf,skin['inverseBindMatrices']),np.float32).reshape(-1,16)
 for level in range(1,4):
  src,payload=read_glb(out/f'mm6_natf_{kind}_lod{level}.glb');sn=next(n for n in src['nodes'] if n.get('name')==node_name)
  if kind=='body':
   ss=src['skins'][sn['skin']];remap=[names.index(src['nodes'][i]['name']) for i in ss['joints']];sb=np.frombuffer(accessor_bytes(src,payload,ss['inverseBindMatrices']),np.float32).reshape(-1,16);assert np.max(abs(bind[remap]-sb))<1e-4
  image_map={}
  for i,im in enumerate(src['images']):
   view=src['bufferViews'][im['bufferView']];start=view.get('byteOffset',0);packed=payload[start:start+view['byteLength']];buf.extend(b'\0'*(-len(buf)%4));v=len(doc['bufferViews']);doc['bufferViews'].append({'buffer':0,'byteOffset':len(buf),'byteLength':len(packed)});buf.extend(packed);new=copy.deepcopy(im);new['bufferView']=v;image_map[i]=len(doc['images']);doc['images'].append(new)
  sampler_offset=len(doc.get('samplers',[]));doc.setdefault('samplers',[]).extend(src.get('samplers',[]));texture_map={}
  for i,t in enumerate(src['textures']):
   t=copy.deepcopy(t);t['source']=image_map[t['source']]
   if 'sampler'in t:t['sampler']+=sampler_offset
   texture_map[i]=len(doc['textures']);doc['textures'].append(t)
  def texture_refs(x):
   if isinstance(x,dict):
    for key,value in x.items():
     if key in ['baseColorTexture','metallicRoughnessTexture','normalTexture','occlusionTexture','emissiveTexture','openyamm_region_mask'] and isinstance(value,dict):value['index']=texture_map[value['index']]
     else:texture_refs(value)
   elif isinstance(x,list):
    for v in x:texture_refs(v)
  material_offset=len(doc['materials'])
  for mat in src['materials']:mat=copy.deepcopy(mat);texture_refs(mat);doc['materials'].append(mat)
  mesh={'name':f'{node_name}_LOD{level}','primitives':[]}
  for pr in src['meshes'][sn['mesh']]['primitives']:
   new=copy.deepcopy(pr);attrs={}
   for semantic,index in pr['attributes'].items():
    ac=src['accessors'][index];packed=accessor_bytes(src,payload,index)
    if semantic.startswith('JOINTS_'):
     code={5121:'B',5123:'H'}[ac['componentType']];values=[remap[v[0]] for v in struct.iter_unpack('<'+code,packed)];packed=struct.pack('<'+code*len(values),*values)
    attrs[semantic]=append_accessor(doc,buf,ac,packed)
   i=pr['indices'];new.update(attributes=attrs,indices=append_accessor(doc,buf,src['accessors'][i],accessor_bytes(src,payload,i)),material=pr['material']+material_offset)
   for mapping in new.get('extensions',{}).get('KHR_materials_variants',{}).get('mappings',[]):mapping['material']+=material_offset
   mesh['primitives'].append(new)
  lods.append(len(doc['meshes']));doc['meshes'].append(mesh)
 doc['meshes'][base].setdefault('extras',{})['openyamm_lods']=lods
 if kind=='body':
  shadows=[]
  for mi in [base]+lods:shadows.append(len(doc['meshes']));doc['meshes'].append(merge_shadow(doc,buf,doc['meshes'][mi]))
  doc['meshes'][base]['extras']['openyamm_shadow_lods']=shadows
 counts=[sum(doc['accessors'][q['indices']]['count']//3 for q in doc['meshes'][i]['primitives']) for i in [base]+lods]
 if kind=='body':assert all(a>b for a,b in zip(counts,counts[1:])),counts
 file=out/('mm6_natf.glb' if kind=='body' else f'mm6_natf_{kind}.glb');write_glb(file,doc,buf);return counts
result={kind:pack(kind,node) for kind,node in [('body','Natf'),('blade','ForearmBlade'),('shield','LeafShield')]}
(out/'lods.json').write_text(json.dumps(result,indent=2));print('PACKED_LODS',result)
