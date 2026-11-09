"""Measured six-limb Harpy rig; anatomical skin weights, connectivity-owned digits, span-weighted wings."""
import bpy,bmesh,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,kdtree
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/anatomy_symmetric.blend'));body=bpy.data.objects['Body'];me=body.data
co=np.array([v.co[:] for v in me.vertices]);pa=np.array([v.value for v in me.attributes['part'].data]);wing=np.load(P/'work/wing_mask.npy');NV=len(co);assert len(wing)==NV
E=np.array([e.vertices[:] for e in me.edges]);adj=[[] for _ in co]
for a,b in E:adj[a].append(int(b));adj[b].append(int(a))
def norm(v):return np.asarray(v)/max(np.linalg.norm(v),1e-9)
def comps(mask,minverts=6):
 remaining=set(np.where(mask)[0]);out=[]
 while remaining:
  todo=[remaining.pop()];ids=[]
  while todo:
   a=todo.pop();ids.append(a)
   for b in adj[a]:
    if b in remaining:remaining.remove(b);todo.append(b)
  if len(ids)>=minverts:out.append(np.array(ids))
 return out
skinbm=bmesh.new();skinbm.from_mesh(me);skinbm.verts.ensure_lookup_table()
bmesh.ops.delete(skinbm,geom=[v for v in skinbm.verts if wing[v.index] or pa[v.index]!=0],context='VERTS')
def ring(seed,axis):
 bm=skinbm.copy();r=bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=Vector(seed),plane_no=Vector(axis));es=[x for x in r['geom_cut'] if isinstance(x,bmesh.types.BMEdge)];nodes={v for e in es for v in e.verts};groups=[]
 while nodes:
  v=nodes.pop();todo=[v];group=[v]
  while todo:
   a=todo.pop()
   for e in a.link_edges:
    if e in es:
     b=e.other_vert(a)
     if b in nodes:nodes.remove(b);todo.append(b);group.append(b)
  if len(group)>3:groups.append(np.array([v.co[:] for v in group]))
 center=min((g.mean(0) for g in groups),key=lambda x:np.linalg.norm(x-seed)) if groups else np.array(seed);bm.free()
 assert np.linalg.norm(center-seed)<.065,('joint section missed',seed,center)
 return center
J={'Hips':[-.01,.07,.99],'Spine':[-.01,.025,1.10],'Spine1':[-.01,-.01,1.22],'Spine2':[-.01,-.012,1.355],'Neck':[-.01,-.04,1.45],'Head':[-.01,-.105,1.54]}
for sd,sg in [('L',1),('R',-1)]:
 J[sd+'Shoulder']=[-.01+sg*.06,-.018,1.36];J[sd+'Arm']=[-.01+sg*.204,-.01,1.37]
 elbow=np.array([.365,.018,1.05]) if sd=='L' else np.array([-.385,.018,1.05]);wrist=np.array([.505,-.07,.87]) if sd=='L' else np.array([-.525,-.07,.87])
 J[sd+'ForeArm']=ring(elbow,wrist-np.array(J[sd+'Arm'])).tolist();J[sd+'Hand']=ring(wrist,wrist-elbow).tolist()
 J[sd+'Thigh']=[-.01+sg*.115,.06,.995];J[sd+'Shin']=ring([-.01+sg*.173,-.06,.615],[0,0,1]).tolist();J[sd+'Tarsus']=ring([-.01+sg*.203,.216,.365],[0,0,1]).tolist()
 J[sd+'Foot']=ring([-.01+sg*.234,.19,.255],[0,0,1]).tolist()
skinbm.free();bones={}
def add(n,h,t,parent=None,deform=True):
 h=np.array(h);t=np.array(t);y=norm(t-h);x=norm(np.cross(y,[0,0,1])) if abs(y[2])<.9 else np.array([1.,0,0]);z=np.cross(x,y)
 bones[n]={'head':h.tolist(),'tail':t.tolist(),'parent':parent,'rot':np.column_stack([x,y,z]).tolist(),'deform':deform}
def chain(ns,points,parent=None,deform=True):
 for i,n in enumerate(ns):add(n,points[i],points[i+1],parent if i==0 else ns[i-1],deform)
