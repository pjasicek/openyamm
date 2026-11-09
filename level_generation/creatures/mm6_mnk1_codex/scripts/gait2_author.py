"""Gait rework (2026-10-21): author Walk2 and Run2 on the export master, keeping the existing nine clips.

The old Walking is a 0.46 m procedural shuffle (authored 0.57 m/s), so the game played it at 3-8x. The new clips take
their legs from Mixamo sources chosen by measured natural speed (work/gait2_sources.json):
- Walk2: Mixamo "Walk" (1.0 s cycle, natural stride 2.36 leg lengths), stride WALK_STRIDE m.
- Run2: Mixamo "Standard Run" (0.733 s cycle), stride RUN_STRIDE m (forward travel scaled, playbook run rule).
Legs: the source's own ankle paths relative to its hip centre (forward offsets x stride scale, heights and lateral
offsets x the leg-length ratio), the source foot pitch about the lateral axis, two-bone IK with the knee forward, a
pelvis height of PEL x Standing plus the source's hip bob shape, pelvis lowered only where a leg cannot reach, and a
boot floor clamp. Upper body: the native folded-arm Standing pose (every arm, sleeve, cuff and cloth support local
from Standing frame 0, so the arms ride the chest), a forward lean, the source hip yaw/roll scaled with a chest
counter-turn, and a head that keeps the gaze level. The leg-driven robe then follows; cloth-only floor offsets
(review3_floor.py rule) keep its hem above the floor. Writes work/gait2.blend.
Args: -- [WALK_STRIDE RUN_STRIDE]"""
import bpy,json,math,sys,os
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
p=Path(__file__).resolve().parents[1];repo=p.parents[2]
FOOT_BACK=.03
# Share of the source foot roll kept: the boots are rigid and a full heel-up toe-off lifts the heel out of the back of the robe.
PITCH=float(os.environ.get('G2_PITCH',.5))
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
WALK_STRIDE=float(args[0]) if args else 1.65
RUN_STRIDE=float(args[1]) if len(args)>1 else 2.55
CLIPS=[('Walk2',repo/'anim_library/mixamo/Walk.fbx',dict(stride=WALK_STRIDE,frames=24,pitch=PITCH,lift=float(os.environ.get('G2_WALK_LIFT',1.)),robe_thigh=float(os.environ.get('G2_WALK_ROBE',.5)),pel=.975,bob=.010,lean=4.,yaw=.6,roll=.5,chest=-.35,sway=.6)),
       ('Run2',repo/'anim_library/mixamo/Standard Run.fbx',dict(stride=RUN_STRIDE,frames=20,pitch=float(os.environ.get('G2_RUN_PITCH',0.)),lift=float(os.environ.get('G2_RUN_LIFT',.45)),robe_thigh=float(os.environ.get('G2_RUN_ROBE',.4)),pel=.925,bob=.045,lean=11.,yaw=.5,roll=.4,chest=-.30,sway=.5))]
bpy.ops.wm.open_mainfile(filepath=str(p/'export/mm6_mnk1.blend'))
sc=bpy.context.scene;r=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];B=r.data.bones;names=[b.name for b in B]
def update():bpy.context.view_layer.update()
def setact(a):
 r.animation_data_create();r.animation_data.action=a
 if a is not None and len(a.slots):r.animation_data.action_slot=a.slots[0]
def capture():return {n:(r.pose.bones[n].rotation_quaternion.copy(),r.pose.bones[n].location.copy(),r.pose.bones[n].scale.copy()) for n in names}
def apply(pose):
 for n,(q,l,sc_) in pose.items():pb=r.pose.bones[n];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q;pb.location=l;pb.scale=sc_
 update()
def setworld(n,rot,head=None):
 pb=r.pose.bones[n];m=rot.to_matrix().to_4x4() if isinstance(rot,Quaternion) else rot.to_4x4();m.translation=pb.head if head is None else head;pb.matrix=m;update()
