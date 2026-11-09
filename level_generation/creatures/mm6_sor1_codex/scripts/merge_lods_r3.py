"""Combine independently rebaked LODs while retaining LOD0's rig and all animation payloads."""
from pathlib import Path
import sys,copy,json,struct,shutil
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p.parents[2]/'tools'));from build_actor_lods import read_glb,write_glb,accessor_bytes,append_accessor,merge_shadow
shutil.copyfile(p/'export/mm6_sor1_lod0.glb',p/'export/mm6_sor1_runtime_lod0.glb')
d,b0=read_glb(p/'export/mm6_sor1_lod0.glb');b=bytearray(b0);node=next(n for n in d['nodes'] if n.get('name')=='Sorcerer');root=node['mesh'];skin=d['skins'][node['skin']];names=[d['nodes'][i]['name'] for i in skin['joints']];bind=list(struct.iter_unpack('<16f',accessor_bytes(d,b,skin['inverseBindMatrices'])));indices=[]
for level in range(1,4):
 a,z=read_glb(p/'export'/f'mm6_sor1_lod{level}.glb');n=next(n for n in a['nodes'] if n.get('name')=='Sorcerer');sk=a['skins'][n['skin']];remap=[names.index(a['nodes'][i]['name']) for i in sk['joints']];matrices=list(struct.iter_unpack('<16f',accessor_bytes(a,z,sk['inverseBindMatrices'])))
 assert max(abs(x-y) for i,m in zip(remap,matrices) for x,y in zip(bind[i],m))<1e-4
 for key,default in [('translation',[0,0,0]),('rotation',[0,0,0,1]),('scale',[1,1,1])]:assert max(abs(x-y) for x,y in zip(node.get(key,default),n.get(key,default)))<1e-4
 offsets={k:len(d.get(k,[])) for k in ['samplers','images','textures','materials']}
 d.setdefault('samplers',[]).extend(copy.deepcopy(a.get('samplers',[])))
 for im in a.get('images',[]):
  v=a['bufferViews'][im['bufferView']];start=v.get('byteOffset',0);b.extend(b'\0'*(-len(b)%4));d['bufferViews'].append({'buffer':0,'byteOffset':len(b),'byteLength':v['byteLength']});b.extend(z[start:start+v['byteLength']]);im=copy.deepcopy(im);im['bufferView']=len(d['bufferViews'])-1;d['images'].append(im)
 for tx in a.get('textures',[]):
  tx=copy.deepcopy(tx);tx['source']+=offsets['images']
  if 'sampler' in tx:tx['sampler']+=offsets['samplers']
  d['textures'].append(tx)
 def textures(x):
  if isinstance(x,dict):
   for k,v in x.items():
    if k.endswith('Texture') and isinstance(v,dict) and 'index' in v:v['index']+=offsets['textures']
    else:textures(v)
  elif isinstance(x,list):
   for v in x:textures(v)
 for m in a['materials']:m=copy.deepcopy(m);textures(m);d['materials'].append(m)
 mesh={'name':f'Sorcerer_LOD{level}','primitives':[]}
 for pr in a['meshes'][n['mesh']]['primitives']:
  attrs={}
  for key,ix in pr['attributes'].items():
   ac=a['accessors'][ix];data=accessor_bytes(a,z,ix)
   if key.startswith('JOINTS_'):
    code={5121:'B',5123:'H'}[ac['componentType']];values=[remap[v[0]] for v in struct.iter_unpack('<'+code,data)];data=struct.pack('<'+code*len(values),*values)
   attrs[key]=append_accessor(d,b,ac,data)
  ix=pr['indices'];mesh['primitives'].append({'attributes':attrs,'indices':append_accessor(d,b,a['accessors'][ix],accessor_bytes(a,z,ix)),'material':pr['material']+offsets['materials']})
 indices.append(len(d['meshes']));d['meshes'].append(mesh)
shadows=[]
for ix in [root,*indices]:
 shadows.append(len(d['meshes']));d['meshes'].append(merge_shadow(d,b,d['meshes'][ix]))
d['meshes'][root].setdefault('extras',{}).update(openyamm_lods=indices,openyamm_shadow_lods=shadows)
write_glb(p/'export/mm6_sor1_lods.glb',d,b)
# Same packaged LOD meshes, same LOD0 animation buffers, isolated only for the Blender reimport audit.
for level,ix in enumerate([root,*indices]):
 audit=copy.deepcopy(d);next(n for n in audit['nodes'] if n.get('name')=='Sorcerer')['mesh']=ix;write_glb(p/'work'/f'round3_lod{level}_audit.glb',audit,b)
ramps=json.loads((p/'textures/sor1_ramps.json').read_text());entry=ramps['materials'][0];ramps['materials']=[]
for level in range(4):
 e=copy.deepcopy(entry);e['base']='Sorcerer'+(f'LOD{level}' if level else '')+'_A';e['prefix']='Sorcerer'+(f'LOD{level}' if level else '');e['mask']=f'r3_lod{level}_Sorcerer_mask.png';ramps['materials'].append(e)
(p/'textures/round3/ramps.json').write_text(json.dumps(ramps,indent=2))
counts=[sum(d['accessors'][pr['indices']]['count']//3 for pr in d['meshes'][ix]['primitives']) for ix in [root,*indices]];assert all(x>y for x,y in zip(counts,counts[1:]));print('LOD counts',counts)
(p/'work/prepare_runtime.log').write_text('Round 3 Cycles tangent-space +Y rebake; no green-channel heuristic applied.\n')
