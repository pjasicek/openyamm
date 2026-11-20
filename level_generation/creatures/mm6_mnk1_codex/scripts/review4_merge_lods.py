"""Attach validated mesh LODs while retaining the runtime rig, clips and material images verbatim."""
import copy,json,struct,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p.parents[2]/'tools'));import build_actor_lods as G
doc,data=G.read_glb(p/'export/mm6_mnk1_runtime_lod0.glb');binary=bytearray(data);node=next(n for n in doc['nodes'] if n.get('name')=='Monk');base=node['mesh'];skin=doc['skins'][node['skin']];names=[doc['nodes'][i]['name'] for i in skin['joints']];bind=list(struct.iter_unpack('<16f',G.accessor_bytes(doc,data,skin['inverseBindMatrices'])));lods=[]
for level in range(1,4):
 src,buf=G.read_glb(p/f'work/review4_lod{level}.geometry.glb');n=next(n for n in src['nodes'] if 'mesh' in n);s=src['skins'][n['skin']];remap=[names.index(src['nodes'][i]['name']) for i in s['joints']];matrices=list(struct.iter_unpack('<16f',G.accessor_bytes(src,buf,s['inverseBindMatrices'])));assert max(abs(a-b) for i,m in zip(remap,matrices) for a,b in zip(bind[i],m))<1e-4
 for key,default in [('translation',[0,0,0]),('rotation',[0,0,0,1]),('scale',[1,1,1])]:assert max(abs(a-b) for a,b in zip(n.get(key,default),node.get(key,default)))<1e-4
 mesh={'name':f'Monk_LOD{level}','primitives':[]}
 for prim in src['meshes'][n['mesh']]['primitives']:
  attrs={}
  for sem,ai in prim['attributes'].items():
   accessor=src['accessors'][ai];packed=G.accessor_bytes(src,buf,ai)
   if sem.startswith('JOINTS_'):
    code={5121:'B',5123:'H'}[accessor['componentType']];values=[remap[x[0]] for x in struct.iter_unpack('<'+code,packed)];packed=struct.pack('<'+code*len(values),*values)
   attrs[sem]=G.append_accessor(doc,binary,accessor,packed)
  ai=prim['indices'];material=next(i for i,m in enumerate(doc['materials']) if m['name']==src['materials'][prim['material']]['name']);mesh['primitives'].append(dict(attributes=attrs,indices=G.append_accessor(doc,binary,src['accessors'][ai],G.accessor_bytes(src,buf,ai)),material=material))
 lods.append(len(doc['meshes']));doc['meshes'].append(mesh)
shadows=[]
for mi in [base]+lods:shadows.append(len(doc['meshes']));doc['meshes'].append(G.merge_shadow(doc,binary,doc['meshes'][mi]))
doc['meshes'][base].setdefault('extras',{}).update(openyamm_lods=lods,openyamm_shadow_lods=shadows);counts=[sum(doc['accessors'][q['indices']]['count']//3 for q in doc['meshes'][mi]['primitives']) for mi in [base]+lods];assert all(a>b for a,b in zip(counts,counts[1:])) and all(n<=min(cap,counts[0]*ratio) for n,cap,ratio in zip(counts[1:],[6212,2235,744],[.55,.25,.10]));G.write_glb(p/'export/mm6_mnk1_lods.glb',doc,binary);(p/'export/lods.json').write_text(json.dumps(dict(triangles=counts,colour_meshes=[base]+lods,shadow_meshes=shadows,original_geometry_rig_clips_images_retained=True),indent=2));print('LOD_CHAIN',counts)
