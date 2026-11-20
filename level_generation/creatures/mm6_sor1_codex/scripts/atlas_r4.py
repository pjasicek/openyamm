"""Pack coherent garment islands and transfer accepted material samples without crossing source UV seams."""
from pathlib import Path
import json,numpy as np
from PIL import Image
from scipy.spatial import cKDTree
from scipy.ndimage import distance_transform_edt
p=Path(__file__).resolve().parents[1];out=p/'textures/round4';W,H=2080,1024;PAD=18
lo=np.load(p/'work/uv_unpacked_r4.npz');hi=np.load(p/'work/uv_accepted_r4.npz')
v,f,u,part=[lo[k].copy() for k in ['vertices','faces','uv','part']]
parent=list(range(len(f)));edges={}
def root(i):
 while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
 return i
for i,(face,uv) in enumerate(zip(f,u)):
 for k in range(3):
  j=(k+1)%3;a,b=sorted([(int(face[k]),*np.round(uv[k],5)),(int(face[j]),*np.round(uv[j],5))]);key=(tuple(a),tuple(b))
  if key in edges:parent[root(i)]=root(edges[key])
  else:edges[key]=i
charts={}
for i in range(len(f)):charts.setdefault(root(i),[]).append(i)
cutpath=p/'work/uv_cuts_r4.json';cuts=set(json.loads(cutpath.read_text())) if cutpath.exists() else set()
charts={k:[i for i in ids if i not in cuts] for k,ids in charts.items()};charts={k:ids for k,ids in charts.items() if ids}
for i in cuts:
 a,b,c=v[f[i]];ab=b-a;ac=c-a;x=ab/np.linalg.norm(ab);u[i]=[[0,0],[np.linalg.norm(ab),0],[ac@x,np.linalg.norm(np.cross(x,ac))]];charts[-i-1]=[i]
tri=v[f];area=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)/2
du=u[:,1]-u[:,0];dv=u[:,2]-u[:,0];ua=np.abs(du[:,0]*dv[:,1]-du[:,1]*dv[:,0])/2
# Preserve robe density; allocate the remaining atlas area to face, hair and hands.
density={2:1830,5:1400,7:1770,8:1770,3:1100,4:1200,100:390,1:500,103:320,104:320}
items=[]
for ix,ids in enumerate(charts.values()):
 ids=np.array(ids);uv=u[ids];pt=int(part[f[ids[0],0]]);s=density.get(pt,430)*np.sqrt(area[ids].sum()/max(ua[ids].sum(),1e-16));q=uv*s;q-=q.min((0,1));wh=np.ceil(q.max((0,1))).astype(int)+1
 items.append({'id':ix,'ids':ids,'part':pt,'q':q,'wh':wh,'density':density.get(pt,430)})
def pack(scale):
 free=[(0,0,W,H)];places={}
 for item in sorted(items,key=lambda x:-np.prod(x['wh']*scale+2*PAD)):
  choices=[]
  for j,(x,y,w,h) in enumerate(free):
   for rot in [False,True]:
    a,b=np.ceil(item['wh']*scale).astype(int)[::(-1 if rot else 1)]+2*PAD
    if a<=w and b<=h:choices.append((min(w-a,h-b),max(w-a,h-b),y,x,j,int(a),int(b),rot))
  if not choices:return None
  _,_,y,x,j,a,b,rot=min(choices);places[item['id']]=(x,y,a,b,rot);new=[]
  for xx,yy,ww,hh in free:
   if xx>=x+a or xx+ww<=x or yy>=y+b or yy+hh<=y:new.append((xx,yy,ww,hh));continue
   if xx<x:new.append((xx,yy,x-xx,hh))
   if xx+ww>x+a:new.append((x+a,yy,xx+ww-x-a,hh))
   if yy<y:new.append((xx,yy,ww,y-yy))
   if yy+hh>y+b:new.append((xx,y+b,ww,yy+hh-y-b))
  free=[r for k,r in enumerate(new) if not any(k!=j and r[0]>=s[0] and r[1]>=s[1] and r[0]+r[2]<=s[0]+s[2] and r[1]+r[3]<=s[1]+s[3] and (r!=s or k>j) for j,s in enumerate(new))]
 return places
SCALE=.85
places=pack(SCALE)
if places is None:SCALE=.83;places=pack(SCALE)
assert places is not None,'Accepted density plus padding does not fit'
packed=np.empty_like(u);chart_index=np.zeros(len(f),int)
for item in items:
 x,y,a,b,rot=places[item['id']];q=item['q'].copy()*SCALE
 if rot:q=q[...,::-1].copy()
 packed[item['ids']]=(q+[x+PAD,y+PAD])/[W,H];chart_index[item['ids']]=item['id']
np.savez_compressed(p/'work/atlas_uv_r4.npz',uv=packed,faces=f,vertices=v,part=part,chart=chart_index)
# Rasterize in UV pixel coordinates. Pixel ownership is retained for independent margin/mip checks.
owner=np.full((H,W),-1,np.int32);face_image=np.full((H,W),-1,np.int32);bary=np.zeros((H,W,3),np.float32);overlap=0;bad=[]
for i,q in enumerate(packed*[W,H]):
 xmin,ymin=np.maximum(np.floor(q.min(0)).astype(int),0);xmax,ymax=np.minimum(np.ceil(q.max(0)).astype(int),[W-1,H-1]);xx,yy=np.meshgrid(np.arange(xmin,xmax+1)+.5,np.arange(ymin,ymax+1)+.5);points=np.stack([xx,yy],-1);ab=q[1]-q[0];ac=q[2]-q[0];det=ab[0]*ac[1]-ab[1]*ac[0]
 if abs(det)<1e-12:continue
 delta=points-q[0];bb=(delta[...,0]*ac[1]-delta[...,1]*ac[0])/det;cc=(ab[0]*delta[...,1]-ab[1]*delta[...,0])/det;aa=1-bb-cc;inside=(aa>=-1e-7)&(bb>=-1e-7)&(cc>=-1e-7)
 sub=face_image[ymin:ymax+1,xmin:xmax+1];hit=(sub>=0)&inside;overlap+=int(hit.sum());
 if hit.any():bad.append((int(i),int(part[f[i,0]]),int(hit.sum())))
 sub[inside]=i;owner[ymin:ymax+1,xmin:xmax+1][inside]=chart_index[i];bary[ymin:ymax+1,xmin:xmax+1][inside]=np.stack([aa,bb,cc],-1)[inside]
if overlap>=25:
 cutpath.write_text(json.dumps(sorted(cuts|{x[0] for x in bad})));raise AssertionError(('UV overlap pixels; cuts recorded for repair',overlap,len(bad)))
print('OVERLAP',overlap,flush=True)
np.savez_compressed(p/'work/atlas_raster_r4.npz',owner=owner,face=face_image,bary=bary)
report={'width':W,'height':H,'islands':len(items),'padding_px':PAD,'covered_fraction':float((owner>=0).mean()),'overlap_pixels':overlap,'parts':{str(k):{'target_texels_per_metre':val*SCALE} for k,val in density.items()},'rectangles':{str(k):[int(x) for x in value] for k,value in places.items()},'seams':'Robe back seam; other seams follow garment/piece edges and side planes.'}
(p/'review/round4/atlas_layout.json').write_text(json.dumps(report,indent=2));print('PACKED',report['islands'],report['covered_fraction'],'overlaps',overlap,flush=True)
