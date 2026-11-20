"""Repack shared all-LOD UV charts by integer texel translation, with 16-pixel dilation."""
import sys,json,math,io,hashlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label,distance_transform_edt
from scipy.signal import fftconvolve
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P.parents[2]/'tools'))
from merge_head_material import read_glb,write_glb,accessor_array,image_of,compact
MARGIN=16
def pack(rects,width,height):
 free=[(0,0,width,height)];placed={}
 for key,w,h in sorted(rects,key=lambda r:(max(r[1:]),r[1]*r[2]),reverse=True):
  choices=[(min(fw-w,fh-h),max(fw-w,fh-h),y,x)for x,y,fw,fh in free if w<=fw and h<=fh]
  if not choices:return None
  _,_,y,x=min(choices);placed[key]=(x,y,w,h);new=[]
  for fx,fy,fw,fh in free:
   if x>=fx+fw or x+w<=fx or y>=fy+fh or y+h<=fy:new.append((fx,fy,fw,fh));continue
   if x>fx:new.append((fx,fy,x-fx,fh))
   if x+w<fx+fw:new.append((x+w,fy,fx+fw-x-w,fh))
   if y>fy:new.append((fx,fy,fw,y-fy))
   if y+h<fy+fh:new.append((fx,y+h,fw,fy+fh-y-h))
  free=[r for i,r in enumerate(new)if not any(i!=j and r[0]>=s[0]and r[1]>=s[1]and r[0]+r[2]<=s[0]+s[2]and r[1]+r[3]<=s[1]+s[3]and(i>j or r!=s)for j,s in enumerate(new))]
 return placed
