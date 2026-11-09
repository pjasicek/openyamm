"""Package rebaked per-LOD materials using shared variant, attachment and head-atlas tools."""
import sys,json,copy,struct,shutil,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];R=P.parents[2];sys.dont_write_bytecode=True;sys.path[:0]=[str(R/'tools'),str(P.parent/'claude_shared')]
from merge_head_material import read_glb,write_glb,compact,TEXTURE_SLOTS,slot
from build_actor_lods import accessor_bytes,append_accessor,merge_shadow
import region_variants,split_attachment,merge_head_material
selection=json.loads((P/'review/rebake/final_selection.json').read_text());base_config=json.loads((P/'textures/lzd_ramps.json').read_text());W=P/'work/rebake_pack';W.mkdir(exist_ok=True)
def invoke(module,args):
 sys.argv=[module.__file__,*map(str,args)];module.main()
def clean(doc):
 for m in doc.get('materials',[]):m.pop('extensions',None)
 for key in ['extensionsUsed','extensionsRequired']:
  if key in doc:
   doc[key]=[x for x in doc[key]if not x.startswith('KHR_materials_') or x=='KHR_materials_variants']
   if not doc[key]:doc.pop(key)
def merge_levels(paths,destination):
 d,b=read_glb(paths[0]);b=bytearray(b);assert len(d['meshes'])==1
 base_node=next(n for n in d['nodes']if n.get('mesh')==0)
 if d.get('skins'):
  skin=d['skins'][base_node['skin']];names=[d['nodes'][i]['name']for i in skin['joints']];ib=list(struct.iter_unpack('<16f',accessor_bytes(d,b,skin['inverseBindMatrices'])))
 for level,path in enumerate(paths[1:],1):
  low,lb=read_glb(path);assert len(low['meshes'])==1
  offsets={k:len(d.setdefault(k,[]))for k in ['bufferViews','accessors','images','textures','samplers','materials']}
  b.extend(b'\0'*(-len(b)%4));byte_offset=len(b);b.extend(lb)
  for v in low['bufferViews']:d['bufferViews'].append(dict(v,byteOffset=v.get('byteOffset',0)+byte_offset))
  for v in low['accessors']:d['accessors'].append(dict(v,bufferView=v['bufferView']+offsets['bufferViews']))
  for v in low.get('images',[]):d['images'].append(dict(v,bufferView=v['bufferView']+offsets['bufferViews']))
  d['samplers'].extend(copy.deepcopy(low.get('samplers',[])))
  for v in low.get('textures',[]):
   v=copy.deepcopy(v);v['source']+=offsets['images']
   if 'sampler'in v:v['sampler']+=offsets['samplers']
   d['textures'].append(v)
  for m in low['materials']:
   m=copy.deepcopy(m)
   for path in TEXTURE_SLOTS:
    info=slot(m,path)
    if info is not None:info['index']+=offsets['textures']
   d['materials'].append(m)
  if d.get('skins'):
   ln=next(n for n in low['nodes']if n.get('mesh')==0);sk=low['skins'][ln['skin']];remap=[names.index(low['nodes'][i]['name'])for i in sk['joints']]
   matrices=list(struct.iter_unpack('<16f',accessor_bytes(low,lb,sk['inverseBindMatrices'])));assert max(abs(x-y)for i,m in zip(remap,matrices)for x,y in zip(ib[i],m))<1e-4
  mesh=copy.deepcopy(low['meshes'][0]);mesh.pop('extras',None);mesh['name']=d['meshes'][0]['name']+f'_LOD{level}'
  for prim,original in zip(mesh['primitives'],low['meshes'][0]['primitives']):
   prim['material']+=offsets['materials'];prim['indices']+=offsets['accessors']
   for mapping in prim.get('extensions',{}).get('KHR_materials_variants',{}).get('mappings',[]):mapping['material']+=offsets['materials']
   for semantic,index in original['attributes'].items():
    prim['attributes'][semantic]=index+offsets['accessors']
    if semantic.startswith('JOINTS_'):
     packed=accessor_bytes(low,lb,index);acc=low['accessors'][index];code={5121:'B',5123:'H'}[acc['componentType']];values=[remap[v[0]]for v in struct.iter_unpack('<'+code,packed)]
     prim['attributes'][semantic]=append_accessor(d,b,acc,struct.pack('<'+code*len(values),*values))
  d['meshes'].append(mesh)
 counts=[sum(d['accessors'][p['indices']]['count']//3 for p in m['primitives'])for m in d['meshes']]
 assert all(a>b for a,b in zip(counts,counts[1:])),counts
 shadows=[]
 for mesh in list(d['meshes']):
  shadows.append(len(d['meshes']));d['meshes'].append(merge_shadow(d,b,mesh))
 d['meshes'][0]['extras']={'openyamm_lods':[1,2,3],'openyamm_shadow_lods':shadows}
 write_glb(destination,*compact(d,b));return counts
combined=[];bodies=[];bows=[]
for level in range(4):
 tag=selection[str(level)]['tag'];metadata=json.loads((P/f'review/rebake/{tag}_bake.json').read_text());source=P/'export/mm6_lzd_lod0.glb'if level==0 else P/f'export/mm6_lzd_level{level}.glb'
 d,b=read_glb(source);assert all(i['mimeType']=='image/png'for i in d['images']);clean(d);assert len(d['meshes'])==1;d['meshes'][0].setdefault('extras',{})['openyamm_lods']=[]
 stage=W/f'level{level}.glb';write_glb(stage,d,b);entries=[]
 for group,item in metadata.items():
  old=next(x for x in base_config['materials']if x['base']==item['base_material']);entry=copy.deepcopy(old);entry['base']=item['material'];entry['prefix']=old['prefix']+(f'_LOD{level}'if level else'');entry['mask']=str(Path(item['paths']['regions']).relative_to('textures'));entries.append(entry)
 config=P/f'textures/rebake_lod{level}_ramps.json';config.write_text(json.dumps(dict(base_config,materials=entries),indent=2));variant=W/f'level{level}_variants.glb'
 region_variants.apply_variants(stage,variant,config,[('Lizard','openyamm_specular',1),('Lizard','openyamm_specular_mask',True)])
 combined.append(variant);body=W/f'level{level}_body.glb';bow=W/f'level{level}_bow.glb';invoke(split_attachment,[variant,'--joint','Bow','--body',body,'--attachment',bow])
 d,b=read_glb(body);mesh=d['meshes'][0];props=[p for p in mesh['primitives']if 'Bow'in d['materials'][p['material']]['name']];assert len(props)==1
 mesh['primitives'].remove(props[0]);d['meshes'].append({'name':'AnimatedPropReservoir','primitives':props});write_glb(body,d,b);invoke(merge_head_material,[body,body]);d,b=read_glb(body);d['meshes'][0]['primitives']+=d['meshes'].pop()['primitives'];write_glb(body,*compact(d,b));bodies.append(body);bows.append(bow)
counts=merge_levels(combined,P/'export/mm6_lzd_lods.glb')
body_counts=merge_levels(bodies,P/'export/mm6_lzd.glb');bow_counts=merge_levels(bows,P/'export/mm6_lzd_bow.glb')
(P/'export/lods.json').write_text(json.dumps({'triangles':counts,'body':body_counts,'bow':bow_counts,'method':'Per-shell protected reduction and texture rebake; measured at 700/550/220/88 pixels with strictly decreasing counts below the installed chain.'},indent=2))
print('REBAKED_RUNTIME_LODS',body_counts,bow_counts,flush=True)
runpy.run_path(str(P/'scripts/viewer_tiers.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/finalize_materials.py'),run_name='__main__')
