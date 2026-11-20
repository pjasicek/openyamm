"""Measured dinosaur skeleton and anatomical chain weights; no humanoid retarget."""
import bpy,json
import numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/geometry_uv.blend'));body=bpy.data.objects['Body'];me=body.data
co=np.array([v.co[:] for v in me.vertices]);parts=np.array([a.value for a in me.attributes['part'].data]);edges=np.array([e.vertices[:] for e in me.edges]);bones={}
def chain(names,points,parent=None):
 for i,n in enumerate(names):bones[n]={'head':points[i],'tail':points[i+1],'parent':parent if i==0 else names[i-1]}
spine=[[0,.28,1.06],[0,-.12,1.18],[0,-.43,1.30],[0,-.53,1.51],[0,-.68,1.74],[0,-1.08,1.67]]
chain(['Hips','Chest','Neck1','Neck2','Head'],spine)
chain(['Jaw'],[[0,-.70,1.685],[0,-1.06,1.59]],'Head')
tail=[[0,.28,1.06],[0,.62,1.02],[0,.86,.84],[0,1.08,.68],[0,1.32,.55],[0,1.56,.47],[0,1.82,.425],[0,2.08,.402],[0,2.36,.40]]
chain([f'Tail{i+1}' for i in range(8)],tail,'Hips')
legs={'L':[[.21,.17,1.06],[.25,-.02,.66],[.25,.20,.37],[.29,.075,.125],[.33,-.18,.055]],'R':[[-.20,.31,1.04],[-.23,.22,.67],[-.25,.57,.45],[-.32,.54,.125],[-.36,.31,.055]]}
arms={}
for sd,s in [('L',1),('R',-1)]:
 chain([f'{n}_{sd}' for n in ['Thigh','Shin','Tarsus','Foot']],legs[sd],'Hips')
 arms[sd]=[[s*.13,-.43,1.24],[s*.23,-.43,1.065],[s*.23,-.67,1.065],[s*.22,-.79,.90]]
 chain([f'{n}_{sd}' for n in ['UpperArm','ForeArm','Hand']],arms[sd],'Chest')
 chain([f'Frill_{sd}'],[[s*.105,-.64,1.75],[s*.39,-.38,1.65]],'Head')
arm=bpy.data.armatures.new('ThunderLizardSkeleton');rig=bpy.data.objects.new('Rig',arm);bpy.context.collection.objects.link(rig)
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
for n,b in bones.items():
 e=arm.edit_bones.new(n);e.head=b['head'];e.tail=b['tail'];e.align_roll(Vector((0,0,1)) if abs((e.tail-e.head).normalized().z)<.9 else Vector((0,-1,0)))
 if b['parent']:e.parent=arm.edit_bones[b['parent']]
bpy.ops.object.mode_set(mode='OBJECT');names=list(bones);ni={n:i for i,n in enumerate(names)};W=np.zeros((len(co),len(names)))
def chain_weights(ids,ns,points):
 pts=np.array(points);arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(pts,axis=0),axis=1))];best=np.full(len(ids),1e10);station=np.zeros(len(ids));c=co[ids]
 for k,(a,b) in enumerate(zip(pts[:-1],pts[1:])):
  d=b-a;t=np.clip((c-a)@d/(d@d),0,1);distance=np.linalg.norm(c-a-t[:,None]*d,axis=1);m=distance<best;best[m]=distance[m];station[m]=arc[k]+t[m]*(arc[k+1]-arc[k])
 mids=(arc[1:]+arc[:-1])/2;out=np.zeros((len(ids),len(names)))
 for k,n in enumerate(ns):out[:,ni[n]]=np.interp(station,mids,np.eye(len(ns))[k])
 return out
ids=np.arange(len(co));W=chain_weights(ids,['Hips','Chest','Neck1','Neck2','Head'],spine)
# A wide pelvis blends into each thigh; distal limbs have exclusive anatomical ownership.
for sd,s in [('L',1),('R',-1)]:
 ids=np.where((co[:,0]*s>0)&(co[:,2]<1.18)&(co[:,1]>-.25)&(co[:,1]<.73))[0]
 leg=chain_weights(ids,[f'{n}_{sd}' for n in ['Thigh','Shin','Tarsus','Foot']],legs[sd]);fade=np.clip((1.13-co[ids,2])/.25,0,1)*np.clip((abs(co[ids,0])-.04)/.16+np.clip((.75-co[ids,2])/.15,0,1),0,1);W[ids]=fade[:,None]*leg+(1-fade[:,None])*W[ids]
 ids=np.where((co[:,0]*s>.10)&(co[:,1]<-.25)&(co[:,2]<1.29))[0]
 aw=chain_weights(ids,[f'{n}_{sd}' for n in ['UpperArm','ForeArm','Hand']],arms[sd]);fade=np.clip((1.28-co[ids,2])/.13,0,1)*np.clip((co[ids,0]*s-.10)/.07,0,1)*np.clip((-.25-co[ids,1])/.22,0,1);W[ids]=fade[:,None]*aw+(1-fade[:,None])*W[ids]
