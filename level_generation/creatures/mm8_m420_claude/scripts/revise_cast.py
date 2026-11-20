"""Fit the accepted Sorcerer cast to the Pirate Mage; replace only Attack and Cast."""
import bpy, sys, json, math, hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector, Matrix, Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import armik
BASE=P/'review/cast_revision/baseline/work/master_settled.blend'
SOURCE=P.parent/'mm6_sor1_codex/work/production_master.blend'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()=='c1311b1239f02b9949bb1f2ab23843ec0cb51a84af441bdbcb8c1829467b0906', 'Sorcerer reference changed; review it before rebuilding'
SG=json.loads((SOURCE.parents[1]/'work/grip_pose.json').read_text())
# Read the accepted reference, preserving its actual world motion and source rate.
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));sr=bpy.data.objects['Rig'];sc=bpy.context.scene
source_names=[n for n in sr.pose.bones.keys() if n.startswith('B_')]
sa=bpy.data.actions['Cast'];sr.animation_data.action=sa;sr.animation_data.action_slot=sa.slots[0]
source=[]
for f in range(247):
 sc.frame_set(f);source.append({n:(sr.matrix_world@sr.pose.bones[n].matrix).copy() for n in source_names})
def source_pose(t):
 f=min(246,max(0,t*120));i=min(245,int(f));u=f-i;out={}
 for n in source_names:
  a,b=source[i][n],source[i+1][n];m=a.to_quaternion().slerp(b.to_quaternion(),u).to_matrix().to_4x4();m.translation=a.translation.lerp(b.translation,u);out[n]=m
 return out
bpy.ops.wm.open_mainfile(filepath=str(BASE));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];staff=bpy.data.objects['StaffMesh'];sc=bpy.context.scene;sc.render.fps=30
names=list(rig.pose.bones.keys())
rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=rig.animation_data.action.slots[0];sc.frame_set(0)
stand={n:rig.pose.bones[n].matrix_basis.copy() for n in names};world={n:armik.W(rig,n).copy() for n in names}
scale=(world['B_Head'].translation.z-world['B_Pelvis'].translation.z)/(source[0]['B_Head'].translation.z-source[0]['B_Pelvis'].translation.z)
def select(a):
 rig.animation_data.action=a
 if a and a.slots:rig.animation_data.action_slot=a.slots[0]
def reset():
 select(None)
 for n,m in stand.items():rig.pose.bones[n].matrix_basis=m
 bpy.context.view_layer.update()
def ease(t):
 t=max(0,min(1,t));return t*t*(3-2*t)
def set_rotation(n,q):
 m=armik.W(rig,n);m=q.to_matrix().to_4x4();m.translation=armik.W(rig,n).translation;armik.set_world(rig,n,m)
def leg(side,target):
 up,lo,foot=[f'B_{side}_{x}' for x in ['Thigh','Calf','Foot']]
 A=armik.W(rig,up).translation;E0=armik.W(rig,lo).translation;W0=armik.W(rig,foot).translation
 l1=(E0-A).length;l2=(W0-E0).length;d=target.translation-A;dist=min(d.length,(l1+l2)*.999);u=d.normalized()
 v=Vector((0,-1,0));v=(v-u*v.dot(u)).normalized();q=(l1*l1+dist*dist-l2*l2)/(2*dist)
 E=A+q*u+math.sqrt(max(0,l1*l1-q*q))*v;W=A+u*dist
 for n,c,T in [(up,lo,E),(lo,foot,W)]:
  m=armik.W(rig,n);old=armik.W(rig,c).translation-m.translation;R=old.normalized().rotation_difference((T-m.translation).normalized()).to_matrix()@m.to_3x3();armik.set_world(rig,n,armik.rot_world(m,R))
 m=target.copy();m.translation=W;armik.set_world(rig,foot,m)
 return (W-target.translation).length
