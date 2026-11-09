"""Bake garment chains with damped motion, body capsules, floor contact and closed robe neighbours.
The existing druidess chain solver supplies the method; this version supports the Necromancer's four garment owners.
"""
from pathlib import Path
import bpy,json,math
import numpy as np
from mathutils import Vector,Matrix,Quaternion
p=Path(__file__).resolve().parents[1]
# gait2 (2026-10-21): INPUT_BLEND/OUTPUT_BLEND/CLIPS/LOOPS may be given as runpy init_globals (defaults: production run).
bpy.ops.wm.open_mainfile(filepath=str(p/'work'/globals().get('INPUT_BLEND','motion_grounded.blend')))
sc=bpy.context.scene;rig=bpy.data.objects['Rig'];CH=json.loads(sc['garment_chains'])
FLOOR=.015;SUB=4;DAMP=.80;STIFF=.28
REST=[];LENS=[];local={};parent_rest={}
for c in CH:
 j=np.array(c['pts']);r=np.array([v for a,b in zip(j[:-1],j[1:]) for v in [a,(a+b)/2]]+[j[-1]])
 REST.append(r);LENS.append(np.linalg.norm(np.diff(j,axis=0),axis=1))
 parent_rest[c['parent']]=rig.data.bones[c['parent']].matrix_local.copy()
 for i,n in enumerate(c['bones']):
  par=c['parent'] if i==0 else c['bones'][i-1]
  local[n]=rig.data.bones[par].matrix_local.inverted()@rig.data.bones[n].matrix_local
CAPS=[('B_Pelvis','B_Spine2',.13),('B_Spine2','B_Neck',.125),('B_Head','B_Head',.075)]
for s in 'LR':
 CAPS += [(f'B_{s}_Thigh',f'B_{s}_Calf',.075),(f'B_{s}_Calf',f'B_{s}_Foot',.060),(f'B_{s}_Foot',f'B_{s}_Toe0',.050),(f'B_{s}_UpperArm',f'B_{s}_Forearm',.060),(f'B_{s}_Forearm',f'B_{s}_Hand',.042)]
NEIGH=[(i,(i+1)%12) for i in range(12)]+[(12,13),(14,15),(16,17)]
NREST={(a,b):np.linalg.norm(REST[a][1:]-REST[b][1:],axis=1) for a,b in NEIGH}
ids=np.cumsum([0]+[len(x)-1 for x in REST]);margins=np.concatenate([np.full(len(r)-1,.012 if c['kind']=='robe' else .007) for c,r in zip(CH,REST)])
def setact(a):
 rig.animation_data_create();rig.animation_data.action=a
 if a is not None and a.slots:rig.animation_data.action_slot=a.slots[0]
mesh=bpy.data.objects['Body'];pv=np.array([v.value for v in mesh.data.attributes['piece'].data]);co=np.array([tuple(v.co) for v in mesh.data.vertices]);FOOT_CAP={}
for side,sign in [('L',1),('R',-1)]:
 points=co[(pv==12)&(co[:,0]*sign>0)&(co[:,2]<.10)]
 heel=points[points[:,1]>np.quantile(points[:,1],.85)].mean(0);toe=points[points[:,1]<np.quantile(points[:,1],.15)].mean(0)
 for role,point,bone in [('heel',heel,f'B_{side}_Foot'),('toe',toe,f'B_{side}_Toe0')]:
  point[2]=.045;FOOT_CAP[side,role]=(bone,rig.data.bones[bone].matrix_local.inverted()@Vector(point))
