"""Branched slime rig: local stalk ownership, arc-length weights, rigid eyes/teeth."""
from pathlib import Path
import bpy, json, heapq, math
import numpy as np
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/geometry_v1.blend'))
o=bpy.data.objects['Nightmare'];me=o.data
co=np.array([v.co[:] for v in me.vertices]);adj=[[] for _ in co]
for e in me.edges:
 a,b=e.vertices;adj[a].append(b);adj[b].append(a)
labels=np.full(len(co),-1,int);pieces=[]
for v in range(len(co)):
 if labels[v]>=0:continue
 q=[v];labels[v]=len(pieces);ids=[]
 while q:
  a=q.pop();ids.append(a)
  for b in adj[a]:
   if labels[b]<0:labels[b]=labels[v];q.append(b)
 pieces.append(np.array(ids))
main=max(pieces,key=len)
# Restore the five spherical eyeballs after native silhouette fitting narrowed the body.
eyes=[a for a in pieces if 90<len(a)<125 and co[a,2].mean()>.4]
assert len(eyes)==5
for ids in eyes:
 center=co[ids].mean(0);co[ids,0]=center[0]+(co[ids,0]-center[0])/.7
for v,c in zip(me.vertices,co):v.co=c
paths=[
 ('NeckL',[(-.125,.0,.29),(-.145,.015,.46),(-.14,-.01,.59),(-.112,-.025,.74),(-.084,-.035,.85),(-.084,-.065,.93)],.080),
 ('NeckR',[(.11,.08,.29),(.15,.06,.46),(.16,.04,.63),(.16,.02,.79),(.175,.005,.87),(.175,-.025,.95)],.080),
 ('Eye0',[(-.16,-.13,.45),(-.19,-.16,.51),(-.245,-.21,.57),(-.266,-.226,.65)],.035),
 ('Eye1',[(-.055,-.19,.34),(-.045,-.19,.46),(-.044,-.186,.644)],.025),
 ('Eye2',[(.0,-.29,.32),(.02,-.32,.43),(.042,-.363,.556)],.027),
 ('Eye3',[(.14,.11,.40),(.18,.14,.48),(.222,.152,.618)],.027),
 ('Eye4',[(.18,-.02,.33),(.23,-.04,.40),(.268,-.05,.494)],.032)]
chains=[]
for name,points,radius in paths:
 q=np.array(points,float);arc=np.r_[0,np.linalg.norm(np.diff(q,axis=0),axis=1).cumsum()]
 # Keep the terminal mouth/eyeball rigid; the stem has four to seven flexion sections.
 end=arc[-1]-(.075 if name.startswith('Neck') else .05)
 ss=np.r_[np.linspace(0,end,max(4,int(end/.075))+1),arc[-1]]
 J=np.stack([np.interp(ss,arc,q[:,i]) for i in range(3)],1)
 names=[name+f'_{i:02}' for i in range(len(J)-2)]+[name+'_Tip']
 chains.append({'name':name,'joints':J,'names':names,'radius':radius})
arm=bpy.data.armatures.new('NightmareRig');rig=bpy.data.objects.new('NightmareRig',arm);bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT');eb=arm.edit_bones

def bone(name,a,b,parent=None,deform=True):
 x=eb.new(name);x.head=a;x.tail=b;x.use_deform=deform
 if parent:x.parent=eb[parent]
 x.align_roll(Vector((1,0,0)));return x
bone('Root',(0,0,0),(0,0,.10),deform=False)
bone('Body',(0,0,0),(0,0,.22),'Root',False)
lumps=[('Core',(0,0,0))]+[(f'Lump{i}',(x,y,0)) for i,(x,y) in enumerate([(-.18,-.27),(.18,-.27),(-.18,.02),(.18,.02),(-.15,.28),(.15,.28)])]
for name,a in lumps:bone(name,a,(a[0],a[1],.25),'Body')
for c in chains:
 c['parent']={'Eye0':'NeckL_01','Eye1':'Body','Eye2':'Body','Eye3':'NeckR_01','Eye4':'NeckR_00'}.get(c['name'],'Body')
 parent=c['parent']
 for i,name in enumerate(c['names']):
  bone(name,c['joints'][i],c['joints'][i+1],parent);parent=name
