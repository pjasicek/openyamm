"""Assemble measured LOD resources, native region tiers, one body draw and the independent animated club."""
import sys,json,copy,subprocess,shutil,numpy as np
from pathlib import Path
from PIL import Image
P=Path(__file__).resolve().parents[1];R=P.parents[2];sys.dont_write_bytecode=True;sys.path[:0]=[str(R/'tools'),str(P.parent/'claude_shared')]
import merge_head_material as G
import build_actor_lods as L
import split_attachment as A
manifest=json.loads((P/'work/reduction/exports_manifest.json').read_text());E=P/'export'
def append_resources(doc,binary,source,data):
 vo,ao,io,to,so,mo=[len(doc.setdefault(k,[]))for k in ['bufferViews','accessors','images','textures','samplers','materials']]
 binary.extend(b'\0'*(-len(binary)%4));offset=len(binary);binary.extend(data)
 for x in source.get('bufferViews',[]):
  y=copy.deepcopy(x);assert y['buffer']==0;y['byteOffset']=y.get('byteOffset',0)+offset;doc['bufferViews'].append(y)
 for x in source.get('accessors',[]):
  y=copy.deepcopy(x);assert 'sparse'not in y
  if 'bufferView'in y:y['bufferView']+=vo
  doc['accessors'].append(y)
 for x in source.get('images',[]):
  y=copy.deepcopy(x);assert 'bufferView'in y;y['bufferView']+=vo;doc['images'].append(y)
 doc['samplers'].extend(copy.deepcopy(source.get('samplers',[])))
 for x in source.get('textures',[]):
  y=copy.deepcopy(x);y['source']+=io
  if 'sampler'in y:y['sampler']+=so
  doc['textures'].append(y)
 def texture_refs(x):
  if isinstance(x,dict):
   for k,v in x.items():
    if k.endswith('Texture') and isinstance(v,dict) and 'index'in v:v['index']+=to
    else:texture_refs(v)
  elif isinstance(x,list):
   for v in x:texture_refs(v)
 for x in source.get('materials',[]):
  y=copy.deepcopy(x);texture_refs(y);doc['materials'].append(y)
 meshes=copy.deepcopy(source.get('meshes',[]))
 for m in meshes:
  for p in m['primitives']:
   p['attributes']={k:v+ao for k,v in p['attributes'].items()};p['indices']+=ao
   if 'material'in p:p['material']+=mo
 return meshes
def authoritative_mr(doc,binary,entry):
 for mat in doc['materials']:
  name=mat['name'];isclub='Club'in name;ishead='Head'in name;folder=P/entry['club'if isclub else'body']['textures'];i=2 if 'Hands' in name else (1 if ishead else 0)
  path=folder/f'{i}_metal_rough.png'
  assert path.exists(),path
  index=G.add_image(doc,binary,Image.open(path).convert('RGB'),name+'_specular_roughness_metal',None)
  mat['pbrMetallicRoughness']['metallicRoughnessTexture']={'index':index};mat['extras']={'openyamm_specular_mask':True,'openyamm_specular':1.0};assert not mat.get('extensions'),mat
def normalise(doc,binary):
 maximum=0
 for mesh in doc['meshes']:
  for prim in mesh['primitives']:
   attrs=prim['attributes'];names=[n for n in attrs if n.startswith('WEIGHTS_')]
   if not names:continue
   arrays=[G.accessor_array(doc,binary,attrs[n]).astype(np.float64)for n in names];total=sum(a.sum(1)for a in arrays);assert np.all(total>0)
   maximum=max(maximum,float(abs(total-1).max()))
   for name,values in zip(names,arrays):attrs[name]=G.append_accessor(doc,binary,(values/total[:,None]).astype(np.float32),{'componentType':5126,'type':'VEC4'},34962)
 return maximum
doc,binary=G.read_glb(P/manifest[0]['glb']);authoritative_mr(doc,binary,manifest[0]);node=next(n for n in doc['nodes']if 'mesh'in n);assert len(doc['skins'])==1
skin=doc['skins'][node['skin']];joints=[doc['nodes'][i]['name']for i in skin['joints']];binds=G.accessor_array(doc,binary,skin['inverseBindMatrices'])
meshes=[copy.deepcopy(doc['meshes'][node['mesh']])];node['mesh']=0
for entry in manifest[1:]:
 src,data=G.read_glb(P/entry['glb']);authoritative_mr(src,data,entry);sn=next(n for n in src['nodes']if 'mesh'in n);ss=src['skins'][sn['skin']];remap=np.array([joints.index(src['nodes'][i]['name'])for i in ss['joints']]);sb=G.accessor_array(src,data,ss['inverseBindMatrices']);assert np.max(abs(sb-binds[remap]))<1e-4
 for k,default in [('translation',[0,0,0]),('rotation',[0,0,0,1]),('scale',[1,1,1])]:assert np.max(abs(np.array(node.get(k,default))-sn.get(k,default)))<1e-4
 appended=append_resources(doc,binary,src,data);mesh=appended[sn['mesh']];mesh['name']=f'Merchant_LOD{entry["level"]}'
 for prim in mesh['primitives']:
  for name,idx in list(prim['attributes'].items()):
   if name.startswith('JOINTS_'):
    values=G.accessor_array(doc,binary,idx);prim['attributes'][name]=G.append_accessor(doc,binary,remap[values].astype(values.dtype),doc['accessors'][idx],34962)
 meshes.append(mesh)