ids=np.where(co[:,1]>.30)[0];tw=chain_weights(ids,[f'Tail{i+1}' for i in range(8)],tail);fade=np.clip((co[ids,1]-.30)/.48,0,1)*np.clip((co[ids,2]-.60)/.30,0,1);fade=np.where(co[ids,1]>.78,1,fade);W[ids]=fade[:,None]*tw+(1-fade[:,None])*W[ids]
# Head is rigid around the eye sockets; only the jaw and lateral membranes articulate.
ids=np.where((co[:,2]>1.57)&(co[:,1]<-.55))[0];W[ids]=0;W[ids,ni['Head']]=1
for sd,s in [('L',1),('R',-1)]:
 ids=np.where((co[:,0]*s>.13)&(co[:,2]>1.34)&(co[:,1]>-.66)&(co[:,1]<-.22))[0];fade=np.clip((co[ids,0]*s-.13)/.15,0,1);W[ids]*=1-fade[:,None];W[ids,ni[f'Frill_{sd}']]+=fade
# The open mouth separates upper and lower branches ahead of the hinge; identify them by connectivity.
adj=[[] for _ in co]
for a,b in edges:adj[a].append(int(b));adj[b].append(int(a))
mask=(co[:,1]<-.80)&(co[:,2]>1.45)&(parts==0);seen=set();components=[]
for i in np.where(mask)[0]:
 if i in seen:continue
 todo=[int(i)];seen.add(int(i));ids=[]
 while todo:
  v=todo.pop();ids.append(v)
  for j in adj[v]:
   if mask[j] and j not in seen:seen.add(j);todo.append(j)
 components.append(ids)
lower=min([ids for ids in components if len(ids)>100],key=lambda ids:co[ids,2].mean())
ids=np.where((co[:,1]<-.79)&(co[:,2]>1.48))[0];W[ids]=0;W[ids,ni['Head']]=1
W[lower]=0;W[lower,ni['Jaw']]=1
W[parts==1]=0;W[parts==1,ni['Jaw']]=1
W[np.isin(parts,[2,3])]=0;W[np.isin(parts,[2,3]),ni['Head']]=1
adj=[[] for _ in co]
for a,b in edges:adj[a].append(int(b));adj[b].append(int(a))
# Distal limbs are disconnected below these cuts; ownership must survive claws crossing the midline.
for region in ['legs','hands']:
 mask=((co[:,2]<.62)&(co[:,1]<.78)) if region=='legs' else ((co[:,1]<-.62)&(co[:,2]<1.15))
 seen=set()
 for start in np.where(mask)[0]:
  if int(start) in seen:continue
  todo=[int(start)];seen.add(int(start));ids=[]
  while todo:
   v=todo.pop();ids.append(v)
   for j in adj[v]:
    if mask[j] and j not in seen:seen.add(j);todo.append(j)
  if len(ids)<10:continue
  sd='L' if co[ids,0].mean()>0 else 'R'
  ns=[f'{n}_{sd}' for n in (['Thigh','Shin','Tarsus','Foot'] if region=='legs' else ['UpperArm','ForeArm','Hand'])]
  W[ids]=chain_weights(np.array(ids),ns,legs[sd] if region=='legs' else arms[sd])
for _ in range(2):
 out=W.copy()
 for i,nb in enumerate(adj):
  if nb and parts[i]==0:out[i]=.75*W[i]+.25*W[nb].mean(0)
 W=out
for sd in 'LR':
 legcols=[ni[n+'_'+sd] for n in ['Thigh','Shin','Tarsus','Foot']];ids=np.where((W[:,legcols].sum(1)>.5)&(co[:,2]<.20))[0];fade=np.clip((.20-co[ids,2])/.085,0,1);W[ids]*=1-fade[:,None];W[ids,ni['Foot_'+sd]]+=fade
keep=np.argpartition(W,-4,axis=1)[:,-4:];mask=np.zeros_like(W,dtype=bool);np.put_along_axis(mask,keep,True,axis=1);W[~mask]=0;W/=W.sum(1)[:,None]
assert np.isfinite(W).all() and np.max(abs(W.sum(1)-1))<1e-8
for n in names:
 g=body.vertex_groups.new(name=n)
 for i in np.where(W[:,ni[n]]>1e-7)[0]:g.add([int(i)],float(W[i,ni[n]]),'REPLACE')
mod=body.modifiers.new('ThunderLizardSkin','ARMATURE');mod.object=rig;body.parent=rig;rig.show_in_front=True
for pb in rig.pose.bones:pb.rotation_mode='QUATERNION'
(P/'work/rig.json').write_text(json.dumps({'bones':bones,'legs':legs,'tail':tail,'arms':arms,'bone_count':len(bones),'weight_method':'Anatomical chain arc interpolation, explicit limb ownership and two topology smoothing passes; normalized top four'},indent=2)+'\n');np.savez(P/'work/rig_weights.npz',co=co,weights=W,parts=parts,edges=edges,names=np.array(names));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_v1.blend'));print('RIG',len(bones),'bones',len(co),'vertices')
