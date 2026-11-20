"""Measured source-frame upper body, connectivity-fitted fingers, vortex chain and detachable jewelry."""
import bpy,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/fitted_body.blend'))
body=bpy.data.objects['Body'];me=body.data;co=np.array([v.co[:] for v in me.vertices]);part=np.array([v.value for v in me.attributes['part'].data]);E=np.array([e.vertices[:] for e in me.edges]);NV=len(co)
J=json.loads((P/'work/joints_final.json').read_text())['joints'];SRC=json.loads((P/'work/source_rest.json').read_text());FIT=json.loads((P/'work/fingers_fit.json').read_text());B={}
def norm(v):return v/max(np.linalg.norm(v),1e-9)
def add(n,h,t,parent=None,r=None):
 h=np.array(h);t=np.array(t);y=norm(t-h)
 if r is None:
  x=norm(np.cross(y,[0,0,1])) if abs(y[2])<.95 else np.array([1.,0,0]);r=np.column_stack([x,y,np.cross(x,y)])
 B[n]={'head':h.tolist(),'tail':t.tolist(),'parent':parent,'rot':np.array(r).tolist()}
add('Root',[0,0,0],[0,0,.1]);add('BodyRoot',J['Pelvis'],np.array(J['Pelvis'])+[0,0,.1],'Root')
child={'Pelvis':'Spine','Spine':'Spine1','Spine1':'Spine2','Spine2':'Neck','Neck':'Head'}
for sd in ['L','R']:child.update({sd+'_Clavicle':sd+'_UpperArm',sd+'_UpperArm':sd+'_Forearm',sd+'_Forearm':sd+'_Hand'})
order=['Pelvis','Spine','Spine1','Spine2','Neck','Head']+[sd+'_'+x for sd in ['L','R'] for x in ['Clavicle','UpperArm','Forearm','Hand']]
for short in order:
 n='B_'+short;h=np.array(J[short]);cs=child.get(short);t=np.array(J[cs]) if cs else h+[0,0,.09];r=Matrix(SRC[n]['rot']);par=SRC[n]['parent'] if short!='Pelvis' else 'BodyRoot'
 if cs:
  source=Vector(SRC['B_'+cs]['head'])-Vector(SRC[n]['head']);r=source.rotation_difference(Vector(t-h)).to_matrix()@r
 add(n,h,t,par,r)
chains={}
def resample(p):
 a=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))];return np.column_stack([np.interp(np.array([0,.46,.77,1])*a[-1],a,p[:,i]) for i in range(3)])
for sd in ['L','R']:
 pts={f:resample(np.array(FIT[sd][name])) for f,name in enumerate(['thumb','index','middle','ring','pinky'])};wr=np.array(J[sd+'_Hand'])
 def frame(f,t):
  f=norm(f);t=norm(t-f*np.dot(t,f));return np.column_stack([f,t,np.cross(f,t)])
 fsrc=np.array(SRC['B_'+sd+'_Finger2']['head'])-SRC['B_'+sd+'_Hand']['head'];tsrc=np.array(SRC['B_'+sd+'_Finger1']['head'])-SRC['B_'+sd+'_Finger4']['head'];fo=pts[2][0]-wr;to=pts[1][0]-pts[4][0]
 swing=frame(fo,to)@frame(fsrc,tsrc).T;B['B_'+sd+'_Hand']['rot']=(swing@np.array(SRC['B_'+sd+'_Hand']['rot'])).tolist();palm=norm(np.cross(fo,to));palm*=1 if palm[1]<0 else -1
 for f,points in pts.items():
  names=[f'B_{sd}_Finger{f}'+suffix for suffix in ['', '1','2']];chains[sd,f]=(names,points)
  for i,n in enumerate(names):
   y=norm(points[i+1]-points[i]);x=norm(np.cross(y,palm));add(n,points[i],points[i+1],'B_'+sd+'_Hand' if i==0 else names[i-1],np.column_stack([x,y,np.cross(x,y)]))
# Measured midline of the shortened tail; all overlapping vortex shells share the same field.
points=np.array([[0,0,1.11],[0,.01,.97],[0,.02,.82],[0,.045,.66],[0,.08,.51],[0,.14,.37],[0,.24,.24],[0,.36,.16],[0,.50,.14],[0,.62,.16],[0,.72,.21],[0,.78,.29]])
for i in range(len(points)-1):add(f'Vortex_{i:02}',points[i],points[i+1],'BodyRoot' if not i else f'Vortex_{i-1:02}')
jewels={5:('GoldBracer','B_L_Forearm'),10:('GoldArmlet','B_R_UpperArm'),11:('GoldBracelet','B_R_Forearm')}
for partnum,(n,follow) in jewels.items():
 c=co[part==partnum].mean(0);add(n,c,c+[0,0,.08],'Root')
arm=bpy.data.armatures.new('GenieSkeleton');rig=bpy.data.objects.new('Rig',arm);bpy.context.collection.objects.link(rig);bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
for n,b in B.items():
 e=arm.edit_bones.new(n);h=np.array(b['head']);r=np.array(b['rot']);e.head=h;e.tail=h+r[:,1]*max(.02,np.linalg.norm(np.array(b['tail'])-h));e.align_roll(Vector(r[:,2]));e.use_deform=n not in ['Root','BodyRoot']
 if b['parent']:e.parent=arm.edit_bones[b['parent']]
bpy.ops.object.mode_set(mode='OBJECT');names=list(B);ni={n:i for i,n in enumerate(names)};W=np.zeros((NV,len(names)))
def closest(p,pts):
 arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(pts,axis=0),axis=1))];best=np.full(len(p),1e9);s=np.zeros(len(p))
 for i,(a,b) in enumerate(zip(pts[:-1],pts[1:])):
  v=b-a;t=np.clip((p-a)@v/(v@v),0,1);d=np.linalg.norm(p-a-t[:,None]*v,axis=1);m=d<best;best[m]=d[m];s[m]=arc[i]+t[m]*(arc[i+1]-arc[i])
 return s,arc
