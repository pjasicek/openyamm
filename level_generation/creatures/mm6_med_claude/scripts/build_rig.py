"""Measured hybrid Medusa rig: source-frame arms, connected fingers and two serpent branches."""
import bpy,json,math,heapq
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/fitted_body.blend'))
body=bpy.data.objects['Body'];me=body.data
co=np.array([v.co[:] for v in me.vertices]);pa=np.array([v.value for v in me.attributes['part'].data]);edges=np.array([e.vertices[:] for e in me.edges]);NV=len(co)
T=json.loads((P/'work/tail_rest.json').read_text());J0=np.array(T['joints']);K=T['root_index'];FIT=json.loads((P/'work/fingers_fit.json').read_text());J=json.loads((P/'work/joints_final.json').read_text())['joints'];SRC=json.loads((P.parent/'mm6_fgt_claude/work/source_rest.json').read_text())
adj=[[] for _ in co]
for a,b in edges:adj[a].append(int(b));adj[b].append(int(a))
def normalize(a):return a/max(np.linalg.norm(a),1e-10)
def resample(p,fr):
 a=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))];return np.column_stack([np.interp(np.array(fr)*a[-1],a,p[:,i]) for i in range(3)])
def closest(p,points):
 arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(points,axis=0),axis=1))];best=np.full(len(p),1e9);s=np.zeros(len(p))
 for i,(a,b) in enumerate(zip(points[:-1],points[1:])):
  d=b-a;t=np.clip((p-a)@d/(d@d),0,1);dist=np.linalg.norm(p-a-t[:,None]*d,axis=1);m=dist<best;best[m]=dist[m];s[m]=arc[i]+t[m]*(arc[i+1]-arc[i])
 return s,best,arc
bones={}
def add(n,h,t,parent=None,rot=None):
 h=np.array(h);t=np.array(t)
 if rot is None:
  y=normalize(t-h);x=normalize(np.cross(y,[0,0,1])) if abs(y[2])<.95 else np.array([1.,0,0]);z=np.cross(x,y);rot=np.column_stack([x,y,z])
 bones[n]={'head':h,'tail':t,'parent':parent,'rot':np.array(rot)}
add('Root',J0[K],J0[K]+[0,0,.08])
for i in list(range(K-1,-1,-1))+list(range(K,len(J0)-1)):
 h,t=(J0[i+1],J0[i]) if i<K else (J0[i],J0[i+1]);parent='Root' if i in (K-1,K) else f'Serpent_{i+1:02d}' if i<K else f'Serpent_{i-1:02d}';add(f'Serpent_{i:02d}',h,t,parent)
J.update({'Pelvis':J0[0].tolist(),'Spine':[0,-.026,1.41],'Spine1':[0,-.018,1.50],'Spine2':[0,.003,1.61],'Neck':[0,.002,1.765],'Head':[0,-.018,1.867]})
for sd,s in [('L',1),('R',-1)]:J.update({sd+'_Clavicle':[s*.047,.015,1.686],sd+'_UpperArm':[s*.169,.024,1.683]})
order=['Pelvis','Spine','Spine1','Spine2','Neck','Head']+[sd+'_'+x for sd in ['L','R'] for x in ['Clavicle','UpperArm','Forearm','Hand']]
for short in order:
 n='B_'+short;src=SRC[n];h=np.array(J[short]);child=src['child'];parent=src['parent'] if short!='Pelvis' else 'Serpent_00';r=Matrix(src['rot']);seg=Vector(src['seg'] or [0,0,.1]);c=child[2:] if child else ''
 if c in J and short!='Pelvis':r=seg.rotation_difference(Vector(J[c])-Vector(h)).to_matrix()@r
 add(n,h,np.array(J[c]) if c in J else h+[0,0,.09],parent,r)
FJ={};chains={}
for sd in ['L','R']:
 pts={f:resample(np.array(FIT[sd][name]),[0,.46,.77,1]) for f,name in enumerate(['thumb','index','middle','ring','pinky'])};wr=np.array(J[sd+'_Hand'])
 def frame(f,t):
  f=normalize(f);t=normalize(t-f*np.dot(t,f));return np.column_stack([f,t,np.cross(f,t)])
 sourcehand=np.array(SRC['B_'+sd+'_Hand']['head']);fs=np.array(SRC['B_'+sd+'_Finger2']['head'])-sourcehand;ts=np.array(SRC['B_'+sd+'_Finger1']['head'])-np.array(SRC['B_'+sd+'_Finger4']['head']);fo=pts[2][0]-wr;to=pts[1][0]-pts[4][0]
 swing=frame(fo,to)@frame(fs,ts).T;bones['B_'+sd+'_Hand']['rot']=swing@np.array(SRC['B_'+sd+'_Hand']['rot']);palm=normalize(np.cross(fo,to));palm*=1 if palm[1]<0 else -1
 for f,points in pts.items():
  names=[f'B_{sd}_Finger{f}'+suffix for suffix in ['', '1','2']];chains[sd,f]=(names,points)
  for i,n in enumerate(names):
   y=normalize(points[i+1]-points[i]);x=normalize(np.cross(y,palm));z=np.cross(x,y);add(n,points[i],points[i+1],f'B_{sd}_Hand' if i==0 else names[i-1],np.column_stack([x,y,z]))
  FJ[sd+str(f)]=points.tolist()