def W(n):return r.pose.bones[n].matrix.copy()
setact(bpy.data.actions['Standing']);sc.frame_set(0);BASE=capture();setact(None);apply(BASE)
BASEW={n:W(n) for n in names};P0=W('B_Pelvis');S0=W('B_Spine').to_quaternion();H0=W('B_Head').to_quaternion()
hip0={sd:W(f'B_{sd}_Thigh').translation.copy() for sd in 'LR'};hipmid0=(hip0['L']+hip0['R'])/2
foot0={sd:W(f'B_{sd}_Foot') for sd in 'LR'}
L1={sd:(B[f'B_{sd}_Calf'].head_local-B[f'B_{sd}_Thigh'].head_local).length for sd in 'LR'}
L2={sd:(B[f'B_{sd}_Foot'].head_local-B[f'B_{sd}_Calf'].head_local).length for sd in 'LR'}
LM=float(np.mean([L1[s]+L2[s] for s in 'LR']))
pv=np.zeros(len(body.data.vertices),np.int32);body.data.attributes['piece'].data.foreach_get('value',pv)
BOOT={'L':np.where(pv==8)[0],'R':np.where(pv==7)[0]}
def boot_low():
 ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();Z=np.array([v.co.z for v in me.vertices]);ev.to_mesh_clear()
 return {sd:float(Z[ids].min()) for sd,ids in BOOT.items()},Z
print('MONK leg',LM,'hipmid',tuple(hipmid0),'feet',{s:tuple(foot0[s].translation) for s in 'LR'},flush=True)

def source(fbx):
 before=set(bpy.data.objects);before_a=set(bpy.data.actions)
 bpy.ops.import_scene.fbx(filepath=str(fbx))
 arm=next(o for o in set(bpy.data.objects)-before if o.type=='ARMATURE')
 bn=lambda s:next(b.name for b in arm.data.bones if b.name.endswith(s))
 J={k:bn(k) for k in ['Hips','LeftUpLeg','LeftLeg','LeftFoot','LeftToeBase','RightUpLeg','RightLeg','RightFoot','RightToeBase']}
 act=arm.animation_data.action;f0,f1=map(int,act.frame_range);rows=[]
 for f in range(f0,f1):
  sc.frame_set(f);rows.append({k:np.array(arm.matrix_world@arm.pose.bones[v].head,dtype=float) for k,v in J.items()})
 fps=sc.render.fps/sc.render.fps_base
 for o in set(bpy.data.objects)-before:bpy.data.objects.remove(o,do_unlink=True)
 for a in set(bpy.data.actions)-before_a:bpy.data.actions.remove(a)
 sc.render.fps=30;sc.render.fps_base=1
 assert abs(fps-30)<1e-6,fps
 return rows

def smooth_cyclic(x,radius=2):
 k=np.exp(-.5*(np.arange(-radius,radius+1)/max(radius/2,1e-6))**2);k/=k.sum()
 return sum(np.roll(x,-i,axis=0)*w for i,w in zip(range(-radius,radius+1),k))

def ik_leg(sd,target,hip_world,pole):
 th,ca,ft=[f'B_{sd}_{n}' for n in ['Thigh','Calf','Foot']];H=r.pose.bones[th].head.copy()
 d=target-H;D=min(d.length,(L1[sd]+L2[sd])*.9995);e=d.normalized();a=(L1[sd]**2-L2[sd]**2+D*D)/(2*D);b=math.sqrt(max(0,L1[sd]**2-a*a))
 v=(pole-e*pole.dot(e)).normalized();knee=H+e*a+v*b
 for n,ch,goal in [(th,ca,knee),(ca,ft,H+e*D)]:
  pb=r.pose.bones[n];cur=r.pose.bones[ch].head-pb.head;q=cur.rotation_difference(goal-pb.head)@pb.matrix.to_quaternion();setworld(n,q)
 return (target-(H+e*D)).length

def robe_legs(share,pelvis_rot):
 """The leg-driven robe follows virtual legs: each thigh swings `share` of its real swing from the pelvis-carried rest,
 the calf cloth runs straight from that virtual knee to the real ankle (stretched along its axis), the foot cloth stays
 on the real foot. The hem keeps every boot inside while the robe drapes as an A-line instead of tracing the knees."""
 carry=pelvis_rot@P0.to_3x3().inverted()
 for sd in 'LR':
  th,ca,ft=[f'B_{sd}_{n}' for n in ['Thigh','Calf','Foot']]
  real=W(th).to_quaternion();rest=(carry@BASEW[th].to_3x3()).to_quaternion()
  if rest.dot(real)<0:rest.negate()
  tv=rest.slerp(real,share);head=W(th).translation.copy()
  setworld(f'Cloth_{sd}_Thigh',tv,head)
  knee=head+tv.to_matrix()@(BASEW[th].to_3x3().inverted()@(BASEW[ca].translation-BASEW[th].translation))
  ankle=W(ft).translation.copy();calf=W(ca);axis=calf.to_3x3()@Vector((0,1,0))
  q=axis.rotation_difference(ankle-knee)@calf.to_quaternion();length=(ankle-knee).length;restlen=(BASEW[ft].translation-BASEW[ca].translation).length
  m=Matrix.LocRotScale(knee,q,Vector((1,length/restlen,1)));r.pose.bones[f'Cloth_{sd}_Calf'].matrix=m;update()

