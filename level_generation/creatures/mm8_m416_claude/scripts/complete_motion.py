"""Finish the selected source clips around the validated two-hand crossbow pilot."""
from pathlib import Path
p=Path(__file__).resolve();src=p.parent/'author_pilot.py';exec(compile(src.read_text().split('frames_by={};')[0],str(src),'exec'))
bpy.ops.wm.open_mainfile(filepath=str(P/'work/pilot.blend'));rig=bpy.data.objects['Rig'];scene=bpy.context.scene;scene.render.fps=30
setact(bpy.data.actions['Standing']);scene.frame_set(0);ST=snap();setact(None)
def write(role,poses):
 old=bpy.data.actions.get(role)
 if old:bpy.data.actions.remove(old)
 a=bpy.data.actions.new(role);a.use_fake_user=True;setact(a);prev={}
 for i,pose in enumerate(poses):
  for n,m in pose.items():
   pb=rig.pose.bones[n];pb.rotation_mode='QUATERNION';pb.matrix_basis=m;q=pb.rotation_quaternion.copy()
   assert abs(q.magnitude-1)<.001 and all(math.isfinite(x) for x in q)
   if n in prev and q.dot(prev[n])<0:q=-q
   prev[n]=q;pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=i)
   if n=='B_Pelvis':pb.keyframe_insert('location',frame=i)
 a.use_frame_range=True;a.frame_start=0;a.frame_end=len(poses)-1;setact(None)
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
reports={}
for role in ['Running','Hit','Fidget']:
 source=raw[role]
 if role=='Hit':source=[blend(ST,x,smooth(i/3)*smooth((len(source)-1-i)/3)) for i,x in enumerate(source)]
 if role=='Fidget':source=[blend(ST,source[0],smooth(i/6)) for i in range(6)]+source+[blend(source[-1],ST,smooth(i/6)) for i in range(1,7)]
 frames=[]
 for i,pose0 in enumerate(source):
  pose=pose0.copy();phase=math.sin(math.pi*i/(len(source)-1))**2 if role=='Fidget' else 0
  if role=='Fidget':pose=blend(ST,pose,.45)
  apply(pose);S=armik.W(rig,'B_R_UpperArm').translation.copy();B=Matrix.Rotation(math.radians(30*(1-.5*phase)),4,'Z')@Matrix.Rotation(math.radians(-30*(1-.5*phase)),4,'Y')@B0@Matrix.Rotation(math.radians(70-35*phase),4,'X');B.translation=S+Vector((-.18,-.25-.04*phase,-.06))
  R=B@rels['R'];left_pose={n:pose[n] for n in names if n.startswith('B_L_')}
  for n in [n for n in names if n.startswith('B_L_') and ('Arm' in n or 'Forearm' in n or 'Hand' in n or 'Finger' in n)]:
   pose[n]=free[n]
  # Running retains the source's free-arm swing while fingers stay relaxed.
  if role=='Running':
   for n in ['B_L_UpperArm','B_L_Forearm','B_L_Hand']:pose[n]=left_pose[n]
  apply(pose);Lfree=armik.W(rig,'B_L_Hand').copy();contact=smooth((phase-.12)/.5) if role=='Fidget' else 0
  if role=='Running':Lfree.translation.x+=.06
  L=Lfree.lerp(B@rels['L'],contact)
  if role=='Fidget':
   for n in ['B_L_UpperArm','B_L_Forearm','B_L_Hand']:pose[n]=pose[n].lerp(raw['AimSource'][0][n],contact)
  for s,w in [('R',1),('L',contact)]:
   for n,q in G[s]['finger_local'].items():pose[n]=pose[n].lerp(Quaternion(q).to_matrix().to_4x4(),w)
  frames.append({'pose':pose,'R':R,'L':L,'B':B,'contact':contact})
 reports[role]={s:solve_clip(frames,s) for s in 'RL'};poses=[f['pose'] for f in frames]
 if role=='Running':
  for i in range(len(poses)-5,len(poses)):poses[i]=blend(poses[i],poses[0],smooth((i-(len(poses)-5))/4))
 write(role,poses)
 print('MOTION',role,{s:{'swing':max(x['swing'] for x in reports[role][s]),'twist':max(abs(x['twist']) for x in reports[role][s]),'reach':max(x['reach'] for x in reports[role][s])} for s in 'RL'})
source=raw['Death'];death=[blend(ST,source[0],smooth(i/6)) for i in range(6)]+source
for pose in death:
 for n,q in G['R']['finger_local'].items():pose[n]=Quaternion(q).to_matrix().to_4x4()
write('Death',death)
# Retain only runtime roles; the aiming study remains in its source checkpoint.
a=bpy.data.actions.get('AimSource')
if a:bpy.data.actions.remove(a)
(P/'work/all_arm_checks.json').write_text(json.dumps(reports,indent=2));(P/'work/clip_timing.json').write_text(json.dumps({'attack_impact_s':1.0,'native_attack_impact_s':1.0,'roles':{a.name:{'duration_s':float(a.frame_range[1]/30)} for a in bpy.data.actions if a.use_fake_user}},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/all_motion.blend'))