LEG_LEVELS=[('B_Pelvis','B_Pelvis')]+[(f'B_L_{n}',f'B_R_{n}') for n in ['Thigh','Calf','Foot','Toe0']]
LEG_REST=np.array([np.mean([np.array(rig.data.bones[n].head_local) for n in pair],axis=0) for pair in LEG_LEVELS])
def state(f,name):
 sc.frame_set(f);mats={n:rig.pose.bones[n].matrix.copy() for n in parent_rest};targets=[]
 pel=rig.pose.bones['B_Pelvis'].matrix@rig.data.bones['B_Pelvis'].matrix_local.inverted();forward=pel.to_3x3()@Vector((0,-1,0));yaw=math.atan2(forward.x,-forward.y)
 Ry=np.array(Matrix.Rotation(yaw,3,'Z'))
 caps=[]
 for a,b,radius in CAPS:
  if a.endswith('Foot'):
   side=a[2];bn,pt=FOOT_CAP[side,'heel'];heel=np.array(rig.pose.bones[bn].matrix@pt);bn,pt=FOOT_CAP[side,'toe'];toe=np.array(rig.pose.bones[bn].matrix@pt);caps.append((heel,toe,.055))
  else:caps.append((np.array(rig.pose.bones[a].head),np.array(rig.pose.bones[b].head),radius))
 leg_centres=np.array([np.mean([np.array(rig.pose.bones[n].head) for n in pair],axis=0) for pair in LEG_LEVELS]);leg_rot=[]
 for pair in LEG_LEVELS:
  qs=[(rig.pose.bones[n].matrix.to_3x3()@rig.data.bones[n].matrix_local.to_3x3().inverted()).to_quaternion() for n in pair];leg_rot.append(qs[0].slerp(qs[1],.5))
 spheres=[(a+(b-a)*t,r+.07) for (na,nb,_),(a,b,r) in zip(CAPS,caps) if any(k in na for k in ['Thigh','Calf','Foot']) for t in np.linspace(0,1,9)]
 for ci,(c,r) in enumerate(zip(CH,REST)):
  M=mats[c['parent']]@parent_rest[c['parent']].inverted();root=np.array(M@Vector(r[0]));off=r-r[0]
  target=root+off@Ry.T
  if c['kind']=='robe':
   for k,q in enumerate(r[1:],1):
    level=int(np.clip(np.searchsorted(-LEG_REST[:,2],-q[2])-1,0,len(LEG_REST)-2));t=float(np.clip((LEG_REST[level,2]-q[2])/(LEG_REST[level,2]-LEG_REST[level+1,2]),0,1))
    centre0=LEG_REST[level]*(1-t)+LEG_REST[level+1]*t;centre=leg_centres[level]*(1-t)+leg_centres[level+1]*t;R=np.array(leg_rot[level].slerp(leg_rot[level+1],t).to_matrix())
    radial=q-centre0;target[k]=centre+R@radial
    # Enclose each leg capsule even when it moves completely outside the previous cloth surface.
    axis=R[:,2];out=R@np.array([math.sin(c['angle']),math.cos(c['angle']),0]);plane=centre+axis*radial[2];extent=float((target[k]-plane)@out)
    for ball,rad in spheres:
     v=ball-plane;z=float(v@axis);disk=rad*rad-z*z
     if disk<=0:continue
     along=float(v@out);perp=float(v@v-z*z-along*along)
     if perp<disk:extent=max(extent,along+math.sqrt(max(0,disk-perp)))
    target[k]=plane+out*extent
  elif name=='Death':
   up=M.to_3x3()@Vector((0,0,1));w=float(np.clip((math.degrees(up.angle(Vector((0,0,1))))-20)/55,0,1));w=w*w*(3-2*w)
   full=np.array([tuple(M@Vector(q)) for q in r]);full[1:,2]-=.045*np.linspace(0,1,len(r)-1)
   target=target*(1-w)+full*w
  target[0]=root;targets.append(target)
 return targets,caps,mats

FLOORS=[.075 if c['kind']=='hair' else (.045 if c['kind']=='cuff' else .025) for c in CH]
def lengths_floor(X):
 for ci,x in enumerate(X):
  floor=FLOORS[ci]
  for k,L in enumerate(LENS[ci]):
   a=2*k;b=a+2;d=x[b]-x[a];d/=max(np.linalg.norm(d),1e-9);x[b]=x[a]+d*L
   if x[b,2]<floor:
    dz=floor-x[a,2];horizontal=d.copy();horizontal[2]=0;horizontal/=max(np.linalg.norm(horizontal),1e-9)
    x[b]=x[a]+horizontal*math.sqrt(max(0,L*L-dz*dz))+np.array([0,0,dz])
   x[a+1]=(x[a]+x[b])/2

def collide(X,caps):
 P=np.concatenate([x[1:] for x in X])
 for a,b,r in caps:
  ab=b-a;t=np.clip((P-a)@ab/max(ab@ab,1e-9),0,1);q=a+t[:,None]*ab;d=P-q;dist=np.linalg.norm(d,axis=1);need=r+margins-dist;hit=need>0
  if not hit.any():continue
  direction=d/np.maximum(dist,1e-9)[:,None]
  # At floor level, the cloth slides around the solid body instead of being repeatedly pushed through the floor.
  blocked=hit&(P[:,2]+direction[:,2]*need<FLOOR)
  direction[blocked,2]=0;direction[blocked]/=np.maximum(np.linalg.norm(direction[blocked],axis=1),1e-9)[:,None]
  P[hit]+=direction[hit]*np.minimum(need[hit],.012)[:,None]
 P[:,2]=np.maximum(P[:,2],FLOOR)
 for ci,x in enumerate(X):x[1:]=P[ids[ci]:ids[ci+1]]