report={}
for clip,fbx,cfg in CLIPS:
 rows=source(fbx);n=len(rows)
 up=np.array([0,0,1.]);lat=np.mean([x['LeftUpLeg']-x['RightUpLeg'] for x in rows],axis=0);lat[2]=0;lat/=np.linalg.norm(lat);fwd=np.cross(lat,up)
 ls=float(np.mean([np.linalg.norm(rows[0][s+'UpLeg']-rows[0][s+'Leg'])+np.linalg.norm(rows[0][s+'Leg']-rows[0][s+'Foot']) for s in ['Left','Right']]));k=LM/ls
 F=lambda v:np.array([v@fwd,v@lat,v@up])
 hm=np.array([F((x['LeftUpLeg']+x['RightUpLeg'])/2) for x in rows])
 ank={sd:np.array([F(x[side+'Foot']) for x in rows]) for sd,side in [('L','Left'),('R','Right')]}
 toe={sd:np.array([F(x[side+'ToeBase']) for x in rows]) for sd,side in [('L','Left'),('R','Right')]}
 rel={sd:ank[sd]-hm for sd in 'LR'}
 # Source stride: backward speed of the ankle against the hip centre while that ankle is low, times the cycle.
 vel=[];plant={}
 for sd in 'LR':
  z=ank[sd][:,2];low=z<z.min()+.15*np.ptp(z);v=-(np.roll(rel[sd][:,0],-1)-np.roll(rel[sd][:,0],1))/2*30;vel.append(float(np.median(v[low])));plant[sd]=float(z.min())
 src_stride=float(np.mean(vel))*n/30
 # Cadence: resample the source cycle to the output frame count (the game plays gaits by distance, one loop per stride).
 def cyc(a):
  ns=len(a);m=2*cfg['frames'];s_=np.arange(m)*ns/m;i0=np.floor(s_).astype(int)%ns;i1=(i0+1)%ns;w=(s_-np.floor(s_)).reshape((-1,)+(1,)*(a.ndim-1));return a[i0]*(1-w)+a[i1]*w
 hm=cyc(hm);ank={sd:cyc(v) for sd,v in ank.items()};toe={sd:cyc(v) for sd,v in toe.items()};rel={sd:ank[sd]-hm for sd in 'LR'};n=2*cfg['frames']
 T=n/60;KY=cfg['stride']/(k*src_stride)
 # Source floor contact per foot (ankle or ball within 1 cm of its lowest height): those boots are kept on the floor.
 contact={sd:((ank[sd][:,2]-ank[sd][:,2].min())<.01)|((toe[sd][:,2]-toe[sd][:,2].min())<.01) for sd in 'LR'}
 pitch={};
 for sd in 'LR':
  d=toe[sd]-ank[sd];pa=np.arctan2(d[:,2],d[:,0]);z=ank[sd][:,2];low=z<z.min()+.08*np.ptp(z);pitch[sd]=pa-np.median(pa[low])
 lhip=cyc(np.array([F(x['LeftUpLeg']-x['RightUpLeg']) for x in rows]));yaw=np.arctan2(lhip[:,0],lhip[:,1]);roll=np.arctan2(lhip[:,2],np.hypot(lhip[:,0],lhip[:,1]))
 yaw-=yaw.mean();roll-=roll.mean()
 bob=hm[:,2]-hm[:,2].min();bob=smooth_cyclic(bob/max(np.ptp(bob),1e-6),1)*cfg['bob']
 srch=float(np.mean([foot0[s].translation.z for s in 'LR']))+k*(hm[:,2]-np.mean(list(plant.values())))
 print('SOURCE_HIP',clip,'monk-scaled source hip height min/mean/max',round(float(srch.min()),3),round(float(srch.mean()),3),round(float(srch.max()),3),'standing',round(hipmid0.z,3),flush=True)
 print('SOURCE',clip,'frames',n,'leg ratio',round(k,4),'source stride',round(src_stride,4),'monk natural',round(k*src_stride,3),'KY',round(KY,3),'yaw deg',round(math.degrees(np.ptp(yaw)),1),'roll deg',round(math.degrees(np.ptp(roll)),1),flush=True)
 # Targets in monk space (x lateral = +X, forward = -Y, up = +Z).
 def M(v):return Vector((v[1],-v[0],v[2]))
 relmean={sd:rel[sd].mean(0) for sd in 'LR'}
 def frame_targets(i):
  hmid=Vector((hipmid0.x+k*(hm[i,1]-hm[:,1].mean())*cfg['sway'],hipmid0.y-k*(hm[i,0]-hm[:,0].mean())*.5,hipmid0.z*cfg['pel']+bob[i]))
  ankles={}
  for sd in 'LR':
   off=rel[sd][i]-relmean[sd];off=np.array([off[0]*KY,off[1],0.])
   t=hmid+Vector((foot0[sd].translation.x-hipmid0.x,hip0[sd].y-hipmid0.y+FOOT_BACK,0))+M(off)*k;t.z=foot0[sd].translation.z+k*(ank[sd][i,2]-plant[sd])*cfg['lift'];ankles[sd]=t
  return hmid,ankles
 # Pass 1: how far the pelvis must drop where a leg cannot reach.
 drops=np.zeros(n)
 for i in range(n):
  hmid,ankles=frame_targets(i)
  for sd in 'LR':
   h=hmid+(hip0[sd]-hipmid0);d=ankles[sd]-h;Lr=(L1[sd]+L2[sd])*.985;hz=d.x*d.x+d.y*d.y
   if ankles[sd].z<foot0[sd].translation.z+.03 and d.length>Lr and hz<Lr*Lr:drops[i]=max(drops[i],-math.sqrt(Lr*Lr-hz)-d.z)
 print('DROPS',clip,np.round(drops,3).tolist(),flush=True)
 for sd in 'LR':print('FOOT',clip,sd,'fwd',np.round(-(rel[sd][:,0]-relmean[sd][0])*KY*k,3).tolist(),'z',np.round(k*(ank[sd][:,2]-plant[sd]),3).tolist(),flush=True)
 drops=np.maximum(drops,0);dil=np.max([np.roll(drops,s) for s in range(-2,3)],axis=0);drops=np.maximum(smooth_cyclic(dil,2),drops)
 frames=[];lifts=[];misses=[];lows=[]
 for i in range(n):
  apply(BASE);hmid,ankles=frame_targets(i);hmid.z-=float(drops[i])
  R=Matrix.Rotation(-yaw[i]*cfg['yaw'],3,'Z')@Matrix.Rotation(roll[i]*cfg['roll'],3,Vector((0,-1,0)))
  rot=R@P0.to_3x3();head=hmid-R@(hipmid0-P0.translation);setworld('B_Pelvis',rot,head)
  setworld('B_Spine',(Matrix.Rotation(-yaw[i]*cfg['yaw']*cfg['chest'],3,'Z')@Matrix.Rotation(math.radians(cfg['lean']),3,'X')).to_quaternion()@S0)
  setworld('B_Head',W('B_Head').to_quaternion().slerp(H0,.75))
  lift={'L':0.,'R':0.}
  for it in range(4):
   miss=0
   for sd in 'LR':
    t=ankles[sd]+Vector((0,0,lift[sd]));fwd_pole=Vector((.08 if sd=='L' else -.08,-1,0))
    miss=max(miss,ik_leg(sd,t,None,fwd_pole))
    setworld(f'B_{sd}_Foot',Matrix.Rotation(-float(pitch[sd][i])*cfg['pitch'],3,'X')@foot0[sd].to_3x3())
   low,_=boot_low()
   want={sd:(abs(low[sd])>.0005 if contact[sd][i] else low[sd]<-.0005) for sd in 'LR'}
   if not any(want.values()):break
   for sd in 'LR':
    if want[sd]:lift[sd]+=-low[sd]
  robe_legs(cfg['robe_thigh'],rot)
  low,_=boot_low();lows.append(low);lifts.append(max(lift.values()));misses.append(miss);frames.append(capture())
 frames.append(frames[0])
 old=bpy.data.actions.get(clip)
 if old:bpy.data.actions.remove(old)
 act=bpy.data.actions.new(clip);act.use_fake_user=True;setact(act);prev={}
 for i,pose in enumerate(frames):
  for bn_,(q,l,sc_) in pose.items():
   q=q.copy()
   if bn_ in prev and q.dot(prev[bn_])<0:q.negate()
   prev[bn_]=q.copy();pb=r.pose.bones[bn_];pb.rotation_quaternion=q;pb.location=l;pb.scale=sc_
   pb.keyframe_insert('rotation_quaternion',frame=i/2);pb.keyframe_insert('location',frame=i/2);pb.keyframe_insert('scale',frame=i/2)
 act.use_frame_range=True;act.frame_start=0;act.frame_end=n//2
 for layer in act.layers:
  for st in layer.strips:
   for cb in st.channelbags:
    for fc in cb.fcurves:
     for key in fc.keyframe_points:key.interpolation='LINEAR'
 setact(None);apply(BASE)
 lowarr=np.array([[x['L'],x['R']] for x in lows])
 report[clip]={'source':fbx.name,'frames':n,'cycle_s':T,'leg_ratio':k,'source_stride_src_units':src_stride,'stride_m':cfg['stride'],'forward_scale':KY,'authored_speed_m_s':cfg['stride']/T,
  'pelvis_drop_max_m':float(drops.max()),'boot_floor_lift_max_m':float(max(lifts)),'ik_miss_max_m':float(max(misses)),'boot_low_min_m':float(lowarr.min()),'contact_share':{sd:float(contact[sd].mean()) for sd in 'LR'},'both_feet_off_frames':int(((lowarr>.01).all(1)).sum()),'cfg':cfg}
 print('GAIT2',clip,json.dumps(report[clip]),flush=True)