# Each snake head belongs to its nearest connected neck; a forked mesh is partitioned by geodesic distance.
neck=[102,103,105,107,109,111,112,115,116,117];heads=[108,113,118,120,122,124,125,126,128];tongues=[100,110,114,119,127,129,130,131,132]
def nearest_part(part,choices):return min(choices,key=lambda n:np.min(np.linalg.norm(co[pa==part,None]-co[pa==n],axis=2)))
hn={h:nearest_part(h,neck) for h in heads};th={t:nearest_part(t,heads) for t in tongues}
def distance(ids,seeds):
 allowed=set(map(int,ids));out={int(i):0. for i in seeds};q=[(0.,int(i)) for i in seeds];heapq.heapify(q)
 while q:
  d,v=heapq.heappop(q)
  if d>out[v]+1e-9:continue
  for w in adj[v]:
   if w not in allowed:continue
   nd=d+float(np.linalg.norm(co[w]-co[v]))
   if nd<out.get(w,1e9):out[w]=nd;heapq.heappush(q,(nd,w))
 return np.array([out.get(int(i),1e9) for i in ids])
snakes=[]
for n in neck:
 ids=np.where(pa==n)[0];hs=[h for h in heads if hn[h]==n];hs=hs or [None];scores=[];seeds=[]
 for h in hs:
  target=co[pa==h].mean(0) if h else co[ids[np.argmax(np.linalg.norm(co[ids]-[0,0,2.08],axis=1))]]
  dd=np.linalg.norm(co[ids]-target,axis=1);seed=ids[np.argsort(dd)[:10]];seeds.append(seed);scores.append(distance(ids,seed))
 owner=np.argmin(scores,axis=0)
 for k,h in enumerate(hs):
  chosen=ids[owner==k];points=co[chosen];root=points[np.argmin(np.linalg.norm(points-[0,.005,2.075],axis=1))];d=distance(chosen,chosen[np.argsort(np.linalg.norm(points-root,axis=1))[:10]]);length=np.percentile(d[d<1e8],99);poly=[]
  for s in np.linspace(0,1,13):
   mask=np.abs(d-s*length)<max(.018,length/12);poly.append(points[mask].mean(0) if mask.any() else poly[-1])
  poly=np.array(poly)
  for _ in range(3):poly[1:-1]=.25*poly[:-2]+.5*poly[1:-1]+.25*poly[2:]
  if h:poly[-1]=co[pa==h].mean(0)
  points=resample(poly,[0,.33,.67,1]);idx=len(snakes);names=[f'Crown_{idx:02d}_{i}' for i in range(3)]
  for i,name in enumerate(names):add(name,points[i],points[i+1],'B_Head' if i==0 else names[i-1])
  snakes.append({'neck':n,'head':h,'tongues':[t for t in tongues if th[t]==h] if h else [],'ids':chosen.tolist(),'joints':points.tolist(),'names':names})
arm=bpy.data.armatures.new('MedusaSkeleton');rig=bpy.data.objects.new('Rig',arm);bpy.context.collection.objects.link(rig);bpy.context.view_layer.objects.active=rig;rig.select_set(True);body.select_set(False);bpy.ops.object.mode_set(mode='EDIT')
for n,b in bones.items():
 e=arm.edit_bones.new(n);e.head=b['head'];e.tail=b['head']+b['rot'][:,1]*max(.015,np.linalg.norm(b['tail']-b['head']));e.align_roll(Vector(b['rot'][:,2]));e.use_deform=n!='Root'
 if b['parent']:e.parent=arm.edit_bones[b['parent']]
bpy.ops.object.mode_set(mode='OBJECT');names=list(bones);ni={n:i for i,n in enumerate(names)};W=np.zeros((NV,len(names)))
def assign(ids,n,w=1.):W[ids,ni[n]]=w
def chainweights(ids,ns,points,root=None):
 ids=np.asarray(ids,dtype=int)
 if not len(ids):return
 s,_,a=closest(co[ids],points);mids=(a[:-1]+a[1:])/2;stations=np.r_[0,mids] if root else mids;nodes=([root]+ns) if root else ns
 for k,n in enumerate(nodes):W[ids,ni[n]]=np.interp(s,stations,np.eye(len(nodes))[k])
