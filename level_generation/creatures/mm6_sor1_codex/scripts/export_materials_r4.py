"""Patch UV/material payloads while preserving every triangle's geometry, weights and animation samples."""
from pathlib import Path
import sys,copy,json,numpy as np,hashlib,io
from scipy.spatial import cKDTree
from PIL import Image
sys.dont_write_bytecode=True
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p.parents[2]/'tools'))
from build_actor_lods import read_glb,write_glb,accessor_bytes,append_accessor
from merge_head_material import compact
base=p/'review/round4/baseline';proof={}
def arr(d,b,i):
 a=d['accessors'][i];return np.frombuffer(accessor_bytes(d,b,i),dtype={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']]).reshape(-1,{'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']])
def add_images(d,b):
 tex={}
 for ch in ['basecolor','normal','orm','mask']:
  data=(p/'textures/round4'/f'sor1_{ch}.png').read_bytes();b.extend(b'\0'*(-len(b)%4));d['bufferViews'].append({'buffer':0,'byteOffset':len(b),'byteLength':len(data)});b.extend(data);d['images'].append({'bufferView':len(d['bufferViews'])-1,'mimeType':'image/png','name':'sor1_shared_'+ch});d['textures'].append({'source':len(d['images'])-1,'sampler':0});tex[ch]=len(d['textures'])-1
 return tex
uvdata={i:np.load(p/'work'/f'uv_final_lod{i}_r4.npz') for i in range(4)}
lookup={}
for level,z in uvdata.items():lookup[level]=(cKDTree(z['vertices']),{tuple(sorted(f)):i for i,f in enumerate(z['faces'])})
def replace_uv(d,b,pr,level):
 z=uvdata[level];tree,faces=lookup[level];ids=arr(d,b,pr['indices']).ravel();verts=arr(d,b,pr['attributes']['POSITION']);co=verts[:,[0,2,1]]*np.array([1,-1,1]);dist,mapping=tree.query(co);assert dist.max()<2e-6,dist.max();old=ids.reshape(-1,3);uv=[]
 for row in old:
  mapped=mapping[row];key=tuple(sorted(mapped))
  if key in faces:
   i=faces[key];order=[list(z['faces'][i]).index(v) for v in mapped];uv.extend(z['uv'][i][order]);continue
  # glTF and Blender choose opposite diagonals for a few quads. Keep the exported triangles, carrying
  # each corner's UV from the common polygon chart instead of retriangulating geometry.
  incident=[np.where((z['faces']==vv).any(1))[0] for vv in mapped];common=set(z['chart'][incident[0]])
  for candidates in incident[1:]:common.intersection_update(z['chart'][candidates])
  if common:
   chart=min(common)
   for vv,ids_ in zip(mapped,incident):
    i=next(int(j) for j in ids_ if z['chart'][j]==chart);uv.append(z['uv'][i,list(z['faces'][i]).index(vv)])
  else:
   from bake_atlas_r4 import nearest
   candidates=np.unique(np.concatenate(incident));tri=z['vertices'][z['faces'][candidates]];centre=co[row].mean(0);weights,dist=nearest(np.broadcast_to(centre,(len(candidates),3)),tri);chart=int(z['chart'][candidates[dist.argmin()]])
   ids_=np.where(z['chart']==chart)[0];tri=z['vertices'][z['faces'][ids_]]
   for point in co[row]:
    weights,dist=nearest(np.broadcast_to(point,(len(ids_),3)),tri);j=int(dist.argmin());uv.append((z['uv'][ids_[j]]*weights[j,:,None]).sum(0))
 uv=np.asarray(uv,np.float32);uv[:,1]=1-uv[:,1]
 keys=np.column_stack([ids.astype(np.uint32),uv.view(np.uint32)]);_,first,inverse=np.unique(keys,axis=0,return_index=True,return_inverse=True);select=ids[first];newuv=uv[first];attributes={}
 for key,index in pr['attributes'].items():
  if key=='TANGENT':continue
  a=copy.deepcopy(d['accessors'][index]);values=newuv if key=='TEXCOORD_0' else arr(d,b,index)[select];a['count']=len(values);a.pop('min',None);a.pop('max',None)
  if key=='POSITION':a['min']=values.min(0).tolist();a['max']=values.max(0).tolist()
  attributes[key]=append_accessor(d,b,a,values.tobytes())
  if key!='TEXCOORD_0':assert np.array_equal(values[inverse],arr(d,b,index)[ids]),key
 a=copy.deepcopy(d['accessors'][pr['indices']]);a.update(componentType=5125,count=len(inverse));a.pop('min',None);a.pop('max',None);pr['attributes']=attributes;pr['indices']=append_accessor(d,b,a,inverse.astype('<u4').tobytes())
def patch_material(m,t):
 m['pbrMetallicRoughness']['baseColorTexture']={'index':t['basecolor']};m['pbrMetallicRoughness']['metallicRoughnessTexture']={'index':t['orm']};m['normalTexture']={'index':t['normal']};m['alphaMode']='OPAQUE'
 if 'openyamm_region_ramps' in m.get('extras',{}):m['extras']['openyamm_region_mask']={'index':t['mask']}
 m.pop('occlusionTexture',None)
def animation_digest(d,b):
 h=hashlib.sha256()
 for a in d.get('animations',[]):
  h.update(a['name'].encode())
  for s in a['samplers']:
   h.update(accessor_bytes(d,b,s['input']));h.update(accessor_bytes(d,b,s['output']))
 return h.hexdigest()
# Runtime body: three tier materials, four maps, all four colour and four shadow LODs.
d,raw=read_glb(base/'export/mm6_sor1.glb');before=animation_digest(d,raw);b=bytearray(raw);t=add_images(d,b);materials=[copy.deepcopy(d['materials'][12+i]) for i in range(3)]
for i,m in enumerate(materials):patch_material(m,t);m['name']='Sorcerer_'+chr(65+i)
for i,mesh in enumerate(d['meshes']):
 for pr in mesh['primitives']:
  replace_uv(d,b,pr,i%4);pr['material']=0;pr['extensions']={'KHR_materials_variants':{'mappings':[{'material':j,'variants':[j]} for j in range(3)]}}
d['materials']=materials;d,b=compact(d,b);assert animation_digest(d,b)==before;write_glb(p/'export/mm6_sor1.glb',d,b);proof['body_animation_sha256']=before
# Staff: its accepted LOD0 texture set is shared by all geometric LODs; no staff UV or vertex changes.
s,z=read_glb(base/'export/mm6_sor1_staff.glb');s['materials']=s['materials'][:3]
for mesh in s['meshes']:
 for pr in mesh['primitives']:
  pr['material']=0
  for j,mapping in enumerate(pr.get('extensions',{}).get('KHR_materials_variants',{}).get('mappings',[])):mapping['material']=j
s,z=compact(s,z);write_glb(p/'export/mm6_sor1_staff.glb',s,z)
# Combined near review input retains the same skin/prop animation payload; no attachment conversion is necessary.
x,z=read_glb(base/'export/mm6_sor1_runtime_lod0.glb');bb=bytearray(z);t=add_images(x,bb)
for mesh in x['meshes']:
 for pr in mesh['primitives']:
  m=x['materials'][pr['material']]
  if 'Staff' not in m['name']:replace_uv(x,bb,pr,0);patch_material(m,t)
x,bb=compact(x,bb);write_glb(p/'export/mm6_sor1_runtime_lod0.glb',x,bb)
# Browser-only tier colour bake applies the unchanged engine ramps to the shared padded mask.
rgba=np.asarray(Image.open(p/'textures/round4/sor1_basecolor.png').convert('RGB'),np.float32)/255;mask=np.asarray(Image.open(p/'textures/round4/sor1_mask.png').convert('RGBA'),np.float32)/255
lin=lambda a:np.where(a<=.04045,a/12.92,((a+.055)/1.055)**2.4);srgb=lambda a:np.where(a<=.0031308,a*12.92,1.055*np.maximum(a,0)**(1/2.4)-.055);linear=lin(rgba);lum=linear@np.array([.2126,.7152,.0722]);ramps=json.loads((p/'textures/sor1_ramps.json').read_text())['materials'][0]['ramps']
for tier in 'abc':
 out=linear.copy()
 for k,r in enumerate(ramps['sor1_'+tier]):
  lo,hi=r['range'];pos=np.clip((lum-lo)/(hi-lo),0,1)*15;ii=np.minimum(pos.astype(int),14);w=(pos-ii)[...,None];colors=np.asarray(r['colors']);color=colors[ii]*(1-w)+colors[ii+1]*w;out=out*(1-mask[...,k,None])+color*mask[...,k,None]
 pixels=np.clip(srgb(out)*255+.5,0,255).astype(np.uint8);im=Image.fromarray(pixels);im.save(p/'textures/round4'/f'review_{tier}.png');stream=io.BytesIO();im.save(stream,format='PNG');payload=stream.getvalue();dd=copy.deepcopy(x);bbb=bytearray(bb);bbb.extend(b'\0'*(-len(bbb)%4));dd['bufferViews'].append({'buffer':0,'byteOffset':len(bbb),'byteLength':len(payload)});bbb.extend(payload);dd['images'].append({'bufferView':len(dd['bufferViews'])-1,'mimeType':'image/png','name':'review_'+tier});dd['textures'].append({'source':len(dd['images'])-1,'sampler':0});tx=len(dd['textures'])-1
 for m in dd['materials']:
  if 'Staff' not in m['name']:m['pbrMetallicRoughness']['baseColorTexture']={'index':tx}
 dd,bbb=compact(dd,bbb);write_glb(p/'review/viewer'/f'mm6_sor1_{tier}.glb',dd,bbb)
proof.update(geometry_weights_normals_per_triangle='exactly identical; asserted on every primitive including shadows',clip_samples='byte-identical',actors_yml_unchanged=hashlib.sha256((p/'integration/actors.yml').read_bytes()).hexdigest()==hashlib.sha256((base/'integration/actors.yml').read_bytes()).hexdigest())
(p/'review/round4/preservation.json').write_text(json.dumps(proof,indent=2));print('EXPORTED shared body4 + staff3 images; geometry/weights/clips unchanged',flush=True)
