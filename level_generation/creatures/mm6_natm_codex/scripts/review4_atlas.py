"""Consolidate chart islands, retaining pixel density, with independent 16-pixel dilation.
LOD1 reuses near charts; distinct envelope charts share the same atlas and image objects.
"""
import sys,json,copy,math,hashlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import distance_transform_edt,label,map_coordinates
from scipy.signal import fftconvolve
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'))
from merge_head_material import read_glb,write_glb,accessor_array,append_accessor,image_of,add_image,slot,set_slot,compact,TEXTURE_SLOTS
PAD=16;OUT=P/'export';records={}
sys.path.insert(0,str(P/'scripts'));from review4_skin_layers import make_skin_donors,skin_faces,repair_skin_layer
donors=make_skin_donors(P);skin_repairs={}

def place(charts,width):
 step=4;occupancy=np.zeros((1024,width//step),np.float32);positions={};used=0
 for c in sorted(charts,key=lambda c:-max(c['w'],c['h'])):
  cw,ch=c['w'],c['h'];mask=Image.new('L',(cw,ch));draw=ImageDraw.Draw(mask);origin=c['lo']-PAD
  for tri in c['tri']:draw.polygon([tuple(v-origin-.5)for v in tri],fill=255)
  coverage=np.array(mask)>0
  if not coverage.any():coverage[PAD,PAD]=True
  safe=distance_transform_edt(~coverage)<=PAD+1
  options=[]
  for turn in range(4):
   rotated=np.rot90(safe,-turn);rh,rw=rotated.shape;blocks=np.pad(rotated,((0,-rh%step),(0,-rw%step))).reshape((rh+step-1)//step,step,(rw+step-1)//step,step).any((1,3));h,w=blocks.shape
   if w>occupancy.shape[1]:continue
   hits=fftconvolve(occupancy[:min(1024,used+h)],blocks[::-1,::-1],mode='valid');spots=np.argwhere(hits<.1)
   if len(spots):
    y,x=spots[0];options.append((max(used,int(y+h)),int(y),int(x),turn,blocks))
  assert options,'Atlas exceeds 4096 px'
  end,y,x,turn,blocks=min(options,key=lambda q:q[:4]);h,w=blocks.shape;occupancy[y:y+h,x:x+w]+=blocks;assert occupancy.max()<1.5
  if turn:
   rot=np.linalg.matrix_power(np.array([[0,-1],[1,0]]),turn);c['tri']=c['tri']@rot.T;c['rot']=rot@c['rot'];lo=np.floor(c['tri'].min((0,1))-.5).astype(int);hi=np.ceil(c['tri'].max((0,1))+.5).astype(int);c['lo']=lo;c['w'],c['h']=(hi-lo+PAD*2).tolist()
  used=end;positions[c['id']]=(x*step,y*step)
 print('PACKING_OCCUPANCY',float(occupancy.sum()*step*step),float(width*used*step),flush=True)
 return ((used*step+31)//32*32,positions)

for kind,node in [('body','Natm'),('spear','Spear'),('buckler','Buckler')]:
 levels=[];charts=[];sources={};source_groups={};old_pixels=0
 for level in range(4):
  file=OUT/f'mm6_natm_{kind}_lod{level}.glb';doc,buf=read_glb(P/'work/atlas_input'/file.name);mesh=doc['meshes'][next(n['mesh']for n in doc['nodes']if n.get('name')==node)];assert len(mesh['primitives'])==1
  pr=mesh['primitives'][0];uv=accessor_array(doc,buf,pr['attributes']['TEXCOORD_0']).astype(float);faces=accessor_array(doc,buf,pr['indices']).reshape(-1,3);mat=doc['materials'][pr['material']];im=image_of(doc,buf,slot(mat,TEXTURE_SLOTS[0])['index'])[0];w,h=im.size;old_pixels+=w*h
  group=0 if level==1 else level
  if level==1:
   # Head merger has a fixed 32px gutter, so undo its layout before matching the near islands.
   if kind=='body':
    x=uv[:,0]*w;head=x>(w-32)/2+16;uv[:,0]=np.where(head,((x-(w+32)/2)*2+1056)/2080,x*2/2080)
   w,h=sources[0]['size']
  else:
   sources[group]={'size':(w,h),'maps':{path:np.array(image_of(doc,buf,slot(mat,path)['index'])[0].convert('RGBA'))for path in TEXTURE_SLOTS}}
  pixel=uv*np.array([w,h]);entry={'level':level,'file':file,'doc':doc,'buf':buf,'pr':pr,'pixel':pixel,'faces':faces,'group':group};levels.append(entry)
  if kind=='body':
   co=accessor_array(doc,buf,pr['attributes']['POSITION']).astype(float)[:,[0,2,1]]*np.array([1,-1,1]);skin=skin_faces(co,faces)
   for category in [False,True]:
    key=(group,category);sources.setdefault(key,copy.deepcopy(sources[group]));selected=faces[skin==category]
    if category:skin_repairs[str(level)]=repair_skin_layer(sources[key],sources[group],uv,selected,co,donors)
    sub=dict(entry,faces=selected,face_ids=np.flatnonzero(skin==category),group=key);source_groups.setdefault(key,[]).append(sub)
  else:source_groups.setdefault(group,[]).append(entry)
 for group,entries in source_groups.items():
  faces=[];refs=[];w,h=sources[group]['size'];mask=Image.new('L',(w,h));draw=ImageDraw.Draw(mask)
  for e in entries:
   for fi,inds in enumerate(e['faces']):
    tri=e['pixel'][inds];faces.append(tri);refs.append((e['level'],int(e.get('face_ids',np.arange(len(e['faces'])))[fi])));draw.polygon([tuple(v-.5)for v in tri],fill=255)
  # True UV connectivity: neighboring raster pixels must not merge unrelated islands.
  parent=list(range(len(faces)));seen={}
  def root(i):
   while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
   return i
  for i,tri in enumerate(faces):
   for point in tri:
    key=tuple(np.round(point,3))
    if key in seen:parent[root(i)]=root(seen[key])
    else:seen[key]=i
  # Near and LOD1 cover the same source maps with different triangulations. Union
  # overlapping interiors as well as shared UV vertices; adjacency alone is insufficient.
  owner=np.full((h,w),-1,np.int32)
  for i,tri in enumerate(faces):
   lo=np.maximum(0,np.floor(tri.min(0)).astype(int));hi=np.minimum([w-1,h-1],np.ceil(tri.max(0)).astype(int));xs,ys=np.meshgrid(np.arange(lo[0],hi[0]+1)+.5,np.arange(lo[1],hi[1]+1)+.5);a,b,c0=tri;den=(b[1]-c0[1])*(a[0]-c0[0])+(c0[0]-b[0])*(a[1]-c0[1])
   if abs(den)<1e-12:continue
   w0=((b[1]-c0[1])*(xs-c0[0])+(c0[0]-b[0])*(ys-c0[1]))/den;w1=((c0[1]-a[1])*(xs-c0[0])+(a[0]-c0[0])*(ys-c0[1]))/den;take=(w0>1e-6)&(w1>1e-6)&(w0+w1<1-1e-6);xx=(xs[take]-.5).astype(int);yy=(ys[take]-.5).astype(int)
   for other in np.unique(owner[yy,xx]):
    if other>=0:parent[root(i)]=root(other)
   owner[yy,xx]=i
  groups={}
  for i in range(len(faces)):groups.setdefault(root(i),[]).append(i)
  for ids in groups.values():
   tri=np.array([faces[i]for i in ids]);points=tri.reshape(-1,2);best=None
   for degrees in range(0,180,3):
    a=math.radians(degrees);rot=np.array([[math.cos(a),-math.sin(a)],[math.sin(a),math.cos(a)]]);turned=points@rot.T;lo=np.floor(turned.min(0)-.5).astype(int);hi=np.ceil(turned.max(0)+.5).astype(int);size=hi-lo;score=np.prod(size+PAD*2)
    if best is None or score<best[0]:best=(score,rot,lo,size)
   _,rot,lo,size=best
   c={'id':len(charts),'group':group,'lo':lo,'w':int(size[0])+PAD*2,'h':int(size[1])+PAD*2,'tri':tri@rot.T,'rot':rot,'refs':[refs[i]for i in ids]};charts.append(c)
 print('CHART_STATS',kind,len(charts),'rect_area',sum(c['w']*c['h']for c in charts),'largest',sorted([(c['w']*c['h'],c['w'],c['h'],c['group'])for c in charts],reverse=True)[:12],flush=True)
 if '--stats'in sys.argv:continue
 # Pack dilated chart shapes, allowing another island to occupy a large chart's empty concavity.
 width={'body':4096,'spear':1536,'buckler':1536}[kind]
 if '--reuse-layout'in sys.argv:
  saved=json.loads((OUT/'textures_shared/layout.json').read_text())[kind];width,height=saved['size'];assert len(saved['layout'])==len(charts);positions={}
  for c,oldc in zip(charts,saved['layout']):
   original=c['tri']@c['rot'];c['rot']=np.array(oldc['rotation']);c['tri']=original@c['rot'].T;c['lo']=np.array(oldc['source_origin'])+PAD;c['w'],c['h']=oldc['size'];positions[c['id']]=oldc['atlas_origin']
 else:height,positions=place(charts,width)
 area=width*height
 print('PACKED_SHAPES',kind,width,height,'old pixels',old_pixels,flush=True)
 dest={path:np.zeros((height,width,4),np.uint8)for path in TEXTURE_SLOTS};new_uv={e['level']:e['pixel'].copy()for e in levels};assigned={e['level']:{}for e in levels};lut={e['level']:e for e in levels};layout=[]
 for c in charts:
  x,y=positions[c['id']];cw,ch=c['w'],c['h'];origin=c['lo']-PAD;mask=Image.new('L',(cw,ch));draw=ImageDraw.Draw(mask)
  for tri in c['tri']:draw.polygon([tuple(v-origin-.5)for v in tri],fill=255)
  coverage=np.array(mask)>0
  if not coverage.any():coverage[PAD,PAD]=True
  dist,nearest=distance_transform_edt(~coverage,return_indices=True);yy,xx=nearest;source=(np.stack([xx,yy],-1)+.5+origin)@c['rot'];srcx=source[:,:,0]-.5;srcy=source[:,:,1]-.5
  # Pad each source island before rotation/filtering, so skinny skin triangles cannot
  # sample the black/feather pixels just beyond their original tightly packed UV boundary.
  source_take=np.array([level==(c['group'][0]if isinstance(c['group'],tuple)else c['group'])for level,fi in c['refs']]);original_tri=(c['tri'][source_take]if source_take.any()else c['tri'])@c['rot'];sw,sh=sources[c['group']]['size'];slo=np.maximum(0,np.floor(original_tri.min((0,1))-2).astype(int));shi=np.minimum([sw,sh],np.ceil(original_tri.max((0,1))+2).astype(int));ssize=shi-slo
  exact=np.zeros((ssize[1],ssize[0]),bool)
  for tri in original_tri:
   lo=np.maximum(slo,np.floor(tri.min(0)).astype(int));hi=np.minimum(shi-1,np.ceil(tri.max(0)).astype(int));xs,ys=np.meshgrid(np.arange(lo[0],hi[0]+1)+.5,np.arange(lo[1],hi[1]+1)+.5);a,b,c0=tri;den=(b[1]-c0[1])*(a[0]-c0[0])+(c0[0]-b[0])*(a[1]-c0[1])
   if abs(den)<1e-12:continue
   w0=((b[1]-c0[1])*(xs-c0[0])+(c0[0]-b[0])*(ys-c0[1]))/den;w1=((c0[1]-a[1])*(xs-c0[0])+(a[0]-c0[0])*(ys-c0[1]))/den;take=(w0>=0)&(w1>=0)&(w0+w1<=1);exact[(ys[take]-.5-slo[1]).astype(int),(xs[take]-.5-slo[0]).astype(int)]=True
  if not exact.any():
   centre=np.clip(np.floor(original_tri.mean((0,1))).astype(int)-slo,[0,0],ssize-1);exact[centre[1],centre[0]]=True
  _,source_near=distance_transform_edt(~exact,return_indices=True)
  for path in TEXTURE_SLOTS:
   raw=sources[c['group']]['maps'][path];original=raw[slo[1]:shi[1],slo[0]:shi[0]][tuple(source_near)];pixels=np.stack([map_coordinates(original[:,:,i],[srcy-slo[1],srcx-slo[0]],order=1,mode='nearest')for i in range(4)],-1)
   if path==('normalTexture',):
    normals=pixels[:,:,:2].astype(float)/127.5-1;normal_rotation=c['rot']*np.array([[1,-1],[-1,1]]);normals=normals@normal_rotation.T;pixels[:,:,:2]=np.uint8(np.clip((normals+1)*127.5,0,255)+.5)
   pixels[dist>PAD+1]=[128,128,255,255]if path==('normalTexture',)else[0,0,0,255];target=dest[path][y:y+ch,x:x+cw];target[dist<=PAD+1]=pixels[dist<=PAD+1]
  for level,fi in c['refs']:
   e=lut[level]
   for vi in e['faces'][fi]:
    value=(e['pixel'][vi]@c['rot'].T-origin+np.array([x,y]))/np.array([width,height])
    if int(vi)in assigned[level]:assert np.max(abs(assigned[level][int(vi)]-value))<1e-7
    assigned[level][int(vi)]=value;new_uv[level][vi]=value
  layout.append({'source_group':c['group'],'rotation':c['rot'].tolist(),'source_origin':origin.tolist(),'atlas_origin':[x,y],'size':[cw,ch],'triangle_count':len(c['refs'])})
 folder=OUT/'textures_shared'/kind;folder.mkdir(parents=True,exist_ok=True);names=['basecolor','metal_rough','normal','region_mask']
 for path,name in zip(TEXTURE_SLOTS,names):Image.fromarray(dest[path]).save(folder/f'{name}.png',optimize=True)
 for e in levels:
  doc,buf,pr=e['doc'],e['buf'],e['pr'];idx=pr['attributes']['TEXCOORD_0'];pr['attributes']['TEXCOORD_0']=append_accessor(doc,buf,new_uv[e['level']].astype(np.float32),doc['accessors'][idx],34962)
  textures={};doc['images']=[];doc['textures']=[]
  for path,name in zip(TEXTURE_SLOTS,names):
   packed=(folder/f'{name}.png').read_bytes();buf.extend(b'\0'*(-len(buf)%4));vi=len(doc['bufferViews']);doc['bufferViews'].append({'buffer':0,'byteOffset':len(buf),'byteLength':len(packed)});buf.extend(packed);idx=len(doc['images']);doc['images'].append({'bufferView':vi,'mimeType':'image/png','name':kind+'_'+name});doc['textures'].append({'source':idx,'sampler':0});textures[path]=idx
  for mat in doc['materials']:
   for path in TEXTURE_SLOTS:set_slot(mat,path,{'index':textures[path]})
  doc,buf=compact(doc,buf);assert len(doc['images'])==4;write_glb(e['file'],doc,buf)
 record={'size':[width,height],'old_total_texels_per_map':old_pixels,'shared_texels_per_map':area,'islands':len(charts),'dilated_margin_px':PAD,'texel_scale':1.0,'LOD1_reuses_near_charts':True,'islands_by':'shared UV vertices, never raster adjacency','source_filter_padding':'nearest exact interior texel before rotated bilinear sampling','layout':layout};records[kind]=record
 print('SHARED_ATLAS',kind,width,height,len(charts),'old',old_pixels,'new',area,flush=True)
(OUT/'textures_shared/layout.json').write_text(json.dumps(records,indent=2))

(P/'review/round4_skin_overlap_repair.json').write_text(json.dumps(skin_repairs,indent=2))