bodyids=np.where((pa==0)&(co[:,2]<1.325))[0];chainweights(bodyids,[f'Serpent_{i:02d}' for i in range(29)],J0)
sp=['B_'+n for n in ['Pelvis','Spine','Spine1','Spine2','Neck','Head']];spz=np.array([bones[n]['head'][2] for n in sp]);ids=np.where((pa==0)&(co[:,2]>=1.325))[0]
for k,n in enumerate(sp):W[ids,ni[n]]=np.interp(co[ids,2],spz,np.eye(len(sp))[k])
for sd,part,hpart in [('L',9,1),('R',6,4)]:
 ns=['B_'+sd+'_'+x for x in ['UpperArm','Forearm','Hand']];points=np.array([J[sd+'_'+x] for x in ['UpperArm','Forearm','Hand']]+[np.array(J[sd+'_Hand'])+[0,0,-.09]])
 ids=np.where(pa==part)[0];chainweights(ids,ns,points)
 # Caps share the clavicle at the shoulder and meet the palm with the same wrist weights.
 t=np.clip((co[ids,2]-1.66)/.07,0,1)*.8;W[ids]*=(1-t[:,None]);W[ids,ni['B_'+sd+'_Clavicle']]+=t
 ids=np.where(pa==hpart)[0];assign(ids,'B_'+sd+'_Hand')
 owner={int(v):f for f,name in enumerate(['thumb','index','middle','ring','pinky']) for v in FIT[sd]['verts'][name]}
 for _ in range(25):
  new={}
  for v,f in owner.items():
   ns,pts=chains[sd,f];d=pts[1]-pts[0]
   for w in adj[v]:
    if w in owner or w in new or pa[w]!=hpart:continue
    if (co[w]-pts[0])@d/(d@d)>.05 and closest(co[w:w+1],pts)[1][0]<.026:new[w]=f
  if not new:break
  owner.update(new)
 for f in range(5):
  ii=np.array([v for v,k in owner.items() if k==f]);ns,pts=chains[sd,f];W[ii]=0;chainweights(ii,ns,pts,'B_'+sd+'_Hand')
 # Match across separate wrist shells; fingers remain unaffected.
 wr=np.array(J[sd+'_Hand']);axis=normalize(wr-np.array(J[sd+'_Forearm']));depth=(co[ids]-wr)@axis;t=np.clip((.022-depth)/.075,0,.35);W[ids]*=(1-t[:,None]);W[ids,ni['B_'+sd+'_Forearm']]+=t
for part in [101,104,106,121,123]:
 ids=np.where(pa==part)[0];t=np.clip((co[ids,2]-1.805)/.08,0,1);assign(ids,'B_Neck',1-t);assign(ids,'B_Head',t)
for sn in snakes:
 chainweights(sn['ids'],sn['names'],np.array(sn['joints']),'B_Head')
 for part in ([sn['head']] if sn['head'] else [])+sn['tongues']:assign(np.where(pa==part)[0],sn['names'][-1])
# Two surface-neighbour passes soften the narrow transitions; disconnected shells never share weights.
for _ in range(4):
 nxt=W.copy()
 for i,nb in enumerate(adj):
  if nb and pa[i] in [0,1,4,6,9,106]+neck:nxt[i]=.65*W[i]+.35*W[nb].mean(0)
 W=nxt
assert np.all(W.sum(1)>.99),np.where(W.sum(1)<.99)
# The portable skin contract is four normalized influences.
keep=np.argpartition(W,-4,axis=1)[:,-4:];mask=np.zeros_like(W,dtype=bool);np.put_along_axis(mask,keep,True,axis=1);W[~mask]=0;W/=W.sum(1)[:,None]
for n in names:
 g=body.vertex_groups.new(name=n)
 for i in np.where(W[:,ni[n]]>1e-7)[0]:g.add([int(i)],float(W[i,ni[n]]),'REPLACE')
mod=body.modifiers.new('MedusaSkin','ARMATURE');mod.object=rig;body.parent=rig;rig.show_in_front=True
assert len(bones)<=128,len(bones)
for pb in rig.pose.bones:pb.rotation_mode='QUATERNION'
jsondata={'tail':T,'fingers':FJ,'snakes':snakes,'joints':J,'bone_count':len(bones),'bones':{n:{k:(v.tolist() if isinstance(v,np.ndarray) else v) for k,v in b.items()} for n,b in bones.items()}}
(P/'work/rig.json').write_text(json.dumps(jsondata,indent=2)+'\n');np.savez(P/'work/rig_weights.npz',weights=W,co=co,parts=pa,edges=edges,names=np.array(names));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_v1.blend'));print('RIG',len(bones),'bones',len(snakes),'snake chains',NV,'vertices; all weights normalized')
