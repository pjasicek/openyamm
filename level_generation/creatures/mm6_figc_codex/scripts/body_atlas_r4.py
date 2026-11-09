"""Repack accepted atlas texels without scaling and share them across the fixed body LODs."""
import sys,json,copy
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import distance_transform_edt
P=Path(__file__).resolve().parents[1];R=P/'review/round4'
sys.path.insert(0,str(P.parents[2]/'tools'))
from merge_head_material import read_glb,accessor_array,append_accessor,write_glb,compact,add_image,image_of,TEXTURE_SLOTS,slot

def charts(pos,uv,faces):
 parent=list(range(len(faces)));edges={}
 def root(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 keys=[tuple(np.round(np.r_[p,u],6)) for p,u in zip(pos,uv)]
 for f,ids in enumerate(faces):
  for a,b in zip(ids,np.roll(ids,-1)):
   key=tuple(sorted((keys[a],keys[b])))
   if key in edges:parent[root(f)]=root(edges[key])
   else:edges[key]=f
 groups={}
 for f in range(len(faces)):groups.setdefault(root(f),[]).append(f)
 return list(groups.values())

def prepare():
 d,b=read_glb(R/'before/mm6_figc.glb');p=d['meshes'][0]['primitives'][0]
 pos=accessor_array(d,b,p['attributes']['POSITION']);uv=accessor_array(d,b,p['attributes']['TEXCOORD_0']);faces=accessor_array(d,b,p['indices']).reshape(-1,3)
 groups=charts(pos,uv,faces);boxes=[]
 for g in groups:
  coords=uv[faces[g]].reshape(-1,2)*[3104,2048];lo=np.floor(coords.min(0)).astype(int);hi=np.ceil(coords.max(0)).astype(int)+1
  boxes.append((lo,hi))
 print('ATLAS',len(groups),'rectangle area',sum(np.prod(hi-lo+32) for lo,hi in boxes),'largest',sorted([tuple(hi-lo+32) for lo,hi in boxes],key=lambda a:a[0]*a[1],reverse=True)[:12],flush=True)
 np.savez(R/'body_charts.npz',pos=pos,uv=uv,faces=faces,chart=np.array([next(i for i,g in enumerate(groups) if f in g) for f in range(len(faces))]),lo=np.array([x[0] for x in boxes]),hi=np.array([x[1] for x in boxes]))
def pack():
 from scipy.signal import fftconvolve
 from scipy.ndimage import maximum_filter
 a=np.load(R/'body_charts.npz');uv=a['uv'];faces=a['faces'];labels=a['chart'];lo=a['lo'];hi=a['hi'];masks=[];shapes=[];grid=4;padding=20
 for i,(start,end) in enumerate(zip(lo,hi)):
  size=end-start+2*padding;size=((size+grid-1)//grid)*grid
  im=Image.new('L',tuple(size));draw=ImageDraw.Draw(im)
  for tri in faces[labels==i]:draw.polygon([tuple(v) for v in uv[tri]*[3104,2048]-start+padding],fill=255)
  mask=np.array(im)>0;masks.append(mask)
  # A full 16-texel border, plus the raster guard, survives the occupancy-grid rounding.
  dense=distance_transform_edt(~mask)<=18
  shapes.append(dense.reshape(size[1]//grid,grid,size[0]//grid,grid).max((1,3)))
 width=2304;occupied=np.zeros((1024,width//grid),np.float32);offsets=np.zeros((len(shapes),2),int)
 for i in sorted(range(len(shapes)),key=lambda i:int(shapes[i].sum()),reverse=True):
  sh=shapes[i];cost=fftconvolve(occupied,sh[::-1,::-1].astype(np.float32),mode='valid');spots=np.argwhere(cost<.2)
  assert len(spots),'Atlas exceeded the fixed 4096-pixel staging height'
  y,x=spots[0];occupied[y:y+sh.shape[0],x:x+sh.shape[1]]+=sh;assert occupied.max()<1.5
  offsets[i]=[int(x*grid),int(y*grid)]
 height=int(np.ceil(max(offsets[i,1]+masks[i].shape[0] for i in range(len(masks)))/16)*16)
 width=int(np.ceil(max(offsets[i,0]+masks[i].shape[1] for i in range(len(masks)))/16)*16)
 d,b=read_glb(R/'before/mm6_figc.glb');mat=d['materials'][0];T=P/'textures/round4_body';T.mkdir(exist_ok=True)
 kinds=['basecolor','metal_rough','normal','region_mask'];images={k:np.array(image_of(d,b,slot(mat,path)['index'])[0].convert('RGB')) for k,path in zip(kinds,TEXTURE_SLOTS)}
 canvases={k:np.zeros((height,width,3),np.uint8) for k in kinds};canvases['normal'][:]=[128,128,255]
 used=0
 for i,mask in enumerate(masks):
  yy,xx=distance_transform_edt(~mask,return_distances=False,return_indices=True);dist=distance_transform_edt(~mask);dilated=dist<=16;used+=int(mask.sum());x,y=offsets[i];h,w=mask.shape
  sx=np.clip(xx+lo[i,0]-padding,0,3103);sy=np.clip(yy+lo[i,1]-padding,0,2047)
  for kind,source in images.items():
   tile=canvases[kind][y:y+h,x:x+w];tile[dilated]=source[sy[dilated],sx[dilated]]
 for kind,canvas in canvases.items():Image.fromarray(canvas).save(T/f'{kind}.png',optimize=True)
 mapped=uv[faces]*[3104,2048]+(offsets[labels]-lo[labels]+padding)[:,None,:]
 assert mapped.min()>=16 and (mapped/np.array([width,height])).max()<1
 np.savez(R/'body_packed.npz',**{k:a[k] for k in a.files},packed_uv=mapped/[width,height],offsets=offsets,padding=padding,size=[width,height])
 report={'old_size':[3104,2048],'size':[width,height],'chart_count':len(shapes),'texel_scale':1.0,'minimum_dilation_pixels':16,'surface_pixels':used,'surface_coverage':used/(width*height),'method':'pixel-preserving shape packing, no rotation or resampling'}
 (R/'body_atlas.json').write_text(json.dumps(report,indent=2));print('PACKED_BODY',report,flush=True)
if __name__=='__main__':
 prepare();pack()

