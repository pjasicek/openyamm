"""Bounded coordinate fitting of the distant silhouette; no topology, UV, weight or animation edits."""
import json,math,time
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import distance_transform_edt
P=Path(__file__).resolve().parents[1];W=P/'work/round2/reduction';R=P/'review/round2/reduction';data=np.load(W/'lod3_raster_input.npz');co=data['co'].copy();original=co.copy();faces=data['faces'];fixed=data['fixed'].copy();soles=co[:,2]<.015;fixed[soles]=False;height=float(data['height']);cameras=data['cameras'];center=data['center'];S=8;X=400;Y=350;CW=200;CH=300;FW=CW*S;FH=CH*S;N=FW*FH;CN=CW*CH
reference=np.concatenate([(np.asarray(Image.open(R/f'lod3_reference_a_{i}.png'))[Y:Y+CH,X:X+CW,3]>=128).ravel()for i in range(8)])
fields=np.array([distance_transform_edt(~v.reshape(CH,CW))-distance_transform_edt(v.reshape(CH,CW))for v in reference.reshape(8,-1)])
projectors=np.array([np.stack([right,-up])*88/height for direction,right,up in cameras]);projected=np.einsum('vij,nj->vni',projectors,co-center)+499.5
_,groups=np.unique(np.round(co,6),axis=0,return_inverse=True);members=[np.flatnonzero(groups==i)for i in range(groups.max()+1)];adjacency=[np.flatnonzero(np.isin(faces,ids).any(1))for ids in members]
cover=np.zeros(8*N,dtype=np.int16);cache={}
def raster(v,triangle):
 xy=projected[v,faces[triangle]];xy=(xy+.5-np.array([X,Y]))*S-.5;lo=np.maximum(np.floor(xy.min(0)).astype(int)-1,0);hi=np.minimum(np.ceil(xy.max(0)).astype(int)+2,[FW,FH]);size=hi-lo
 if np.any(size<=0):return np.empty(0,np.int32)
 image=Image.new('1',tuple(size));ImageDraw.Draw(image).polygon([tuple(q-lo)for q in xy],fill=1);yy,xx=np.where(np.asarray(image));return (v*N+(yy+lo[1])*FW+xx+lo[0]).astype(np.int32)
for view in range(8):
 for triangle in range(len(faces)):
  ids=raster(view,triangle);cache[view,triangle]=ids;cover[ids]+=1
sub=np.array([y*FW+x for y in range(S)for x in range(S)])
def coarse(ids):
 view=ids//CN;q=ids%CN;y=q//CW;x=q%CW;base=view*N+y*S*FW+x*S;return ((cover[base[:,None]+sub]>0).sum(1)>=S*S/2)
def pixels(ids):
 view=ids//N;q=ids%N;return view*CN+(q//FW//S)*CW+(q%FW//S)
mask=coarse(np.arange(8*CN));intersection=int((mask&reference).sum());union=int((mask|reference).sum());history=[{'pass':-1,'iou':intersection/union}];print('RASTER INITIAL',intersection/union,flush=True)
# Exclude interior vertices that cannot influence a silhouette at this scale.
active=[]
for i,ids in enumerate(members):
 if fixed[ids].any():continue
 xy=np.rint(projected[:,ids[0]]-np.array([X,Y])).astype(int);near=any(0<=x<CW and 0<=y<CH and abs(fields[v,y,x])<2.5 for v,(x,y)in enumerate(xy))
 if near:active.append(i)
print('ACTIVE OUTLINE GROUPS',len(active),flush=True);started=time.time()
for sweep,step in enumerate([.006,.003,.003,.0015,.0015,.00075]):
 accepted=0
 for group in active:
  verts=members[group];triangles=adjacency[group];oldpos=co[verts].copy();oldprojected=projected[:,verts].copy();entries=[(view,int(t))for view in range(8)for t in triangles];old=[cache[k]for k in entries];best=None;bestscore=intersection/union
  for axis in range(3):
   if axis==2 and soles[verts].any():continue
   for sign in [-1,1]:
    delta=np.zeros(3);delta[axis]=sign*step;candidate=oldpos+delta
    if np.max(np.linalg.norm(candidate-original[verts],axis=1))>.03:continue
    projected[:,verts]=oldprojected+np.einsum('vij,j->vi',projectors,delta)[:,None,:];new=[raster(*k)for k in entries];affected=np.unique(pixels(np.concatenate(old+new)));before=coarse(affected)
    for ids in old:cover[ids]-=1
    for ids in new:cover[ids]+=1
    after=coarse(affected);truth=reference[affected];ni=intersection+int((after&truth).sum())-int((before&truth).sum());nu=union+int((after|truth).sum())-int((before|truth).sum());score=ni/nu
    if score>bestscore+1e-10:bestscore=score;best=(delta,new,ni,nu)
    for ids in new:cover[ids]-=1
    for ids in old:cover[ids]+=1
  projected[:,verts]=oldprojected
  if best:
   delta,new,intersection,union=best;co[verts]=oldpos+delta;projected[:,verts]=oldprojected+np.einsum('vij,j->vi',projectors,delta)[:,None,:]
   for key,oldids,newids in zip(entries,old,new):cover[oldids]-=1;cover[newids]+=1;cache[key]=newids
   accepted+=1
 assert cover.min()>=0
 mask=coarse(np.arange(8*CN));assert intersection==int((mask&reference).sum())and union==int((mask|reference).sum())
 row={'pass':sweep,'step_m':step,'iou':intersection/union,'accepted_moves':accepted,'seconds':time.time()-started};history.append(row);print('RASTER FIT',row,flush=True);np.save(W/'lod3_raster_output.npy',co);(R/'lod3_raster_fit.json').write_text(json.dumps({'source':'lod3_material02.blend','supersample':S,'max_displacement_m':float(np.linalg.norm(co-original,axis=1).max()),'history':history,'external_blender_validation':'pending'},indent=2))
assert np.array_equal(co[fixed],original[fixed]);assert np.array_equal(co[soles,2],original[soles,2])
