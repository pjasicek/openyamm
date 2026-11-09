"""Pack all measured LOD UV charts into one texture set with 16-pixel dilated chart borders."""
import sys,json,copy,hashlib,io,math
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import distance_transform_edt,binary_dilation
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P.parents[2]/'tools'));import merge_head_material as G
slots=[('base',('pbrMetallicRoughness','baseColorTexture')),('mr',('pbrMetallicRoughness','metallicRoughnessTexture')),('normal',('normalTexture',)),('region',('extras','openyamm_region_mask'))]
def slot(d,path):
 for k in path:
  if k not in d:return None
  d=d[k]
 return d
def put(d,path,v):
 for k in path[:-1]:d=d.setdefault(k,{})
 d[path[-1]]=v
def image(d,b,idx):
 im=d['images'][d['textures'][idx]['source']];v=d['bufferViews'][im['bufferView']];return Image.open(io.BytesIO(b[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']])).convert('RGBA')
report={}
for actor in ['mm6_mer1','mm6_mer1_club']:
 path=P/'export'/f'{actor}.glb';d,b=G.read_glb(path);old_images=len(d['images']);charts=[];levels=[];pixels={}
 for level in range(4):
  prim=d['meshes'][level]['primitives'][0];assert len(d['meshes'][level]['primitives'])==1
  mat=d['materials'][prim['material']];maps={key:image(d,b,slot(mat,sp)['index'])for key,sp in slots if slot(mat,sp)};sizes={m.size for m in maps.values()};assert len(sizes)==1;w,h=sizes.pop()
  uv=G.accessor_array(d,b,prim['attributes']['TEXCOORD_0']).copy();faces=G.accessor_array(d,b,prim['indices']).reshape(-1,3);parent=np.arange(len(uv))
  def root(i):
   while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
   return i
  for a,c,e in faces:
   r=root(a);parent[root(c)]=r;parent[root(e)]=r
  # Rejoin split normal vertices along an unchanged UV seam.
  seen={}
  for i,v in enumerate(uv):
   key=tuple(np.round(v,7))
   if key in seen:parent[root(i)]=root(seen[key])
   else:seen[key]=i
  roots=np.array([root(i)for i in range(len(uv))]);coords=uv*np.array([w,h]);new=np.zeros_like(uv)
  for r in np.unique(roots):
   ids=np.where(roots==r)[0];fs=faces[np.all(roots[faces]==r,axis=1)];lo=np.maximum(0,np.floor(coords[ids].min(0)).astype(int)-1);hi=np.minimum([w,h],np.ceil(coords[ids].max(0)).astype(int)+1)
   size=hi-lo;assert min(size)>0;mask=Image.new('L',tuple(size));draw=ImageDraw.Draw(mask)
   for face in fs:draw.polygon([tuple(x)for x in coords[face]-lo],fill=255)
   valid=binary_dilation(np.asarray(mask)>0,iterations=1);assert valid.any()
   padded=np.pad(valid,16);nearest=distance_transform_edt(~padded,return_distances=False,return_indices=True)
   charts.append({'level':level,'ids':ids,'lo':lo,'size':tuple(size+32),'nearest':nearest,'maps':maps,'uv':uv,'old_size':(w,h),'new_uv':new})
  levels.append((prim,new,mat))
 def pack(width):
  shelves=[];places={}
  for idx,ch in sorted(enumerate(charts),key=lambda v:(-v[1]['size'][1],-v[1]['size'][0])):
   w,h=ch['size']
   if w>width:return None
   possible=[(width-s['x']-w,j)for j,s in enumerate(shelves)if s['h']>=h and s['x']+w<=width]
   if possible:j=min(possible)[1];s=shelves[j]
   else:s={'x':0,'y':sum(s['h']for s in shelves),'h':h};shelves.append(s)
   places[idx]=(s['x'],s['y']);s['x']+=w
  height=int(math.ceil(sum(s['h']for s in shelves)/64)*64);return width*height,width,height,places
 candidates=[x for w in [2048,3072,4096,6144,8192]if (x:=pack(w)) is not None];_,aw,ah,places=min(candidates,key=lambda x:x[0])
 atlases={key:Image.new('RGBA',(aw,ah),(0,0,0,255))for key in charts[0]['maps']};max_pixel_error=0
 for idx,ch in enumerate(charts):
  x,y=places[idx];lo=ch['lo'];w,h=ch['size'];cw,chh=w-32,h-32;ys,xs=ch['nearest'];ys=np.clip(ys-16,0,chh-1);xs=np.clip(xs-16,0,cw-1)
  for key,im in ch['maps'].items():
   crop=np.asarray(im)[lo[1]:lo[1]+chh,lo[0]:lo[0]+cw];tile=Image.fromarray(crop[ys,xs]);atlases[key].paste(tile,(x,y))
  old=ch['uv'][ch['ids']]*ch['old_size'];new=(old-lo+[x+16,y+16])/[aw,ah];ch['new_uv'][ch['ids']]=new
  reverse=ch['new_uv'][ch['ids']]*[aw,ah]-[x+16,y+16]+lo
  max_pixel_error=max(max_pixel_error,float(abs(reverse-old).max()))
 assert max_pixel_error<.002,max_pixel_error
 textures={key:G.add_image(d,b,im,actor+'_'+key+'_shared_atlas',None)for key,im in atlases.items()};canonical={}
 for level,(prim,uv,mat)in enumerate(levels):
  acc=prim['attributes']['TEXCOORD_0'];prim['attributes']['TEXCOORD_0']=G.append_accessor(d,b,uv.astype(np.float32),d['accessors'][acc],34962)
  ids=[prim['material']]+[m['material']for m in prim.get('extensions',{}).get('KHR_materials_variants',{}).get('mappings',[])]
  for i in set(ids):
   m=d['materials'][i]
   for key,sp in slots:
    if key in textures:put(m,sp,{'index':textures[key]})
   sig=copy.deepcopy(m);sig.pop('name',None);k=json.dumps(sig,sort_keys=True)
   canonical.setdefault(k,i)
  def canonical_id(i):
   sig=copy.deepcopy(d['materials'][i]);sig.pop('name',None);return canonical[json.dumps(sig,sort_keys=True)]
  prim['material']=canonical_id(prim['material'])
  for m in prim.get('extensions',{}).get('KHR_materials_variants',{}).get('mappings',[]):m['material']=canonical_id(m['material'])
 shadow=len(d['materials']);d['materials'].append({'name':'OpaqueShadow','alphaMode':'OPAQUE','doubleSided':True,'pbrMetallicRoughness':{'baseColorFactor':[1,1,1,1],'metallicFactor':0,'roughnessFactor':1}})
 for mesh in d['meshes'][4:]:
  for prim in mesh['primitives']:prim['material']=shadow;prim.pop('extensions',None);prim['attributes'].pop('TEXCOORD_0',None)
 d,b=G.compact(d,b);G.write_glb(path,d,b);assert len(d['images'])==len(atlases)
 report[actor]={'images_before':old_images,'images_after':len(d['images']),'maps':list(atlases),'atlas_size':[aw,ah],'charts':len(charts),'margin_pixels':16,'texel_density':'unchanged; charts translated only','uv_texel_error_max':max_pixel_error,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
(P/'review/shared_texture_atlases.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
