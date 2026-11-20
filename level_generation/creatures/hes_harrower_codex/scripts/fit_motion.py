"""Mocap body plus crescent-aware arm paths; exact grip frame, global elbow-plane solve."""
from pathlib import Path
import sys,json,math
import bpy,numpy as np
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P/'scripts'));import armik
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
bpy.ops.wm.open_mainfile(filepath=str(Path(args[0]).resolve() if args else P/'work/motion_sources.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
sc.render.fps=30
G={s:json.loads((P/f'work/grip_pose_{s}.json').read_text()) for s in 'LR'}
H={}
for sd,sgn in (('L',1),('R',-1)):
 ax=Vector(G[sd]['handle_axis_hand_local']).normalized()
 f=Vector(G[sd]['handle_centre_hand_local']);f=(f-ax*f.dot(ax)).normalized()
 local=Matrix((ax,f,ax.cross(f))).transposed()
 up=Vector((0,0,1));out=Vector((sgn,0,0))
 forward=Vector((0,-1,0))
 H[sd]=Matrix((up,forward,up.cross(forward))).transposed()@local.transposed()
 G[sd]['blade_out_hand_local']=list(H[sd].transposed()@out)
 G[sd]['blade_front_hand_local']=list(H[sd].transposed()@Vector((0,-1,0)))
 (P/f'work/grip_pose_{sd}.json').write_text(json.dumps(G[sd],indent=2)+'\n')
def set_action(a):
 rig.animation_data_create();rig.animation_data.action=a
 if a and len(a.slots):rig.animation_data.action_slot=a.slots[0]
def snap():return {b.name:b.matrix_basis.copy() for b in rig.pose.bones}
def restore(s):
 set_action(None)
 for n,m in s.items():rig.pose.bones[n].matrix_basis=m
 bpy.context.view_layer.update()
set_action(bpy.data.actions['Standing']);sc.frame_set(0);ST=snap()
CH0=rig.data.bones['B_Spine2'].matrix_local.to_3x3().normalized()
PELV=rig.pose.bones['B_Pelvis'].location.copy()
lat0=armik.W(rig,'B_L_UpperArm').translation-armik.W(rig,'B_R_UpperArm').translation;lat0.z=0;lat0.normalize();up0=Vector((0,0,1));ATTACK_FRAME=Matrix((lat0,up0.cross(lat0),up0)).transposed()
ATTACK_ANCHOR=(armik.W(rig,'B_L_UpperArm').translation+armik.W(rig,'B_R_UpperArm').translation)*.5
BLADE_LOCAL={}
for sd in 'LR':
 obj=bpy.data.objects.get('Vreth_Blade_'+sd)
 inv=rig.data.bones[f'B_{sd}_Hand'].matrix_local.inverted()
 if obj:BLADE_LOCAL[sd]=np.array([list(inv@v.co) for v in obj.data.vertices])
BONES=list(rig.pose.bones.keys());LEG=[n for n in BONES if any(x in n for x in ('Thigh','Calf','Foot','Toe'))]
ROLES=tuple(args[2:]) if len(args)>2 else ('Standing','Walking','Running','Attack','Attack2','Hit','Death','Dead','Fidget','Roar')
report={}
for role in ROLES:
 src=bpy.data.actions['Attack3' if role=='Attack2' else role];n=int(round(src.frame_range[1]));frames=[]
 for f in range(n+1):
  set_action(src);sc.frame_set(f);S=snap();u=f/max(n,1)
  # The one-shot body comes from the selected professional clip and joins the guard at both ends.
  if role in ('Attack','Attack2','Hit','Fidget','Roar'):
   edge=min(1.,u/.18,(1-u)/.18);edge=max(0.,edge);edge=edge*edge*(3-2*edge)
   for bn in BONES:
    if bn in LEG or bn=='B_Pelvis':S[bn]=ST[bn].copy()
    else:
     weight=edge*(.20 if role.startswith('Attack') else .35 if role=='Fidget' else .60 if role=='Roar' else 1.)
     a=ST[bn].to_quaternion();b=S[bn].to_quaternion();q=a.slerp(b,weight)
     S[bn]=q.to_matrix().to_4x4();S[bn].translation=ST[bn].translation.lerp(S[bn].translation,weight)
  # A stable reference arm plane prevents mocap elbow rolls from flipping the IK branch.
  for sd in 'LR':
   for part in ('UpperArm','Forearm','Hand'):S[f'B_{sd}_{part}']=ST[f'B_{sd}_{part}'].copy()
  restore(S)
  ch=armik.W(rig,'B_Spine2');pel=armik.W(rig,'B_Pelvis').translation
  lateral=armik.W(rig,'B_L_UpperArm').translation-armik.W(rig,'B_R_UpperArm').translation
  up=(armik.W(rig,'B_Neck').translation-pel).normalized() if role in ('Death','Dead') else Vector((0,0,1))
  lateral=(lateral-up*lateral.dot(up)).normalized();C=Matrix((lateral,up.cross(lateral),up)).transposed()
  anchor=(armik.W(rig,'B_L_UpperArm').translation+armik.W(rig,'B_R_UpperArm').translation)*.5
  if role.startswith('Attack'):C=ATTACK_FRAME.copy();anchor=ATTACK_ANCHOR.copy()
  entry={'snap':snap(),'hands':{}}
  for sd,sgn in (('L',1),('R',-1)):
   # Carry inherits the source chest; small source wrist motion keeps the held silhouette alive.
   local=Vector((sgn*.53,-.30,-.14));yaw=0.;pitch=-sgn*math.radians(15)
   if role.startswith('Attack'):
    phase=max(0.,u-(.16 if role=='Attack' and sd=='R' else 0.))
    def path(keys,values):
     i=min(len(keys)-2,max(0,int(np.searchsorted(keys,phase,side='right'))-1))
     t=max(0.,min(1.,(phase-keys[i])/(keys[i+1]-keys[i])));t=t*t*(3-2*t)
     return values[i]*(1-t)+values[i+1]*t
    turn=path([0,.12,.26,.54,.84,1],[0,0,1,1,0,0])
    thrust=path([0,.12,.26,.43,.54,.84,1],[0,.03,.08,-.17,-.17,0,0])
    stroke=path([0,.12,.26,.43,.54,.84,1],[0,0,0,1,1,0,0])
    local+=Vector((-sgn*.075*turn,thrust,.025*turn)) if sd=='L' else Vector((sgn*(-.09*turn+.13*stroke),.02*turn-.06*stroke,.025*turn))
    yaw=-sgn*math.radians(80)*turn
    pitch+=0.
   elif role=='Roar':
    pulse=math.sin(math.pi*u)**2;local+=Vector((sgn*.025*pulse,.02*pulse,.08*pulse))
   elif role in ('Walking','Running','Standing'):
    native=ch.inverted()@armik.W(rig,f'B_{sd}_Hand').translation
    # Tiny inherited carry sway, bounded to avoid the native arm crossing the blade over the trunk.
    local+=Vector((0,float(np.clip(native.y,-1,1))*.015,float(np.clip(native.z,-1,1))*.015))
   wrist=anchor+C@local
   R=C@Matrix.Rotation(yaw,3,'Z')@Matrix.Rotation(pitch,3,'Y')@H[sd]
   if sd in BLADE_LOCAL:
    lowest=float((BLADE_LOCAL[sd]@np.array(R).T)[:,2].min())+wrist.z
    wrist.z+=max(0.,.025-lowest)
   direction=R@Vector(G[sd]['handle_axis_hand_local'])
   entry['hands'][sd]={'wrist':wrist,'dir':direction,'fixed_hand':R,'elbow_out':(anchor,C.col[0],sgn,.22 if role.startswith('Attack') else .25)}
  frames.append(entry)
 paths={}
 for sd in 'LR':
  frs=[{'snap':fr['snap'],**fr['hands'][sd]} for fr in frames]
  paths[sd]=armik.arm_dp(rig,sd,frs,G[sd]['handle_axis_hand_local'],phis=range(-180,181,10),psis=range(-60,61,10),k_phi=.25,k_dphi=2.0,twist_neutral=0.)
 poses=[];metrics={sd:{'swing':0.,'twist':0.} for sd in 'LR'}
 for f,fr in enumerate(frames):
  restore(fr['snap'])
  for sd in 'LR':
   current=snap();h=fr['hands'][sd];q=paths[sd][f]
   armik.apply_arm(rig,sd,current,h['wrist'],G[sd]['handle_axis_hand_local'],h['dir'],q['phi'],0)
   hand_rot=Quaternion(h['dir'],math.radians(q['psi'])).to_matrix()@h['fixed_hand']
   armik.set_world(rig,f'B_{sd}_Hand',armik.rot_world(armik.W(rig,f'B_{sd}_Hand'),hand_rot))
   sw,tw=armik.wrist_cost(rig,sd,hand_rot);metrics[sd]['swing']=max(metrics[sd]['swing'],sw);metrics[sd]['twist']=max(metrics[sd]['twist'],abs(tw))
   for bn,quat in G[sd]['finger_local'].items():rig.pose.bones[bn].rotation_mode='QUATERNION';rig.pose.bones[bn].rotation_quaternion=Quaternion(quat)
   # Bake the existing helper bones only; retain the shared skin weights and skeleton unchanged.
   fb=rig.data.bones[f'B_{sd}_Forearm'];hb=rig.data.bones[f'B_{sd}_Hand'];axis=(fb.matrix_local.inverted()@hb.head_local).normalized()
   rel=(rig.pose.bones[fb.name].matrix.inverted()@rig.pose.bones[hb.name].matrix).to_quaternion();rest=(fb.matrix_local.inverted()@hb.matrix_local).to_quaternion()
   dq=rel@rest.inverted();_,twist=armik.split_swing_twist(dq,axis)
   rig.pose.bones[f'B_{sd}_ForearmTwist'].rotation_quaternion=Quaternion(axis,.6*twist)
   ub=rig.data.bones[f'B_{sd}_UpperArm'];axis=(ub.matrix_local.inverted()@fb.head_local).normalized();_,twist=armik.split_swing_twist(rig.pose.bones[ub.name].matrix_basis.to_quaternion(),axis)
   rig.pose.bones[f'B_{sd}_UpperArmTwist'].rotation_quaternion=Quaternion(axis,-.5*twist)
  bpy.context.view_layer.update();poses.append(snap())
 if role in ('Standing','Walking','Running'):poses[-1]=poses[0]
 old=bpy.data.actions.get('Harrower_'+role)
 if old:bpy.data.actions.remove(old)
 a=bpy.data.actions.new('Harrower_'+role);a.use_fake_user=True;set_action(a);prev={}
 for f,S in enumerate(poses):
  for bn,m in S.items():
   pb=rig.pose.bones[bn];pb.rotation_mode='QUATERNION';q=m.to_quaternion()
   if bn in prev and q.dot(prev[bn])<0:q=-q
   prev[bn]=q;pb.rotation_quaternion=q;pb.location=m.translation;pb.scale=m.to_scale()
   pb.keyframe_insert('rotation_quaternion',frame=f);pb.keyframe_insert('location',frame=f);pb.keyframe_insert('scale',frame=f)
 a.use_frame_range=True;a.frame_start=0;a.frame_end=n
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
 report[role]={'duration':n/30,'wrist':metrics,'elbow_phi':{sd:[v['phi'] for v in paths[sd]] for sd in 'LR'},'hand_roll_psi':{sd:[v['psi'] for v in paths[sd]] for sd in 'LR'}}
 print('FIT',role,json.dumps(metrics),flush=True)
 bpy.context.preferences.filepaths.save_version=0
 bpy.ops.wm.save_as_mainfile(filepath=str(Path(args[1]).resolve() if args else P/'work/armed.blend'))
previous=json.loads((P/'review/arm_fit.json').read_text()) if (P/'review/arm_fit.json').exists() else {}
previous.update(report)
(P/'review/arm_fit.json').write_text(json.dumps(previous,indent=2)+'\n')
set_action(None)
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=str(Path(args[1]).resolve() if args else P/'work/armed.blend'))