ids=np.where(np.isin(part,[0,1,4,6,8,12]))[0];s,arc=closest(co[ids],points);stations=(arc[:-1]+arc[1:])/2
for i in range(len(stations)):W[ids,ni[f'Vortex_{i:02}']]=np.interp(s,stations,np.eye(len(stations))[i])
sp=['B_'+n for n in ['Pelvis','Spine','Spine1','Spine2','Neck','Head']];z=[B[n]['head'][2] for n in sp];ids=np.where(part==2)[0]
for k,n in enumerate(sp):W[ids,ni[n]]=np.interp(co[ids,2],z,np.eye(len(sp))[k])
adj=[[] for _ in co]
for a,b in E:adj[a].append(int(b));adj[b].append(int(a))
for sd,sign in [('L',1),('R',-1)]:
 ns=['B_'+sd+'_'+n for n in ['UpperArm','Forearm','Hand']];pts=np.array([J[sd+'_'+n] for n in ['UpperArm','Forearm','Hand']]);ids=np.where(np.isin(part,[2,3])&(co[:,0]*sign>.18)&(co[:,2]<1.74))[0];s,arc=closest(co[ids],pts)
 # Transition at measured joints; arm weights fade medially through the pectoral attachment.
 station=np.array([0,arc[1]-.075,arc[1]+.075,arc[2]-.045,arc[2]+.045]);weights=np.zeros((len(ids),len(names)))
 for k,n in enumerate(ns):weights[:,ni[n]]=np.interp(s,station,[[1,1,0,0,0],[0,0,1,1,0],[0,0,0,0,1]][k])
 boundary=.19+.10*np.clip((1.61-co[ids,2])/.25,0,1);blend=np.clip((co[ids,0]*sign-boundary)/.13,0,1);W[ids]=W[ids]*(1-blend[:,None])+weights*blend[:,None]
 wr=np.array(J[sd+'_Hand']);axis=norm(wr-np.array(J[sd+'_Forearm']));handids=np.where(np.isin(part,[2,3])&(co[:,0]*sign>.45)&((co-wr)@axis>0))[0];W[handids]=0;W[handids,ni['B_'+sd+'_Hand']]=1
 owners={int(v):f for f,name in enumerate(['thumb','index','middle','ring','pinky']) for v in FIT[sd]['verts'][name]};allowed=set(handids)
 for _ in range(12):
  new={}
  for v,f in owners.items():
   nsf,fp=chains[sd,f];d=fp[1]-fp[0]
   for w in adj[v]:
    if w in owners or w in new or w not in allowed:continue
    if (co[w]-fp[0])@d/(d@d)>.08 and min(np.linalg.norm(co[w]-q) for q in fp)<.055:new[w]=f
  if not new:break
  owners.update(new)
 for f in range(5):
  ids=np.array([v for v,k in owners.items() if k==f]);nsf,fp=chains[sd,f];s,arc=closest(co[ids],fp);W[ids]=0;st=np.r_[0,(arc[:-1]+arc[1:])/2];gn=['B_'+sd+'_Hand']+nsf
  for k,n in enumerate(gn):W[ids,ni[n]]=np.interp(s,st,np.eye(len(gn))[k])
 # Diffusion only on skin retains continuity across the wrist and knuckle webs.
 smoothids=np.where(np.isin(part,[2,3])&(co[:,0]*sign>.20)&(co[:,2]<1.7))[0]
 for _ in range(3):
  old=W.copy()
  for v in smoothids:
   if adj[v]:W[v]=.6*old[v]+.4*old[adj[v]].mean(0)
# Position-weighted shoulder diffusion avoids discontinuities across tiny irregular Meshy edges.
sv=np.where((part==2)&(np.abs(co[:,0])>.17)&(np.abs(co[:,0])<.48)&(co[:,2]>1.24)&(co[:,2]<1.73))[0]
allskin=np.where(part==2)[0];dist=np.linalg.norm(co[sv,None]-co[allskin],axis=2);kernel=np.exp(-.5*(dist/.036)**2);kernel[dist>.10]=0
W[sv]=kernel@W[allskin]/kernel.sum(1)[:,None]
for partnum,(n,follow) in jewels.items():W[part==partnum]=0;W[part==partnum,ni[n]]=1
for partnum in [7,9,13,14,15,16]:W[part==partnum]=0;W[part==partnum,ni['B_Head']]=1
sums=W.sum(1);assert (sums>0).all(),np.where(sums==0);W/=sums[:,None]
# Four strongest influences for the full-detail consumer.
keep=np.argsort(W,axis=1)[:,-4:];out=np.zeros_like(W);np.put_along_axis(out,keep,np.take_along_axis(W,keep,axis=1),axis=1);W=out/out.sum(1)[:,None]
body.vertex_groups.clear()
for n in names:
 g=body.vertex_groups.new(name=n)
 for v in np.where(W[:,ni[n]]>1e-6)[0]:g.add([int(v)],float(W[v,ni[n]]),'REPLACE')
body.parent=rig;mod=body.modifiers.new('Skin','ARMATURE');mod.object=rig
for pb in rig.pose.bones:pb.rotation_mode='QUATERNION'
D={'bones':B,'jewels':{str(k):{'bone':n,'follow':f} for k,(n,f) in jewels.items()},'tail':points.tolist(),'weights':{'unweighted':0,'max_influences':4}}
(P/'work/rig.json').write_text(json.dumps(D,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_v1.blend'));print('RIG',len(B),'bones',len(co),'vertices')