# Quantify the old shoulder/arm motion before replacing it.
def trace(action):
 select(action);out={n:[] for n in ['B_Spine2','B_R_Clavicle','B_R_UpperArm','B_R_Forearm','B_R_Hand','B_R_UpperArmTwist','B_R_ForearmTwist','B_L_UpperArm','B_L_Forearm']}
 times=np.arange(0,float(action.frame_range[1])/30+.00001,1/48)
 for t in times:
  f=t*30;sc.frame_set(int(f),subframe=float(f%1))
  for n in out:out[n].append(armik.W(rig,n).to_quaternion())
 rows={}
 for n,qs in out.items():
  d=[math.degrees(2*math.acos(min(1,abs(a.dot(b))))) for a,b in zip(qs,qs[1:])];i=int(np.argmax(d));rows[n]={'max_step_deg_per_48fps':d[i],'at_seconds':float(times[i]),'frames_62_75_max_step':max(d[62:75],default=0)}
 return rows
before=trace(bpy.data.actions['Attack'])
for n in ['Attack','Cast']:bpy.data.actions.remove(bpy.data.actions[n])
a=bpy.data.actions.new('Attack');a.use_fake_user=True;a.use_frame_range=True;a.frame_start=0;a.frame_end=77
prevq={};prevtwist={};rows=[];frames=[];G=json.loads((P/'work/grip_pose.json').read_text());axis=Vector(G['handle_axis_hand_local'])
for k in range(309):
 t=k/120;u=min(1,t/.8125);st=.2125*u**3+.0875*u**2 if t<.8125 else min(2.05,t-.5125);src=source_pose(st);active=ease(st/.25)*ease((2.05-st)/.3);reset()
 # Preserve the accepted small torso/gaze gesture around this creature's upright stance.
 for n in ['B_Pelvis','B_Spine','B_Spine1','B_Spine2','B_Neck','B_Head','B_R_Clavicle','B_L_Clavicle']:
  dq=src[n].to_quaternion()@source[0][n].to_quaternion().inverted();set_rotation(n,dq@world[n].to_quaternion())
 delta=(src['B_Pelvis'].translation-source[0]['B_Pelvis'].translation)*scale
 m=armik.W(rig,'B_Pelvis');m.translation=world['B_Pelvis'].translation+delta;armik.set_world(rig,'B_Pelvis',m)
 legmiss={}
 for side in 'RL':
  n=f'B_{side}_Foot';m=world[n].copy();m.translation+=(src[n].translation-source[0][n].translation)*scale;legmiss[side]=leg(side,m)
 # The source's different hand frame cannot be copied onto our fitted fist.
 # Preserve its staff axis and wrist arc, then solve one continuous arm/roll path.
 ua,fa,hd=['B_L_'+x for x in ['UpperArm','Forearm','Hand']]
 target=world[hd].translation+(src[hd].translation-source[0][hd].translation)*scale
 S=armik.W(rig,ua).translation;length=(rig.data.bones[fa].head_local-rig.data.bones[ua].head_local).length+(rig.data.bones[hd].head_local-rig.data.bones[fa].head_local).length
 d=target-S
 if d.length>length*.985:target=S+d.normalized()*length*.985
 pole0=(world[fa].translation-world[ua].translation).normalized();pole=pole0.lerp((src[fa].translation-src[ua].translation).normalized(),active).normalized()
 dq=src[hd].to_quaternion()@source[0][hd].to_quaternion().inverted();H=(dq@world[hd].to_quaternion()).to_matrix()
 reach=armik.solve(rig,'L',target,pole=S+pole,hand_rot=H);sw,tw=armik.wrist_cost(rig,'L',H)
 rtarget=world['B_R_Hand'].translation+(src['B_R_Hand'].translation-source[0]['B_R_Hand'].translation)*scale
 ownlen=(world['B_R_Forearm'].translation-world['B_R_UpperArm'].translation).length+(world['B_R_Hand'].translation-world['B_R_Forearm'].translation).length
 srclen=(source[0]['B_R_Forearm'].translation-source[0]['B_R_UpperArm'].translation).length+(source[0]['B_R_Hand'].translation-source[0]['B_R_Forearm'].translation).length
 # His idle grip is higher than the Sorcerer's: transfer the arm relative to its shoulder.
 fitted=armik.W(rig,'B_R_UpperArm').translation+(src['B_R_Hand'].translation-src['B_R_UpperArm'].translation)*(ownlen/srclen)
 rtarget=rtarget.lerp(fitted,active)
 saxis=Vector(SG['handle_axis_hand_local']);d0=(source[0]['B_R_Hand'].to_3x3()@saxis).normalized();dn=(src['B_R_Hand'].to_3x3()@saxis).normalized()
 direction=d0.rotation_difference(dn)@(world['B_R_Hand'].to_3x3()@axis)
 rua,rfa,rhd=['B_R_'+x for x in ['UpperArm','Forearm','Hand']]
 rpole0=(world[rfa].translation-world[rua].translation).normalized();rpole=rpole0.lerp((src[rfa].translation-src[rua].translation).normalized(),active).normalized()
 armik.solve(rig,'R',rtarget,pole=armik.W(rig,rua).translation+rpole,hand_rot=world[rhd].to_3x3())
 frames.append({'snap':{n:rig.pose.bones[n].matrix_basis.copy() for n in names},'wrist':rtarget,'dir':direction,'active':active,'t':t,'source_t':st,'low_elbow':True,'left':{'reach':reach,'swing':sw,'twist':tw},'legmiss':legmiss})
