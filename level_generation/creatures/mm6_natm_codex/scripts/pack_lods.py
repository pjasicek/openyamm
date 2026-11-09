"""Pack colour LODs with one shared padded texture set and opaque dedicated shadows."""
import json,copy,struct,sys,numpy as np
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p.parents[2]/'tools'))
from build_actor_lods import read_glb,write_glb,append_accessor,accessor_bytes,merge_shadow
out=p/'export'
def pack(kind,node_name):
 doc,data=read_glb(out/f'mm6_natm_{kind}_lod0.glb');buf=bytearray(data);node=next(n for n in doc['nodes'] if n.get('name')==node_name);base=node['mesh'];lods=[]
 if kind=='body':
  skin=doc['skins'][node['skin']];names=[doc['nodes'][i]['name'] for i in skin['joints']];bind=np.frombuffer(accessor_bytes(doc,buf,skin['inverseBindMatrices']),np.float32).reshape(-1,16)
 for level in range(1,4):
  src,payload=read_glb(out/f'mm6_natm_{kind}_lod{level}.glb');sn=next(n for n in src['nodes'] if n.get('name')==node_name)
  if kind=='body':
   ss=src['skins'][sn['skin']];remap=[names.index(src['nodes'][i]['name']) for i in ss['joints']];sb=np.frombuffer(accessor_bytes(src,payload,ss['inverseBindMatrices']),np.float32).reshape(-1,16);assert np.max(abs(bind[remap]-sb))<1e-4
  # All colour levels use the exact LOD0 atlas images, samplers and texture indices.
  assert len(src['images'])==len(doc['images'])==4
  material_map={}
  for i,mat in enumerate(src['materials']):
   key={k:v for k,v in mat.items()if k!='name'}
   match=next((j for j,m in enumerate(doc['materials'])if {k:v for k,v in m.items()if k!='name'}==key),None)
   if match is None:match=len(doc['materials']);doc['materials'].append(copy.deepcopy(mat))
   material_map[i]=match
  mesh={'name':f'{node_name}_LOD{level}','primitives':[]}
  for pr in src['meshes'][sn['mesh']]['primitives']:
   new=copy.deepcopy(pr);attrs={}
   for semantic,index in pr['attributes'].items():
    ac=src['accessors'][index];packed=accessor_bytes(src,payload,index)
    if semantic.startswith('JOINTS_'):
     code={5121:'B',5123:'H'}[ac['componentType']];values=[remap[v[0]] for v in struct.iter_unpack('<'+code,packed)];packed=struct.pack('<'+code*len(values),*values)
    attrs[semantic]=append_accessor(doc,buf,ac,packed)
   i=pr['indices'];new.update(attributes=attrs,indices=append_accessor(doc,buf,src['accessors'][i],accessor_bytes(src,payload,i)),material=material_map[pr['material']])
   for mapping in new.get('extensions',{}).get('KHR_materials_variants',{}).get('mappings',[]):mapping['material']=material_map[mapping['material']]
   mesh['primitives'].append(new)
  lods.append(len(doc['meshes']));doc['meshes'].append(mesh)
 doc['meshes'][base].setdefault('extras',{})['openyamm_lods']=lods
 if kind=='body':
  shadows=[]
  shadow_material=len(doc['materials']);doc['materials'].append({'name':'Natm_Shadow_Opaque','alphaMode':'OPAQUE','doubleSided':True,'pbrMetallicRoughness':{'baseColorFactor':[1,1,1,1],'metallicFactor':0,'roughnessFactor':1}})
  for mi in [base]+lods:
   source=copy.deepcopy(doc['meshes'][mi]);source.pop('extras',None)
   for q in source['primitives']:q['material']=shadow_material;q.pop('extensions',None)
   shadow=merge_shadow(doc,buf,source)
   shadows.append(len(doc['meshes']));doc['meshes'].append(shadow)
  doc['meshes'][base]['extras']['openyamm_shadow_lods']=shadows
 counts=[sum(doc['accessors'][q['indices']]['count']//3 for q in doc['meshes'][i]['primitives']) for i in [base]+lods]
 if kind=='body':assert all(a>b for a,b in zip(counts,counts[1:])),counts
 file=out/('mm6_natm_body_packed.glb' if kind=='body' else f'mm6_natm_{kind}.glb');from merge_head_material import compact
 doc,buf=compact(doc,buf);write_glb(file,doc,buf);return counts
result={kind:pack(kind,node) for kind,node in [('body','Natm'),('spear','Spear'),('buckler','Buckler')]}
(out/'lods.json').write_text(json.dumps(result,indent=2));print('PACKED_LODS',result)