def key(f,X,mats):
 for c,x in zip(CH,X):
  parent=mats[c['parent']]
  for k,n in enumerate(c['bones']):
   inherited=parent@local[n];direction=Vector(x[2*k+2])-inherited.translation
   q=(inherited.to_3x3()@Vector((0,1,0))).rotation_difference(direction.normalized());posed=(q.to_matrix()@inherited.to_3x3()).to_4x4();posed.translation=inherited.translation
   pb=rig.pose.bones[n];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=(inherited.inverted()@posed).to_quaternion();pb.keyframe_insert('rotation_quaternion',frame=f);parent=posed

report={}
for name in globals().get('CLIPS',['Standing','Walking','Running','Attack','Cast','Hit','Death','Fidget']):
 act=bpy.data.actions[name];setact(act);end=int(act.frame_range[1]);loop=name in globals().get('LOOPS',['Standing','Walking','Running','Fidget']);states=[state(f,name) for f in range(end+1)]
 seq=list(range(end))*3+[end] if loop else [0]*24+list(range(end+1))+([end]*18 if name=='Death' else [])
 start=2*end if loop else 24
 X=[a.copy() for a in states[seq[0]][0]];V=[np.zeros_like(x) for x in X];prev=states[seq[0]];saved=[]
 for it,f in enumerate(seq):
  cur=states[f]
  for sub in range(SUB):
   w=(sub+1)/SUB;targets=[a*(1-w)+b*w for a,b in zip(prev[0],cur[0])];caps=[(a0*(1-w)+a1*w,b0*(1-w)+b1*w,r) for (a0,b0,r),(a1,b1,_) in zip(prev[1],cur[1])];old=[x.copy() for x in X]
   for ci,x in enumerate(X):
    x[1:]+=V[ci][1:]*DAMP+(targets[ci][1:]-x[1:])*STIFF;x[0]=targets[ci][0]
   for _ in range(3):
    lengths_floor(X)
    for a,b in NEIGH:
     d=X[b][1:]-X[a][1:];L=np.linalg.norm(d,axis=1);r=NREST[(a,b)];delta=np.where(L>1.06*r,L-1.06*r,np.where(L<.65*r,L-.65*r,0));corr=d/np.maximum(L,1e-9)[:,None]*delta[:,None]*.4;X[a][1:]+=corr;X[b][1:]-=corr
    collide(X,caps)
   lengths_floor(X);V=[x-o for x,o in zip(X,old)]
  prev=cur
  if it>=start:saved.append(([x.copy() for x in X],cur[2]))
 # Smooth trajectories before baking, then restore exact rigid lengths and floor clearance.
 n=len(saved);sm=[];radius=3;kernel=np.exp(-.5*(np.arange(-radius,radius+1)/1.2)**2);kernel/=kernel.sum()
 for i in range(n):
  inds=[(i+k)%(n-1) if loop else min(n-1,max(0,i+k)) for k in range(-radius,radius+1)]
  row=[sum(saved[j][0][c]*w for j,w in zip(inds,kernel)) for c in range(len(CH))]
  for c in range(len(CH)):row[c][0]=saved[i][0][c][0]
  lengths_floor(row);sm.append(row)
 if loop:sm[-1]=[x.copy() for x in sm[0]]
 for i,x in enumerate(sm):key(i,x,saved[i][1])
 act.use_frame_range=True;act.frame_start=0;act.frame_end=n-1
 for layer in act.layers:
  for strip in layer.strips:
   for cb in strip.channelbags:
    for fc in cb.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
 arr=np.array([np.concatenate(x) for x in sm]);assert np.isfinite(arr).all()
 report[name]={'frames':n,'floor_min_m':float(arr[:,:,2].min()),'max_point_step_cm':float(np.linalg.norm(np.diff(arr,axis=0),axis=2).max()*100)}
 print('GARMENT_SIM',name,report[name],flush=True)
setact(None)
for b in rig.pose.bones:b.matrix_basis.identity()
old=json.loads((p/'work/garment_sim.json').read_text()) if globals().get('CLIPS') else {}
old.update(report);(p/'work/garment_sim.json').write_text(json.dumps(old,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work'/globals().get('OUTPUT_BLEND','rig_animated.blend')))