jaw_specs=[('JawL',(-.084,.035,.87),(-.084,-.14,.85),'NeckL_Tip'),('JawR',(.175,.065,.89),(.175,-.11,.87),'NeckR_Tip'),('JawFront',(-.04,-.29,.225),(-.04,-.43,.195),'Body')]
for name,a,b,parent in jaw_specs:bone(name,a,b,parent)
embedded=[]
for ids in pieces:
 if 90<len(ids)<125 and co[ids,2].mean()<.4:
  center=co[ids].mean(0);name=f'EmbeddedEye{len(embedded)}';bone(name,center,center+np.array([0,0,.04]),'Body');embedded.append((name,center.tolist(),ids.tolist()))
bone('FrontTop',(-.04,-.34,.26),(-.04,-.44,.26),'Body')
bpy.ops.object.mode_set(mode='OBJECT')
names=[b.name for b in arm.bones if b.use_deform];ix={n:i for i,n in enumerate(names)}
W=np.zeros((len(co),len(names)))
# Floor-anchored body lobes keep the underside down during squash and peristalsis.
centers=np.array([a for _,a in lumps]);D=np.linalg.norm(co[:,None,:2]-centers[None,:,:2],axis=2)
BW=np.exp(-D**2/.16**2);BW/=BW.sum(1)[:,None]
for i,(n,_) in enumerate(lumps):W[:,ix[n]]=BW[:,i]
chain_weights=[];cost=[]
for c in chains:
 J=c['joints'];seg=np.linalg.norm(np.diff(J,axis=0),axis=1);arc=np.r_[0,seg.cumsum()];mid=(arc[:-1]+arc[1:])/2
 dist=np.full(len(co),1e9);pos=np.zeros(len(co))
 for i,(a,b) in enumerate(zip(J[:-1],J[1:])):
  d=b-a;t=np.clip((co-a)@d/(d@d),0,1);dd=np.linalg.norm(co-(a+t[:,None]*d),axis=1);m=dd<dist
  dist[m]=dd[m];pos[m]=arc[i]+t[m]*seg[i]
 wt=np.zeros_like(W)
 for i,n in enumerate(c['names']):
  # Linear interpolation between segment centres.
  wt[:,ix[n]]=np.interp(pos,mid,np.eye(len(mid))[i])
 chain_weights.append(wt);cost.append(dist/c['radius'])
cost=np.array(cost);near=cost.argmin(0)
# Geodesic ownership on the connected skin; no nearest-neighbour jumps across air gaps.
seeds=[]
for v in main:
 if co[v,2]<.16 or (co[v,1]>.27 and co[v,2]<.38):seeds.append((0.,int(v),0))
 elif co[v,2]>.44 and cost[near[v],v]<1.7:seeds.append((0.,int(v),int(near[v])+1))
heapq.heapify(seeds);dist=np.full(len(co),np.inf);owner=np.zeros(len(co),int)
while seeds:
 d,v,label=heapq.heappop(seeds)
 if d>=dist[v]:continue
 dist[v]=d;owner[v]=label
 for b in adj[v]:
  nd=d+float(np.linalg.norm(co[b]-co[v]))
  if nd<dist[b]:heapq.heappush(seeds,(nd,b,label))
for k,c in enumerate(chains):
 ids=np.flatnonzero(owner==k+1);fade=np.clip((co[ids,2]-c['joints'][0,2]+.025)/.14,0,1)
 base=chain_weights[0 if c['parent'].startswith('NeckL') else 1][ids] if c['parent'].startswith('Neck') else W[ids]
 W[ids]=base*(1-fade[:,None])+chain_weights[k][ids]*fade[:,None]
