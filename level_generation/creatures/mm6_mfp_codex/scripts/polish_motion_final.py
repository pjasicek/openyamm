"""Remove retarget-only rotation spikes; keep source motion and aim relaxed palms inward."""
import bpy,sys,math,json,runpy,os,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_textured.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
ROLES=['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget']
for a in list(bpy.data.actions):
 if a.name not in ROLES:bpy.data.actions.remove(a)
for a in bpy.data.actions:a.use_fake_user=True
names=[f'B_{s}_{n}'for s in 'LR'for n in ['Clavicle','UpperArm','Forearm','Hand']]
rest={n:b.matrix_local.copy()for n,b in rig.data.bones.items()};palm={}
for s in 'LR':
 W=rig.data.bones[f'B_{s}_Hand'].head_local;kn=[rig.data.bones[f'B_{s}_Finger{i}'].head_local for i in range(1,5)];K=sum(kn,Vector())/4;long=(K-W).normalized();N=(kn[0]-kn[-1]).normalized().cross(long).normalized();tips=sum((rig.data.bones[f'B_{s}_Finger{i}2'].head_local for i in range(1,5)),Vector())/4
 if (tips-K).dot(N)<0:N=-N
 inv=rest[f'B_{s}_Hand'].inverted();palm[s]=(inv.to_3x3()@N,inv.to_3x3()@long,inv@((W+K)*.5))
for role in [x for x in ROLES if x!='Dead']:
 a=bpy.data.actions[role];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];nf=int(a.frame_range[1]);raw=[]
 for f in range(nf+1):
  sc.frame_set(f);raw.append({n:rig.pose.bones[n].rotation_quaternion.copy()for n in names})
 sigma={'Attack':1.3,'Hit':1.2,'Death':3.0}.get(role,0)
 smooth=[]
 for f in range(nf+1):
  row={}
  for n in names:
   if sigma:
    vec=np.zeros(4);center=raw[f][n]
    for j in range(max(0,f-5),min(nf,f+5)+1):
     other=raw[j][n].copy()
     if other.dot(center)<0:other=-other
     vec+=np.array(other)*math.exp(-.5*((j-f)/sigma)**2)
    row[n]=Quaternion(vec/np.linalg.norm(vec))
   else:row[n]=raw[f][n]
  if role=='Death'and f<7:
   t=f/7;t=t*t*(3-2*t)
   for n in names:row[n]=raw[0][n].slerp(row[n],t)
  if role=='Attack'and f>21:
   t=(f-21)/(nf-21);t=t*t*(3-2*t)
   for n in names:
    if n.startswith('B_R_'):row[n]=smooth[21][n].slerp(raw[nf][n],t)
  smooth.append(row)
 # Replace existing rotation channels only; the source root, feet and garment remain authoritative.
 for layer in a.layers:
  for st in layer.strips:
   for bag in st.channelbags:
    for fc in list(bag.fcurves):
     if any(fc.data_path==f'pose.bones["{n}"].rotation_quaternion'for n in names):bag.fcurves.remove(fc)
 prev={}
 for f,row in enumerate(smooth):
  rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];sc.frame_set(f);rig.animation_data.action=None
  for n,q in row.items():rig.pose.bones[n].rotation_quaternion=q
  bpy.context.view_layer.update()
  if role in ['Standing','Fidget','Walking','Running','Attack']:
   for s in ('L',)if role=='Attack'else'LR':
    n=f'B_{s}_Hand';pb=rig.pose.bones[n];M=pb.matrix.copy();N=(M.to_3x3()@palm[s][0]).normalized();axis=(M.to_3x3()@palm[s][1]).normalized();origin=M@palm[s][2];goal=rig.pose.bones[f'B_{s}_Thigh'].head-origin;goal.z=0;goal=(goal-axis*goal.dot(axis)).normalized();N=(N-axis*N.dot(axis)).normalized();angle=math.atan2(axis.dot(N.cross(goal)),N.dot(goal));R=Quaternion(axis,angle).to_matrix();rot=R.to_4x4()@M;rot.translation=M.translation;pb.matrix=rot;bpy.context.view_layer.update()
  if role=='Attack':
   pb=rig.pose.bones['B_R_UpperArm'];M=pb.matrix.copy();R=Quaternion(Vector((0,1,0)),math.radians(5)*math.sin(math.pi*f/nf)**2).to_matrix();m=R.to_4x4()@M;m.translation=M.translation;pb.matrix=m;bpy.context.view_layer.update()
  result={n:rig.pose.bones[n].rotation_quaternion.copy()for n in names};rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
  for n,q in result.items():
   if n in prev and q.dot(prev[n])<0:q=-q
   prev[n]=q;pb=rig.pose.bones[n];pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f)
 rig.animation_data.action=None