add('Root',[0,0,0],[0,0,.1],None,False)
sp=['Hips','Spine','Spine1','Spine2','Neck','Head'];chain(sp,[J[n] for n in sp]+[[-.01,-.1,1.74]],'Root')
digits=[]
for sd,sg in [('L',1),('R',-1)]:
 ns=[sd+n for n in ['Shoulder','Arm','ForeArm','Hand']];h=np.array(J[sd+'Hand']);chain(ns,[J[n] for n in ns]+[(h+[sg*.035,0,-.08]).tolist()],'Spine2')
 ns=[sd+n for n in ['Thigh','Shin','Tarsus','Foot']];chain(ns,[J[n] for n in ns]+[[sg*.245-.01,-.035,.1]],'Hips')
 wp=[[-.01+sg*.10,.09,1.43],[-.01+sg*.52,.085,1.545],[-.01+sg*.99,.025,1.67],[-.01+sg*1.47,-.09,1.78]]
 chain([sd+'Wing'+str(i) for i in range(3)],wp,'Spine2',False)
 # Connectivity, rather than proximity, establishes each finger's ownership.
 cut=.80
 groups=comps((pa==0)&(co[:,0]*sg>.44)&(co[:,2]<cut)&(co[:,2]>.6),10)
 assert len(groups)==4,(sd,len(groups))
 groups.sort(key=lambda ids:co[ids,0].mean()*sg)
 thumb=groups[0];long=sorted(groups[1:],key=lambda ids:co[ids,1].mean());long.insert(1,np.where(pa==(8 if sd=='L' else 9))[0])
 for k,ids in enumerate([thumb]+long):
  points=co[ids];base=points[points[:,2]>points[:,2].max()-.014].mean(0);tip=points[points[:,2].argmin()];base[2]+=.026 if k else .025
  # The copied ring finger already extends inside the palm.
  if k==2:base[2]-=.025
  mid=base+(tip-base)*.53;ns=[sd+'Finger'+str(k)+'a',sd+'Finger'+str(k)+'b'];chain(ns,[base,mid,tip],sd+'Hand',False)
  digits.append({'side':sd,'kind':'hand','number':k,'ids':ids.tolist(),'names':ns,'points':[base.tolist(),mid.tolist(),tip.tolist()]})
 feet=comps((pa==0)&(co[:,0]*sg>.02)&(co[:,2]<.25)&(co[:,1]<.04),12);assert len(feet)==3,(sd,len(feet))
 feet.sort(key=lambda ids:co[ids,0].mean()*sg);back=np.where((pa==0)&(co[:,0]*sg>.02)&(co[:,2]<.24)&(co[:,1]>.255))[0]
 for k,ids in enumerate(feet+[back]):
  points=co[ids]
  if k<3:
   base=points[points[:,1]>points[:,1].max()-.02].mean(0);base[1]+=.025;tip=points[points[:,2].argmin()]
  else:
   base=points[points[:,1]<points[:,1].min()+.02].mean(0);base[1]-=.025;tip=points[points[:,1].argmax()]
  n=sd+'Toe'+str(k);add(n,base,tip,sd+'Foot',False);digits.append({'side':sd,'kind':'foot','number':k,'ids':ids.tolist(),'names':[n],'points':[base.tolist(),tip.tolist()]})
chain(['Tail0','Tail1'],[[-.01,.14,1.00],[-.01,.38,.94],[-.01,.59,.85]],'Hips',False)
arm=bpy.data.armatures.new('HarpySkeleton');rig=bpy.data.objects.new('Rig',arm);bpy.context.collection.objects.link(rig)
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
for n,b in bones.items():
 e=arm.edit_bones.new(n);e.head=b['head'];e.tail=b['tail'];e.align_roll(Vector(np.array(b['rot'])[:,2]));e.use_deform=b['deform']
 if b['parent']:e.parent=arm.edit_bones[b['parent']]
bpy.ops.object.mode_set(mode='OBJECT')
# The open feather/body shell has no stable heat solution; use measured anatomical chains.
names=list(bones);ni={n:i for i,n in enumerate(names)};W=np.zeros((NV,len(names)))
def setchain(ids,ns,points,root=None):
 ids=np.array(ids,dtype=int)
 if not len(ids):return
 points=np.array(points);arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(points,axis=0),axis=1))];best=np.full(len(ids),1e9);station=np.zeros(len(ids))
 for k,(a,b) in enumerate(zip(points[:-1],points[1:])):
  d=b-a;t=np.clip((co[ids]-a)@d/(d@d),0,1);dist=np.linalg.norm(co[ids]-a-t[:,None]*d,axis=1);hit=dist<best;best[hit]=dist[hit];station[hit]=arc[k]+t[hit]*(arc[k+1]-arc[k])
 loc=(arc[:-1]+arc[1:])/2;bn=ns
 if root:loc=np.r_[0,loc];bn=[root]+ns
 W[ids]=0
 for k,n in enumerate(bn):W[ids,ni[n]]=np.interp(station,loc,np.eye(len(bn))[k])
# Torso, then each connected limb, with a broad transition into the shoulder/hip.
zs=np.array([J[n][2] for n in sp])
for k,n in enumerate(sp):W[:,ni[n]]=np.interp(co[:,2],zs,np.eye(len(sp))[k])
for sd,sg in [('L',1),('R',-1)]:
 ids=np.where((~wing)&(pa==0)&(co[:,2]<1.01)&((co[:,0]+.01)*sg>0))[0]
 setchain(ids,[sd+n for n in ['Thigh','Shin','Tarsus','Foot']], [J[sd+n] for n in ['Thigh','Shin','Tarsus','Foot']]+[[-.01+sg*.245,-.035,.1]],'Hips')
 ids=np.where((~wing)&np.isin(pa,[0,8,9])&(co[:,2]>.60)&(co[:,2]<1.42)&((co[:,0]+.01)*sg>.10+.52*(1.36-co[:,2])))[0]
 setchain(ids,[sd+n for n in ['Arm','ForeArm','Hand']],[J[sd+n] for n in ['Arm','ForeArm','Hand']]+[(np.array(J[sd+'Hand'])+[sg*.035,0,-.12]).tolist()],sd+'Shoulder')
 x=(co[ids,0]+.01)*sg;k=np.clip((x-.105)/.135,0,1);k=k*k*(3-2*k);W[ids]*=k[:,None];W[ids,ni['Spine2']]+=1-k