print('FITTING',len(frames),'arm poses',flush=True)
# Choose on the 30 Hz grid; interpolate the continuous controls onto the 120 Hz bake.
coarse=list(range(0,len(frames),4));choices=armik.arm_dp(rig,'R',[frames[i] for i in coarse],axis,phis=range(-30,31,10),k_twist=1.2,k_dphi=2.5,k_dpsi=3.0)
ph=np.interp(np.arange(len(frames)),coarse,[x['phi'] for x in choices]);ps=np.interp(np.arange(len(frames)),coarse,np.degrees(np.unwrap(np.radians([x['psi'] for x in choices]))))
kernel=np.exp(-.5*(np.arange(-6,7)/2.5)**2);kernel/=kernel.sum()
ph=np.convolve(np.pad(ph,6,mode='edge'),kernel,'valid');ps=np.convolve(np.pad(ps,6,mode='edge'),kernel,'valid')
for k,fr in enumerate(frames):
 select(None)
 armik.apply_arm(rig,'R',fr['snap'],fr['wrist'],axis,fr['dir'],float(ph[k]),float(ps[k]))
 for n in ['B_R_UpperArm','B_R_Forearm','B_R_Hand']:
  pb=rig.pose.bones[n];pb.rotation_quaternion=fr['snap'][n].to_quaternion().slerp(pb.rotation_quaternion,fr['active'])
 bpy.context.view_layer.update();H=armik.W(rig,'B_R_Hand').to_3x3();sw,tw=armik.wrist_cost(rig,'R',H)
 armrows={'R':{'reach':float((armik.W(rig,'B_R_Hand').translation-armik.W(rig,'B_R_UpperArm').translation).length/((rig.data.bones['B_R_Forearm'].head_local-rig.data.bones['B_R_UpperArm'].head_local).length+(rig.data.bones['B_R_Hand'].head_local-rig.data.bones['B_R_Forearm'].head_local).length)),'swing':sw,'twist':tw},'L':fr['left']}
 t,st,legmiss=fr['t'],fr['source_t'],fr['legmiss']
 # Twist helpers follow continuous angles; a principal-angle wrap must not flip a sleeve.
 for side in 'RL':
  for kind,child,factor in [('Forearm','Hand',.6),('UpperArm','Forearm',-.5)]:
   bn=f'B_{side}_{kind}';cn=f'B_{side}_{child}';b=rig.data.bones[bn];c=rig.data.bones[cn];ax=(b.matrix_local.inverted()@c.head_local).normalized()
   if kind=='Forearm':q=(rig.pose.bones[bn].matrix.inverted()@rig.pose.bones[cn].matrix).to_quaternion()@(b.matrix_local.inverted()@c.matrix_local).to_quaternion().inverted()
   else:q=rig.pose.bones[bn].matrix_basis.to_quaternion()
   _,tw=armik.split_swing_twist(q,ax);key=bn+'Twist'
   if key in prevtwist:tw+=round((prevtwist[key]-tw)/(2*math.pi))*2*math.pi
   prevtwist[key]=tw;rig.pose.bones[key].rotation_quaternion=Quaternion(ax,factor*tw)
 edge=ease(t/.20)*ease((77/30-t)/.25)
 pose={n:(stand[n].to_quaternion().slerp(rig.pose.bones[n].rotation_quaternion,edge),stand[n].translation.lerp(rig.pose.bones[n].location,edge)) for n in names};select(a)
 for n,(q,l) in pose.items():
  if n in prevq and q.dot(prevq[n])<0:q=-q
  prevq[n]=q.copy();pb=rig.pose.bones[n];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=k/4)
  if n=='B_Pelvis':pb.location=l;pb.keyframe_insert('location',frame=k/4)
 rows.append({'t':t,'source_t':st,'arms':armrows,'leg_reach_miss_mm':{s:v*1000 for s,v in legmiss.items()}})
