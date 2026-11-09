"""Compose review geometry from the final runtime body and rigid attachments, preserving exact transforms."""
import sys,copy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'))
from merge_head_material import read_glb,write_glb,compact,TEXTURE_SLOTS,slot
folder=P/'review/runtime';folder.mkdir(exist_ok=True)
for level in range(4):
 doc,buf=read_glb(P/'export/mm6_natm.glb');node=next(n for n in doc['nodes']if n.get('name')=='Natm');base=node['mesh'];index=base if level==0 else doc['meshes'][base]['extras']['openyamm_lods'][level-1];doc['meshes']=[copy.deepcopy(doc['meshes'][index])];doc['meshes'][0].pop('extras',None);doc['meshes'][0]['name']='Natm';node['mesh']=0;doc,buf=compact(doc,buf)
 for kind,name in [('spear','Spear'),('buckler','Buckler')]:
  src,payload=read_glb(P/f'export/mm6_natm_{kind}.glb');base=src['nodes'][0]['mesh'];index=base if level==0 else src['meshes'][base]['extras']['openyamm_lods'][level-1];src['meshes']=[copy.deepcopy(src['meshes'][index])];src['meshes'][0].pop('extras',None);src['nodes'][0]['mesh']=0;src,payload=compact(src,payload)
  vo,ao,io,to,so,mo=(len(doc.get(k,[]))for k in ['bufferViews','accessors','images','textures','samplers','materials']);buf.extend(b'\0'*(-len(buf)%4));offset=len(buf);buf.extend(payload)
  for v in src['bufferViews']:v['byteOffset']=v.get('byteOffset',0)+offset
  for a in src['accessors']:a['bufferView']+=vo
  for im in src['images']:im['bufferView']+=vo
  for tex in src['textures']:tex['source']+=io;tex['sampler']=tex.get('sampler',0)+so
  for mat in src['materials']:
   for path in TEXTURE_SLOTS:
    info=slot(mat,path)
    if info:info['index']+=to
  for pr in src['meshes'][0]['primitives']:
   pr['attributes']={k:v+ao for k,v in pr['attributes'].items()};pr['indices']+=ao;pr['material']+=mo
   for mapping in pr.get('extensions',{}).get('KHR_materials_variants',{}).get('mappings',[]):mapping['material']+=mo
  for key in ['bufferViews','accessors','images','textures','samplers','materials']:doc.setdefault(key,[]).extend(src[key])
  ni=len(doc['nodes']);doc['nodes'].append({'name':name+'Mesh','mesh':len(doc['meshes'])});doc['meshes'].extend(src['meshes']);next(n for n in doc['nodes']if n.get('name')==name).setdefault('children',[]).append(ni)
 doc,buf=compact(doc,buf);write_glb(folder/f'combined_lod{level}.glb',doc,buf)
print('RUNTIME_REVIEW_SOURCES_READY')