code=(P/'scripts/twist_bones.py').read_text();FA=.6;UA=.5;exec(code[code.index('def twist_about'):code.index('for act in [a for a in bpy.data.actions')])
for a in bpy.data.actions:
 if a.name!='Dead':bake_twist(a)
# Sample the real skin for the final floor envelope; translating the root preserves limb/cloth clearance.
root=rig.pose.bones['B_Pelvis'];inv=rig.data.bones[root.name].matrix_local.to_3x3().inverted();floor={}
for a in bpy.data.actions:
 if a.name=='Dead':continue
 rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];nf=int(a.frame_range[1]);loc=[];corr=np.zeros(nf+1)
 for f in range(nf+1):sc.frame_set(f);loc.append(root.location.copy())
 for f in np.linspace(0,nf,math.ceil(nf*48/30)+1):
  sc.frame_set(int(f),subframe=float(f%1));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();dz=max(0,.001-min(v.co.z for v in me.vertices));ev.to_mesh_clear()
  for j in {int(f),min(nf,math.ceil(f))}:corr[j]=max(corr[j],dz)
 for f,l in enumerate(loc):root.location=l+inv@Vector((0,0,float(corr[f])));root.keyframe_insert('location',frame=f)
 floor[a.name]=float(corr.max())
a=bpy.data.actions['Death'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];sc.frame_set(int(a.frame_range[1]));held={pb.name:(pb.rotation_quaternion.copy(),pb.location.copy(),pb.scale.copy())for pb in rig.pose.bones};rig.animation_data.action=None;bpy.data.actions.remove(bpy.data.actions['Dead']);a=bpy.data.actions.new('Dead');a.use_fake_user=True;a.use_frame_range=True;a.frame_start=0;a.frame_end=30;rig.animation_data.action=a
for f in [0,30]:
 for n,(q,l,s)in held.items():pb=rig.pose.bones[n];pb.rotation_quaternion=q;pb.location=l;pb.scale=s;pb.keyframe_insert('rotation_quaternion',frame=f);pb.keyframe_insert('location',frame=f);pb.keyframe_insert('scale',frame=f)
for a in bpy.data.actions:
 for l in a.layers:
  for st in l.strips:
   for bag in st.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
# Preserve the library's validated swing path; slow its fast return after the cutting stroke.
grid=np.linspace(0,1,4001);ease=lambda x:np.clip(x,0,1)**2*(3-2*np.clip(x,0,1));rate=1+5*ease((grid-.43)/.015)*ease((.56-grid)/.020);warped=np.r_[0,np.cumsum((rate[:-1]+rate[1:])*.5*np.diff(grid))];a=bpy.data.actions['Attack']
for layer in a.layers:
 for strip in layer.strips:
  for bag in strip.channelbags:
   for fc in bag.fcurves:
    for k in fc.keyframe_points:
     for co in [k.co,k.handle_left,k.handle_right]:co.x=float(np.interp(co.x/30,grid,warped)*30)
a.frame_end=float(warped[-1]*30)
death=bpy.data.actions['Death'];duration=death.frame_range[1]/30;dgrid=np.linspace(0,duration,8001);drate=1+1.25*ease((.38-dgrid)/.1);dwarped=np.r_[0,np.cumsum((drate[:-1]+drate[1:])*.5*np.diff(dgrid))]
for layer in death.layers:
 for strip in layer.strips:
  for bag in strip.channelbags:
   for fc in bag.fcurves:
    for k in fc.keyframe_points:
     for co in [k.co,k.handle_left,k.handle_right]:co.x=float(np.interp(co.x/30,dgrid,dwarped)*30)
death.frame_end=float(dwarped[-1]*30)
(P/'review/death_retime.json').write_text(json.dumps({'source':'Mixamo Falling Forward Death','duration_s':float(dwarped[-1]),'anticipation_interval_s':[0,.38],'maximum_time_stretch':2.25},indent=2))
(P/'review/attack_retime.json').write_text(json.dumps({'source':'DaggerAttackR3','duration_s':float(warped[-1]),'slow_source_interval_s':[.43,.56],'maximum_time_stretch':6,'upper_arm_abduction_degrees':5},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_polished.blend'));(P/'review/motion_polish_floor.json').write_text(json.dumps(floor,indent=2))
os.environ.update(MOTION_BLEND=str(P/'work/rig_polished.blend'),GATE_BLEND=str(P/'work/rig_polished.blend'),GATE_REPORT=str(P/'review/polished_gates.json'),GATE_RENDER='0',EXTRA_BLEND=str(P/'work/rig_polished.blend'),EXTRA_REPORT=str(P/'review/polished_prop.json'))
runpy.run_path(str(P/'scripts/initial_checks.py'),run_name='__main__');runpy.run_path(str(P/'scripts/motion_proof.py'),run_name='__main__');runpy.run_path(str(P/'scripts/extra_metrics.py'),run_name='__main__')