# The crotch is one continuous surface; blend both thighs by distance across its centre.
ids=np.where((pa==0)&(co[:,2]>.76)&(co[:,2]<1.01)&(abs(co[:,0]+.01)<.09))[0]
sides=[]
for sd,sg in [('L',1),('R',-1)]:
 setchain(ids,[sd+n for n in ['Thigh','Shin','Tarsus','Foot']],[J[sd+n] for n in ['Thigh','Shin','Tarsus','Foot']]+[[-.01+sg*.245,-.035,.1]],'Hips');sides.append(W[ids].copy())
k=np.clip((co[ids,0]+.10)/.18,0,1);k=k*k*(3-2*k);W[ids]=sides[0]*k[:,None]+sides[1]*(1-k[:,None])
# Direct head ownership prevents a shrug or flap dragging the jaw or hair.
head=(~wing)&(co[:,2]>1.54)
W[head]=0;W[head,ni['Head']]=1
for part in [3,4,6,7]:ids=pa==part;W[ids]=0;W[ids,ni['Head']]=1
for part in [2,5]:ids=pa==part;setchain(np.where(ids)[0],['Spine','Spine1','Spine2'],[J['Spine'],J['Spine1'],J['Spine2'],J['Neck']])
for sd,sg in [('L',1),('R',-1)]:
 ids=np.where(wing&(co[:,0]*sg>0))[0];W[ids]=0;x=co[ids,0]*sg
 for k,n in enumerate([sd+'Wing0',sd+'Wing1',sd+'Wing2']):
  W[ids,ni[n]]=np.interp(x,[.29,.75,1.25],np.eye(3)[k])
tail=(~wing)&(pa==0)&(co[:,1]>.245)&(co[:,2]>.755)&(co[:,2]<1.06)
setchain(np.where(tail)[0],['Tail0','Tail1'],[bones['Tail0']['head'],bones['Tail0']['tail'],bones['Tail1']['tail']],'Hips')
# Grow digit ownership only through its own surface edges, then soften the joint band.
for d in digits:
 ids=set(d['ids']);pts=np.array(d['points']);ax=norm(pts[1]-pts[0]);partset=set(pa[list(ids)])
 for _ in range(12):
  grow=set()
  for i in ids:
   for j in adj[i]:
    if j in ids or pa[j] not in partset:continue
    dep=(co[j]-pts[0])@ax
    if dep>-.005 and np.linalg.norm(np.cross(co[j]-pts[0],ax))<(.023 if d['kind']=='hand' else .05):grow.add(j)
  if not grow:break
  ids.update(grow)
 d['ids']=sorted(ids);setchain(d['ids'],d['names'],pts,d['side']+('Hand' if d['kind']=='hand' else 'Foot'))
# Smooth transitions over connected edges; never blend across different separate pieces.
for _ in range(3):
 nxt=W.copy()
 for i,nb in enumerate(adj):
  if nb and not wing[i] and pa[i] in [0,8,9]:nxt[i]=.8*W[i]+.2*W[nb].mean(0)
 W=nxt
keep=np.argpartition(W,-4,axis=1)[:,-4:];mask=np.zeros_like(W,dtype=bool);np.put_along_axis(mask,keep,True,axis=1);W[~mask]=0;W/=W.sum(1)[:,None]
body.vertex_groups.clear()
for n in names:
 g=body.vertex_groups.new(name=n)
 for i in np.where(W[:,ni[n]]>1e-7)[0]:g.add([int(i)],float(W[i,ni[n]]),'REPLACE')
for b in arm.bones:b.use_deform=b.name!='Root'
mod=body.modifiers.new('HarpySkin','ARMATURE');mod.object=rig;body.parent=rig;rig.show_in_front=True
for pb in rig.pose.bones:pb.rotation_mode='QUATERNION'
assert len(bones)<=128 and np.allclose(W.sum(1),1)
out={'joints':J,'bones':bones,'digits':digits,'bone_count':len(bones)}
(P/'work/rig.json').write_text(json.dumps(out,indent=2));np.savez(P/'work/rig_weights.npz',weights=W,co=co,parts=pa,edges=E,names=np.array(names),wing=wing)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_v1.blend'));print('RIG',len(bones),'bones, digits',len(digits),'vertices',NV,flush=True)