# Cloth-only floor offsets for the new clips (review3_floor.py rule: lowest leg-driven robe vertex 8 mm above the floor).
me=body.data;cloth=[(f'B_{sd}_{part}',f'Cloth_{sd}_{part}') for sd in 'LR' for part in ['Thigh','Calf','Foot']];ids=np.where(pv==1)[0]
Wc=np.zeros((len(me.vertices),6))
for j,(_,name) in enumerate(cloth):
 gi=body.vertex_groups[name].index
 for i in ids:Wc[i,j]=next((g.weight for g in me.vertices[int(i)].groups if g.group==gi),0)
for clip,_,_ in CLIPS:
 act=bpy.data.actions[clip];setact(act);rows=[]
 for f in np.arange(0,float(act.frame_range[1])+.01,.5):
  sc.frame_set(int(f),subframe=float(f%1));_,Z=boot_low();offset=np.zeros(6)
  for _ in range(20):
   deficit=.008-Z-Wc@offset;active=ids[np.sum(Wc[ids]*Wc[ids],axis=1)>1e-5];worst=max(active,key=lambda i:deficit[i])
   if deficit[worst]<=.00001:break
   w=Wc[worst];offset+=w*deficit[worst]/(w@w)
  rows.append((float(f),{name:r.pose.bones[name].location.copy()+r.pose.bones[src].matrix.to_3x3().inverted()@Vector((0,0,offset[j])) for j,(src,name) in enumerate(cloth)},float(offset.max())))
 for f,pose,_ in rows:
  for name,l in pose.items():r.pose.bones[name].location=l;r.pose.bones[name].keyframe_insert('location',frame=f)
 for layer in act.layers:
  for st in layer.strips:
   for cb in st.channelbags:
    for fc in cb.fcurves:
     for key in fc.keyframe_points:key.interpolation='LINEAR'
 report[clip]['cloth_floor_lift_max_m']=max(x[2] for x in rows);print('CLOTH_FLOOR',clip,report[clip]['cloth_floor_lift_max_m'],flush=True)
setact(None);apply(BASE)
for pb in r.pose.bones:pb.matrix_basis.identity()
(p/os.environ.get('G2_REPORT','work/gait2_author.json')).write_text(json.dumps(report,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(p/os.environ.get('G2_OUT','work/gait2.blend')))
