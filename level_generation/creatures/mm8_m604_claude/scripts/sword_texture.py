"""Project the generated sword reference onto a solid blade and cylindrical grip; retain the original artwork."""
from pathlib import Path
import json,numpy as np
from PIL import Image
from scipy import ndimage
p=Path(__file__).resolve().parents[1];T=p/'textures';T.mkdir(exist_ok=True)
im=np.array(Image.open(p/'references_hd/sword_reference.png').convert('RGBA'))
# Alpha supplies geometry, not a translucent glow card. The guard and grip get solid volumes.
m=im[:1200,:,3]>=200
labels,n=ndimage.label(m);areas=np.bincount(labels.ravel());areas[0]=0;m=labels==int(areas.argmax())
# Directed pixel edges form the external silhouette, including the hooked cut-outs.
edges={}
for y,x in np.argwhere(m):
 x,y=int(x),int(y)
 for outside,a,b in [(y==0 or not m[y-1,x],(x,y),(x+1,y)),(x==m.shape[1]-1 or not m[y,x+1],(x+1,y),(x+1,y+1)),
                     (y==m.shape[0]-1 or not m[y+1,x],(x+1,y+1),(x,y+1)),(x==0 or not m[y,x-1],(x,y+1),(x,y))]:
  if outside:edges.setdefault(a,[]).append(b)
loops=[]
while edges:
 start=min(edges,key=lambda q:(q[1],q[0]));q=start;loop=[q]
 while True:
  ns=edges[q];nxt=ns.pop()
  if not ns:del edges[q]
  q=nxt
  if q==start:break
  assert q in edges,'Open alpha contour'
  loop.append(q)
 loops.append(loop)
poly=max(loops,key=len);poly=np.asarray(poly,float)
def simplify(a,eps=2.0):
 if len(a)<=2:return a
 d=a[-1]-a[0];L=np.linalg.norm(d)
 dist=np.linalg.norm(a-a[0],axis=1) if L<1e-9 else np.abs(d[0]*(a[:,1]-a[0,1])-d[1]*(a[:,0]-a[0,0]))/L
 k=int(np.argmax(dist))
 if dist[k]<=eps:return a[[0,-1]]
 return np.concatenate([simplify(a[:k+1],eps)[:-1],simplify(a[k:],eps)])
# Split the closed loop at its farthest point so RDP does not have a zero-length baseline.
k=int(np.argmax(np.linalg.norm(poly-poly[0],axis=1)))
poly=np.concatenate([simplify(poly[:k+1])[:-1],simplify(np.vstack([poly[k:],poly[0]]))[:-1]])
assert 20<len(poly)<200 and poly[:,1].min()<30 and poly[:,1].max()==1200
json.dump({'outline':poly.tolist(),'axis_x':540,'grip_row':1350,'metres_per_pixel':0.00063,'crop':[390,0,690,1536]},open(T/'sword_profile.json','w'),indent=2)
crop=im[:,390:690];opaque=crop[:,:,3]>=128
_,(iy,ix)=ndimage.distance_transform_edt(~opaque,return_indices=True);rgb=crop[:,:,:3][iy,ix]
Image.fromarray(rgb).resize((256,1024),Image.Resampling.LANCZOS).save(T/'m604_sword_basecolor.png')
normal=np.zeros((1024,256,3),np.uint8);normal[:]=[128,128,255];Image.fromarray(normal).save(T/'m604_sword_normal.png')
orm=np.zeros_like(normal);orm[:]=[220,95,0];orm[830:960]=[90,200,0]
Image.fromarray(orm).save(T/'m604_sword_metal_rough.png')
classes=np.full((1024,256),9,np.uint8);classes[830:960]=8;Image.fromarray(classes).save(T/'m604_sword_material_classes.png')
print('SWORD contour',len(poly),'points; projected texture 256x1024')
