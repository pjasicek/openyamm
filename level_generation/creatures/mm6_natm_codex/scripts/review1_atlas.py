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
  pixel=uv*np.array([w,h]);entry={'level':level,'file':file,'doc':doc,'buf':buf,'pr':pr,'pixel':pixel,'faces':faces,'group':group};levels.append(entry);source_groups.setdefault(group,[]).append(entry)
 for group,entries in source_groups.items():
  faces=[];refs=[];w,h=sources[group]['size'];mask=Image.new('L',(w,h));draw=ImageDraw.Draw(mask)
  for e in entries:
   for fi,inds in enumerate(e['faces']):
    tri=e['pixel'][inds];faces.append(tri);refs.append((e['level'],fi));draw.polygon([tuple(v-.5)for v in tri],fill=255)
  labels,count=label(np.array(mask)>0,np.ones((3,3)))
  groups={}
  for i,tri in enumerate(faces):
   x,y=np.clip(np.floor(tri.mean(0)-.5).astype(int),[0,0],[w-1,h-1]);key=int(labels[y,x])
   if key==0:
    # Pixel coverage is conservative at degenerate UV caps and texture borders.
    ids=np.unique(labels[max(0,y-1):y+2,max(0,x-1):x+2]);ids=ids[ids>0];assert len(ids)>0;key=int(ids[0])
   groups.setdefault(key,[]).append(i)
  # Conservative pixel labels may separate a subpixel tip. Shared UV vertices remain one chart.
  parent={key:key for key in groups};seen={}
  def root(key):
   while parent[key]!=key:parent[key]=parent[parent[key]];key=parent[key]
   return key
  for key,ids in groups.items():
   for i in ids:
    for point in faces[i]:
     uvkey=tuple(np.round(point,4))
     if uvkey in seen:parent[root(key)]=root(seen[uvkey])
     else:seen[uvkey]=key
  merged={}
  for key,ids in groups.items():merged.setdefault(root(key),[]).extend(ids)
  groups=merged
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
 width={'body':2048,'spear':1536,'buckler':1536}[kind];height,positions=place(charts,width);area=width*height
 print('PACKED_SHAPES',kind,width,height,'old pixels',old_pixels,flush=True)
 dest={path:np.zeros((height,width,4),np.uint8)for path in TEXTURE_SLOTS};new_uv={e['level']:e['pixel'].copy()for e in levels};assigned={e['level']:{}for e in levels};lut={e['level']:e for e in levels};layout=[]
 for c in charts:
  x,y=positions[c['id']];cw,ch=c['w'],c['h'];origin=c['lo']-PAD;mask=Image.new('L',(cw,ch));draw=ImageDraw.Draw(mask)
  for tri in c['tri']:draw.polygon([tuple(v-origin-.5)for v in tri],fill=255)
  coverage=np.array(mask)>0
  if not coverage.any():coverage[PAD,PAD]=True
  dist,nearest=distance_transform_edt(~coverage,return_indices=True);yy,xx=nearest;source=(np.stack([xx,yy],-1)+.5+origin)@c['rot'];srcx=source[:,:,0]-.5;srcy=source[:,:,1]-.5
  for path in TEXTURE_SLOTS:
   original=sources[c['group']]['maps'][path];pixels=np.stack([map_coordinates(original[:,:,i],[srcy,srcx],order=1,mode='nearest')for i in range(4)],-1)
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
 record={'size':[width,height],'old_total_texels_per_map':old_pixels,'shared_texels_per_map':area,'islands':len(charts),'dilated_margin_px':PAD,'texel_scale':1.0,'LOD1_reuses_near_charts':True,'layout':layout};records[kind]=record
 print('SHARED_ATLAS',kind,width,height,len(charts),'old',old_pixels,'new',area,flush=True)
(OUT/'textures_shared/layout.json').write_text(json.dumps(records,indent=2))