doc['meshes']=meshes;normalise(doc,binary)
# Retain a standard combined LOD0 with the club for the viewer and portable tier exports.
single=copy.deepcopy(doc);single['meshes']=single['meshes'][:1];single,b0=G.compact(single,bytearray(binary));G.write_glb(E/'mm6_mer1_runtime_lod0.glb',single,b0)
for mesh in meshes[:4]:doc['meshes'].append(L.merge_shadow(doc,binary,mesh))
doc['meshes'][0]['extras']={'openyamm_lods':[1,2,3],'openyamm_shadow_lods':[4,5,6,7]};error=normalise(doc,binary);doc,binary=G.compact(doc,binary);G.write_glb(E/'mm6_mer1_lods.glb',doc,binary)
ramps=json.loads((P/'textures/round3/mer1_ramps.json').read_text());entries=[]
for entry in manifest:
 e=copy.deepcopy(ramps['materials'][0]);level=entry['level'];e['base']=f'MerchantL{level}_A';e['prefix']=f'MerchantL{level}';e['mask']=str((P/entry['body']['textures']/'0_region_mask.png').resolve());entries.append(e)
config={'variants':ramps['variants'],'materials':entries};rp=P/'work/reduction/runtime_ramps.json';rp.write_text(json.dumps(config,indent=2))
subprocess.run([sys.executable,str(P.parent/'claude_shared/region_variants.py'),str(E/'mm6_mer1_lods.glb'),str(E/'mm6_mer1_regions.glb'),str(rp)],check=True)
subprocess.run([sys.executable,str(R/'tools/split_attachment.py'),str(E/'mm6_mer1_regions.glb'),'--joint','Club','--body',str(E/'mm6_mer1_unmerged.glb'),'--attachment',str(E/'mm6_mer1_club.glb')],check=True)
# Keep head and hands separate, with their original UV coordinates.
shutil.copyfile(E/'mm6_mer1_unmerged.glb',E/'mm6_mer1.glb')
# Each independently rebaked club LOD has its own UV chart and texture; preserve these with the shared extractor.
rd,rb=G.read_glb(E/'mm6_mer1_regions.glb');joint_node=next(i for i,n in enumerate(rd['nodes'])if n.get('name')=='Club');ss=rd['skins'][0];js=ss['joints'].index(joint_node);ib=G.accessor_array(rd,rb,ss['inverseBindMatrices'])[js].reshape(4,4).T
attachment=None;ab=None;ame=[]
for level in range(4):
 items=[]
 for prim in rd['meshes'][level]['primitives']:
  _,indices=A.split_primitive(rd,rb,prim,js)
  if len(indices):items.append((level,prim,indices))
 assert len(items)==1
 ad,adbin=A.build_attachment(rd,rb,items,ib,[rd['materials'][items[0][1]['material']]],[],'Club')
 if attachment is None:attachment,ab=ad,bytearray(adbin);ame=[copy.deepcopy(ad['meshes'][0])]
 else:ame.append(append_resources(attachment,ab,ad,adbin)[0])
attachment['meshes']=ame
for mesh in ame[:4]:attachment['meshes'].append(L.merge_shadow(attachment,ab,mesh))
attachment['meshes'][0]['extras']={'openyamm_lods':[1,2,3],'openyamm_shadow_lods':[4,5,6,7]};attachment,ab=G.compact(attachment,ab);G.write_glb(E/'mm6_mer1_club.glb',attachment,ab)
report={'body_triangles':[entry['body']['triangles']for entry in manifest],'club_triangles':[entry['club']['triangles']for entry in manifest],'weight_error_before_final_normalisation':error,'body_draws_per_lod':3,'texture_sets':{'clothing':[2048,2048],'head':[1024,1024],'hands':[512,512]},'tiers':ramps['variants'],'clips':[a['name']for a in single['animations']]}
(P/'review/runtime_package.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