assert pack([(0,20,20),(1,20,20)],40,20) is not None
records={}
for name in ['mm6_arc1.glb','mm6_arc1_bow.glb','mm6_arc1_arrow.glb']:
 src=P/'work/round5/runtime_unpadded'/name;doc,raw=read_glb(src);binary=bytearray(raw)
 density={'mm6_arc1.glb':.75,'mm6_arc1_bow.glb':.875,'mm6_arc1_arrow.glb':1.}[name]
 original_size=image_of(doc,raw,0)[0].size
 images=[np.array(image_of(doc,raw,i)[0].convert('RGBA').resize(tuple(round(v*density)for v in original_size),Image.Resampling.NEAREST if i==3 else Image.Resampling.LANCZOS))for i in range(len(doc['textures']))]
 assert len({x.shape for x in images})==1
 height,width=images[0].shape[:2];scale=np.array([width,height]);accessors={};faces=[]
 for mesh in doc['meshes']:
  for prim in mesh['primitives']:
   ai=prim['attributes']['TEXCOORD_0']
   if ai not in accessors:accessors[ai]=accessor_array(doc,raw,ai).astype(float)*scale
   ix=accessor_array(doc,raw,prim['indices']).reshape(-1,3);faces.extend(accessors[ai][ix])
 faces=np.array(faces)
 # A chart is connected texture coverage over the entire LOD chain, including overlapping UV charts.
 # Supersampling keeps small islands; all triangle vertices participate in the component union below.
 coverage=Image.new('1',(width*2,height*2));draw=ImageDraw.Draw(coverage)
 for tri in faces:draw.polygon([tuple(x)for x in tri*2],fill=1)
 lab,count=label(np.array(coverage),np.ones((3,3)));_,nearest=distance_transform_edt(lab==0,return_indices=True);filled=lab[tuple(nearest)]
 parent=list(range(count+1))
 def root(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 def ids(points):
  xy=np.floor(points*2).astype(int);xy=np.clip(xy,[0,0],[width*2-1,height*2-1]);return filled[xy[...,1],xy[...,0]]
 for tri in faces:
  ks=ids(np.vstack((tri,tri.mean(0))))
  for k in ks[1:]:parent[root(int(k))]=root(int(ks[0]))
 roots=np.array([root(i)for i in range(count+1)]);lookup=roots[filled];groups={}
 uv_ids={}
 for ai,uv in accessors.items():
  labels=roots[ids(uv)];uv_ids[ai]=labels
  for k in np.unique(labels):groups.setdefault(int(k),[]).append(uv[labels==k])
 bounds={k:(np.floor(np.vstack(v).min(0)).astype(int)-1,np.ceil(np.vstack(v).max(0)).astype(int)+2)for k,v in groups.items()}
 rects=[(k,int(hi[0]-lo[0]+2*MARGIN),int(hi[1]-lo[1]+2*MARGIN))for k,(lo,hi)in bounds.items()]
 # Pack actual dilated chart silhouettes rather than wasting their empty bounding-box corners.
 tri_groups=roots[ids(faces.mean(1))];patch_masks={};coarse={};GRID=4
 for k,(lo,hi)in bounds.items():
  cw,ch=map(int,hi-lo);mi=Image.new('1',(cw+2*MARGIN,ch+2*MARGIN));dr=ImageDraw.Draw(mi)
  for tri in faces[tri_groups==k]:dr.polygon([tuple(p-lo+MARGIN)for p in tri],fill=1)
  mask=distance_transform_edt(~np.array(mi))<=MARGIN
  # Conservative 4-pixel occupancy retains every padded texel.
  hh,ww=mask.shape;pad=np.pad(mask,((0,(-hh)%GRID),(0,(-ww)%GRID)))
  coarse[k]=pad.reshape(pad.shape[0]//GRID,GRID,pad.shape[1]//GRID,GRID).any((1,3))
  patch_masks[k]=mask
 print('DILATED_AREA',name,sum(x.sum()for x in patch_masks.values()),'source',width*height,flush=True)
 def polygon_pack(ww,hh):
  occupied=np.zeros((hh//GRID,ww//GRID),np.float32);result={}
  for k in sorted(coarse,key=lambda k:(coarse[k].sum(),max(coarse[k].shape)),reverse=True):
   mask=coarse[k];h,w=mask.shape
   if h>len(occupied)or w>occupied.shape[1]:return None
   hits=fftconvolve(occupied,mask[::-1,::-1].astype(np.float32),mode='valid')
   options=np.argwhere(hits<.1)
   if not len(options):return None
   y,x=options[0];occupied[y:y+h,x:x+w]+=mask
   assert occupied.max()<=1
   ph,pw=patch_masks[k].shape;result[k]=(int(x*GRID),int(y*GRID),pw,ph)
  return result
 new_width=math.ceil(max(width,max(r[1]for r in rects))/32)*32
 new_height=math.ceil(max(max(r[2]for r in rects),sum(x.sum()for x in coarse.values())*GRID*GRID/new_width)/32)*32
 while (placements:=polygon_pack(new_width,new_height))is None:new_height+=32
 outputs=[np.zeros((new_height,new_width,4),np.uint8)for _ in images];changes={};texel_error=0.
 tri_groups=roots[ids(faces.mean(1))]
 for k,(lo,hi)in bounds.items():
  x,y,w,h=placements[k];cw,ch=map(int,hi-lo);maskim=Image.new('1',(cw,ch));draw=ImageDraw.Draw(maskim)
  for tri in faces[tri_groups==k]:draw.polygon([tuple(p-lo)for p in tri],fill=1)
  mask=np.array(maskim)
  assert mask.any(),(name,k)
  _,nn=distance_transform_edt(~mask,return_indices=True)
  yy,xx=np.indices((ch+2*MARGIN,cw+2*MARGIN));local_y=np.clip(yy-MARGIN,0,ch-1);local_x=np.clip(xx-MARGIN,0,cw-1)
  sy=nn[0,local_y,local_x]+lo[1];sx=nn[1,local_y,local_x]+lo[0]
  sy=np.clip(sy,0,height-1);sx=np.clip(sx,0,width-1)
  # Keep original texels inside the chart; only exterior pixels use edge dilation.
  iy,ix=np.indices((ch,cw));sy[MARGIN:MARGIN+ch,MARGIN:MARGIN+cw][mask]=np.clip(iy+lo[1],0,height-1)[mask];sx[MARGIN:MARGIN+ch,MARGIN:MARGIN+cw][mask]=np.clip(ix+lo[0],0,width-1)[mask]
  for output,source in zip(outputs,images):output[y:y+h,x:x+w][patch_masks[k]]=source[sy,sx][patch_masks[k]]
  changes[k]=np.array([x+MARGIN,y+MARGIN])-lo
 for ai,uv in accessors.items():
  shifted=uv+np.array([changes[int(k)]for k in uv_ids[ai]]);result=(shifted/[new_width,new_height]).astype('<f4')
  texel_error=max(texel_error,float(abs(result*[new_width,new_height]-shifted).max()))
  a=doc['accessors'][ai];bv=doc['bufferViews'][a['bufferView']];stride=bv.get('byteStride',8);offset=bv.get('byteOffset',0)+a.get('byteOffset',0)
  for i,row in enumerate(result):binary[offset+i*stride:offset+i*stride+8]=row.tobytes()
  a.pop('min',None);a.pop('max',None)
 assert texel_error<.001
 # All variants and LODs retain their existing texture references. Replace each shared image once.
 written=set()
 for ti,output in enumerate(outputs):
  imidx=doc['textures'][ti]['source']
  if imidx in written:continue
  written.add(imidx);buf=io.BytesIO();Image.fromarray(output).save(buf,format='PNG',optimize=True);data=buf.getvalue();binary.extend(b'\0'*(-len(binary)%4));offset=len(binary);binary.extend(data)
  doc['images'][imidx]['bufferView']=len(doc['bufferViews']);doc['bufferViews'].append({'buffer':0,'byteOffset':offset,'byteLength':len(data)})
 doc,binary=compact(doc,binary);dest=P/'export'/name;write_glb(dest,doc,binary)
 assert len(doc['images'])==len(written)
 records[name]={'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'images_before':len(written),'images_after':len(doc['images']),'dimensions_before':list(original_size),'dimensions_after':[new_width,new_height],'bytes_before':src.stat().st_size,'bytes_after':dest.stat().st_size,'charts':len(groups),'dilated_margin_px':MARGIN,'min_uv_to_patch_border_px':MARGIN+1,'texel_density_scale':density,'max_texel_translation_rounding_error_px':texel_error,'shared_by_all_lods':True,'maps':len(outputs)}
 (P/'work/round5'/f'{name}.uv_translation.json').write_text(json.dumps({'old_size':[width,height],'new_size':[new_width,new_height],'charts':{str(k):{'old_min':lo.tolist(),'old_max':hi.tolist(),'rect':placements[k],'translation':changes[k].tolist()}for k,(lo,hi)in bounds.items()}}))
 print('PADDED',name,records[name],flush=True)
(P/'review/round5/texture_sets.json').write_text(json.dumps({'method':'Polygon occupancy packing, conservative four-pixel grid. Integer-pixel chart translation; Body 0.75x, bow 0.875x linear resolution to prioritize the explicit R5 memory cap; arrow unchanged. No island rotation. Connected coverage charts include all LODs. 16-pixel nearest-edge dilation on every map. One set per runtime asset, shared across its entire LOD chain.','assets':records},indent=2))
