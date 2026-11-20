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
J.update({'Pelvis':J0[0].tolist(),'Spine':[0,-.07,1.48],'Spine1':[0,-.02,1.59],'Spine2':[0,.015,1.70],'Neck':[0,.01,1.85],'Head':[0,-.04,2.015]})
for sd,s in [('L',1),('R',-1)]:J.update({sd+'_Clavicle':[s*.07,.015,1.72],sd+'_UpperArm':J[sd+'_UpperArm']})
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
 swing=frame(fo,to)@frame(fs,ts).T;bones['B_'+sd+'_Hand']['rot']=swing@np.array(SRC['B_'+sd+'_Hand']['rot']);palm=normalize(np.cross(fo,to));palm*=1 if palm[0]* (1 if sd=='L' else -1)<0 else -1
 for f,points in pts.items():
  names=[f'B_{sd}_Finger{f}'+suffix for suffix in ['', '1','2']];chains[sd,f]=(names,points)
  for i,n in enumerate(names):
   y=normalize(points[i+1]-points[i]);x=normalize(np.cross(y,palm));z=np.cross(x,y);add(n,points[i],points[i+1],f'B_{sd}_Hand' if i==0 else names[i-1],np.column_stack([x,y,z]))
  FJ[sd+str(f)]=points.tolist()

# A distal forearm control spreads the hand's twist across the measured forearm.
for sd in ['L','R']:
 fn='B_'+sd+'_Forearm';hn='B_'+sd+'_Hand';tn='B_'+sd+'_ForearmTwist';h=(bones[fn]['head']+bones[hn]['head'])/2
 add(tn,h,bones[hn]['head'],fn,bones[fn]['rot']);bones[hn]['parent']=tn
# Parent-before-child order is also the animation evaluation order.
ordered={}
while len(ordered)<len(bones):
 for n,b in bones.items():
  if n not in ordered and (b['parent'] is None or b['parent'] in ordered):ordered[n]=b
bones=ordered
add('Polearm',[0,0,0],[0,0,.12],'Root')
arm=bpy.data.armatures.new('SalamanderSkeleton');rig=bpy.data.objects.new('Rig',arm);bpy.context.collection.objects.link(rig);bpy.context.view_layer.objects.active=rig;rig.select_set(True);body.select_set(False);bpy.ops.object.mode_set(mode='EDIT')
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
ids=np.where((pa==1)&(co[:,2]<J0[0,2]))[0];chainweights(ids,[f'Serpent_{i:02d}' for i in range(len(J0)-1)],J0)
sp=['B_'+n for n in ['Pelvis','Spine','Spine1','Spine2','Neck','Head']];spz=np.array([bones[n]['head'][2] for n in sp]);ids=np.where((pa==1)&(co[:,2]>=J0[0,2]))[0]
for k,n in enumerate(sp):W[ids,ni[n]]=np.interp(co[ids,2],spz,np.eye(len(sp))[k])
labels=np.zeros(NV,dtype=int)
for sd,sgn in [('L',1),('R',-1)]:
 ns=['B_'+sd+'_'+x for x in ['UpperArm','Forearm','ForearmTwist','Hand']]
 pts=np.array([bones[n]['head'] for n in ns]+[np.array(J[sd+'_Hand'])+[sgn*.05,-.03,-.12]])
 width=.22+.20*np.clip(1.65-co[:,2],0,.5)
 ids=np.where((pa==1)&(co[:,0]*sgn>width)&(co[:,2]<1.84))[0]
 prior=W[ids].copy();W[ids]=0;chainweights(ids,ns,pts)
 fade=np.clip((co[ids,0]*sgn-width[ids])/.11,0,1);W[ids]=fade[:,None]*W[ids]+(1-fade[:,None])*prior
 wr=np.array(J[sd+'_Hand']);axis=normalize(wr-np.array(J[sd+'_Forearm']));hids=np.where((pa==1)&(co[:,0]*sgn>.5)&((co-wr)@axis>0))[0]
 W[hids]=0;assign(hids,'B_'+sd+'_Hand')
 # Connectivity identifies free digits; extend only along each digit's own proximal axis.
 owner={int(v):f for f,name in enumerate(['thumb','index','middle','ring','pinky']) for v in FIT[sd]['verts'][name]}
 for _ in range(30):
  new={}
  for v,f in owner.items():
   nsf,fp=chains[sd,f];d=fp[1]-fp[0]
   for w in adj[v]:
    if w in owner or w in new or pa[w]!=1:continue
    if (co[w]-fp[0])@d/(d@d)>.05 and closest(co[w:w+1],fp)[1][0]<.032:new[w]=f
  if not new:break
  owner.update(new)
 for f in range(5):
  ii=np.array([v for v,k in owner.items() if k==f]);nsf,fp=chains[sd,f];W[ii]=0;chainweights(ii,nsf,fp,'B_'+sd+'_Hand');labels[ii]=f+1
 # Claws are rigid and follow their matching distal finger, never nearby palm weights.
 for part in np.unique(pa[(co[:,0]*sgn>.5)&(pa!=1)]):
  ii=np.where(pa==part)[0];f=min(range(5),key=lambda k:np.linalg.norm(co[ii].mean(0)-chains[sd,k][1][-1]));assign(ii,chains[sd,f][0][-1]);labels[ii]=f+1
 depth=(co[hids]-wr)@axis;t=np.clip((.055-depth)/.09,0,.65);W[hids]*=(1-t[:,None]);W[hids,ni['B_'+sd+'_ForearmTwist']]+=t
# Crest and rib shells follow the neck base and skull without moving individual ribs independently.
ids=np.where((pa!=1)&(np.abs(co[:,0])<.3))[0]
for k,n in enumerate(sp):W[ids,ni[n]]=np.interp(co[ids,2],spz,np.eye(len(sp))[k])
for _ in range(3):
 nxt=W.copy()
 for i,nb in enumerate(adj):
  if nb and pa[i]==1:nxt[i]=.7*W[i]+.3*W[nb].mean(0)
 W=nxt
assert np.all(W.sum(1)>.99),np.where(W.sum(1)<.99)
keep=np.argpartition(W,-4,axis=1)[:,-4:];mask=np.zeros_like(W,dtype=bool);np.put_along_axis(mask,keep,True,axis=1);W[~mask]=0;W/=W.sum(1)[:,None]
for n in names:
 g=body.vertex_groups.new(name=n)
 for i in np.where(W[:,ni[n]]>1e-7)[0]:g.add([int(i)],float(W[i,ni[n]]),'REPLACE')
lab=me.attributes.new('finger','INT','POINT');lab.data.foreach_set('value',labels)
mod=body.modifiers.new('SalamanderSkin','ARMATURE');mod.object=rig;body.parent=rig;rig.show_in_front=True
assert len(bones)<=128,len(bones)
for pb in rig.pose.bones:pb.rotation_mode='QUATERNION'
jsondata={'tail':T,'fingers':FJ,'joints':J,'bone_count':len(bones),'bones':{n:{k:(v.tolist() if isinstance(v,np.ndarray) else v) for k,v in b.items()} for n,b in bones.items()}}
(P/'work/rig.json').write_text(json.dumps(jsondata,indent=2)+'\n');np.savez(P/'work/rig_weights.npz',weights=W,co=co,parts=pa,edges=edges,names=np.array(names));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_v1.blend'));print('RIG',len(bones),'bones',NV,'vertices; all weights normalized')