for layer in a.layers:
 for strip in layer.strips:
  for bag in strip.channelbags:
   for fc in bag.fcurves:
    for key in fc.keyframe_points:key.interpolation='LINEAR'
# The right support is an actual peg, so level the evaluated shoe/peg surface, not the source ankle.
parts=np.array([x.value for x in body.data.attributes['piece'].data]);rest=np.array([v.co[:] for v in body.data.vertices]);support=np.isin(parts,[6,12])&(rest[:,2]<.10);inv=rig.data.bones['B_Pelvis'].matrix_local.to_3x3().inverted();ground=[];select(a)
for k in range(309):
 f=k/4;sc.frame_set(int(f),subframe=f%1);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();co=np.array([(body.matrix_world@v.co)[:] for v in me.vertices]);ev.to_mesh_clear();dz=.002-float(co[support,2].min());ground.append(rig.pose.bones['B_Pelvis'].location.copy()+inv@Vector((0,0,dz)))
for k,loc in enumerate(ground):
 rig.pose.bones['B_Pelvis'].location=loc;rig.pose.bones['B_Pelvis'].keyframe_insert('location',frame=k/4)
for layer in a.layers:
 for strip in layer.strips:
  for bag in strip.channelbags:
   for fc in bag.fcurves:
    for key in fc.keyframe_points:key.interpolation='LINEAR'
for f in [0,77]:
 select(a);sc.frame_set(f)
 errors=[np.max(np.abs(np.array(armik.W(rig,n))-np.array(world[n]))) for n in names]
 assert max(errors)<1e-5,('Cast endpoint differs from idle',f,max(errors))
c=a.copy();c.name='Cast';c.use_fake_user=True
after=trace(a)
report={'reference':str(SOURCE),'reference_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'source_clip':'Cast','source_timing_s':2.05,'duration_s':77/30,'release_s':1.25,'source_release_s':.7375,'adaptation':'Sorcerer world-space gesture fitted to Pirate Mage standing pose and limb lengths, right peg support, original grip; preparation extended by .5125 s; release/follow-through retain source rate.','before':before,'after':after,'arm_choices':choices,'samples':rows}
(P/'review/cast_revision/motion.json').write_text(json.dumps(report,indent=2)+'\n')
print('CAST_REVISION',json.dumps({'before':before,'after':after,'arm_max':{s:{k:max(r['arms'][s][k] for r in rows) for k in ['reach','swing','twist']} for s in 'RL'}}),flush=True)
select(None)
for pb in rig.pose.bones:pb.matrix_basis.identity()
assert max(r['arms'][s]['reach'] for r in rows for s in 'RL')<1.01
assert max(r['arms'][s]['swing'] for r in rows for s in 'RL')<60
assert max(abs(r['arms']['R']['twist']) for r in rows)<95

bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/master_settled.blend'))