# Detached eyeballs and teeth have one anatomical owner, never blended across two stalks.
rigid=[]
for ids in pieces:
 if len(ids)>150:continue
 center=co[ids].mean(0)
 if center[2]>.4:
  k=int(np.argmin([np.linalg.norm(center-c['joints'][-1]) for c in chains]));name=chains[k]['names'][-1];owner[ids]=k+1
  if k<2 and len(ids)<60 and center[2]<(.875 if k==0 else .895):name='JawL' if k==0 else 'JawR'
 else:
  name='JawFront' if len(ids)<60 and center[2]<.225 else ('FrontTop' if len(ids)<60 else next(n for n,c,vs in embedded if ids[0] in vs))
 W[ids]=0;W[ids,ix[name]]=1;rigid.extend(ids.tolist())
# Lower lips blend to their jaw at the hinge; upper pods remain on their terminal stalk bone.
for k,(name,a,b,parent) in enumerate(jaw_specs):
 if k<2:
  mask=(owner==k+1)&(labels==labels[main[0]])
  z0=.79 if k==0 else .81;hinge=.885 if k==0 else .905
  w=np.clip((co[:,2]-z0)/.035,0,1)*np.clip((hinge-co[:,2])/.035,0,1)*np.clip((a[1]+.02-co[:,1])/.065,0,1)
 else:
  mask=(labels==labels[main[0]])&(np.abs(co[:,0]+.04)<.13)&(co[:,1]<-.3)
  w=np.clip((co[:,2]-.12)/.035,0,1)*np.clip((.237-co[:,2])/.035,0,1)*np.clip((-.29-co[:,1])/.08,0,1)
 w*=mask;W*=1-w[:,None];W[:,ix[name]]+=w
for _ in range(5):
 new=W.copy()
 for v in main:
  if adj[v]:new[v]=.65*W[v]+.35*W[adj[v]].mean(0)
 W=new
# The front mouth cage follows its teeth; socket skin follows each embedded eyeball.
front=np.clip((.21-np.abs(co[:,0]+.04))/.045,0,1)*np.clip((-.20-co[:,1])/.07,0,1)
front*=np.clip((co[:,2]-.17)/.04,0,1)*np.clip((.40-co[:,2])/.06,0,1)*(labels==labels[main[0]])
lower=np.clip((.245-co[:,2])/.025,0,1)*np.clip((-.29-co[:,1])/.07,0,1)
W*=1-front[:,None];W[:,ix['FrontTop']]+=front*(1-lower);W[:,ix['JawFront']]+=front*lower
for name,center,ids in embedded:
 delta=np.linalg.norm(co-np.array(center),axis=1)
 socket=np.clip((.085-delta)/.025,0,1)*(labels==labels[main[0]])
 W*=1-socket[:,None];W[:,ix[name]]+=socket
# Four influences is the native runtime limit; normalise after truncation.
keep=np.argsort(W,axis=1)[:,-4:];out=np.zeros_like(W);np.put_along_axis(out,keep,np.take_along_axis(W,keep,1),1)
W=out/np.maximum(out.sum(1)[:,None],1e-12)
assert np.isfinite(W).all() and np.max(abs(W.sum(1)-1))<1e-8
for i,n in enumerate(names):
 vg=o.vertex_groups.new(name=n)
 for v in np.flatnonzero(W[:,i]>1e-6):vg.add([int(v)],float(W[v,i]),'REPLACE')
mod=o.modifiers.new('Skin','ARMATURE');mod.object=rig;o.parent=rig
attr=me.attributes.new('owner','INT','POINT');attr.data.foreach_set('value',owner.tolist())
for c in chains:c['joints']=c['joints'].tolist()
(P/'work/rig.json').write_text(json.dumps({'chains':chains,'jaws':jaw_specs,'lumps':lumps,'embedded_eyes':[(n,c) for n,c,vs in embedded],'bones':names,'rigid_vertices':rigid,'triangles':len(me.polygons)},indent=2))
np.savez_compressed(P/'work/rig_weights.npz',co=co,W=W,owner=owner,edges=np.array([e.vertices[:] for e in me.edges]))
print('RIG',len(arm.bones),'bones',len(me.polygons),'triangles; eyes',len(eyes),'rigid vertices',len(rigid))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_v1.blend'))
