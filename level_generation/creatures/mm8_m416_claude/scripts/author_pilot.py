"""Native raised carry and short two-hand fire on fitted, fixed-length source bones."""
from pathlib import Path
import bpy,sys,json,math,numpy as np
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common,armik
bpy.ops.wm.open_mainfile(filepath=str(P/'work/fingered.blend'));rig=bpy.data.objects['Rig'];scene=bpy.context.scene;scene.render.fps=30
names=[p.name for p in rig.pose.bones];G={s:json.loads((P/('work/grip_pose.json' if s=='R' else 'work/grip_pose_L.json')).read_text()) for s in 'RL'}
def setact(a):
 rig.animation_data.action=a
 if a and a.slots:rig.animation_data.action_slot=a.slots[0]
def snap():return {n:rig.pose.bones[n].matrix_basis.copy() for n in names}
def apply(pose):
 setact(None)
 for n,m in pose.items():rig.pose.bones[n].matrix_basis=m
 bpy.context.view_layer.update()
def smooth(x):x=max(0,min(1,x));return x*x*(3-2*x)
def blend(a,b,w):return {n:a[n].lerp(b[n],w) for n in names}
raw={}
for a in list(bpy.data.actions):
 setact(a);raw[a.name]=[]
 for f in range(int(a.frame_range[1])+1):scene.frame_set(f);raw[a.name].append(snap())
apply(raw['AimSource'][0]);B0=Matrix(((-1,0,0),(0,-1,0),(0,0,1))).to_4x4()
rels={}
for s,axis,centre in [('R',Vector((0,.35,.937)).normalized(),Vector((0,0,0))),('L',Vector((0,-1,0)),Vector((0,.24,.06)))]:
 H=armik.W(rig,f'B_{s}_Hand').copy();A=(H.to_3x3()@Vector(G[s]['handle_axis_hand_local'])).normalized()
 R=A.rotation_difference(axis).to_matrix()@H.to_3x3().normalized()
 if s=='L':R=Quaternion(axis,math.radians(-25)).to_matrix()@R
 rel=B0.to_3x3().inverted()@R;M=rel.to_4x4();M.translation=centre-rel@Vector(G[s]['handle_centre_hand_local']);rels[s]=M
(P/'work/prop_grips.json').write_text(json.dumps({s:[list(row) for row in M] for s,M in rels.items()},indent=2))
# Fixed prop frame fully constrains both palms. Choose the elbow plane over the complete clip.
def solve_clip(frames,side):
 PH=list(range(-180,181,10));cost=[];poses=[]
 for fr in frames:
  candidates=[];cs=[]
  for phi in PH:
   apply(fr['pose']);T=fr[side].translation;u=(T-armik.W(rig,f'B_{side}_UpperArm').translation).normalized()
   S=armik.W(rig,f'B_{side}_UpperArm').translation.copy();pole=Vector((-.8 if side=='R' else .8,0,-.5));pole=Quaternion(u,math.radians(phi))@pole
   reach=armik.solve(rig,side,T,pole=S+pole,hand_rot=fr[side].to_3x3().normalized())
   sw,tw=armik.wrist_cost(rig,side,fr[side].to_3x3().normalized());elbow=armik.W(rig,f'B_{side}_Forearm').translation;clear=1000*max(0,elbow.x-S.x+.10) if side=='R' else 0;cs.append(clear+sw+.025*sw*sw+.35*abs(tw)+.06*abs(phi)+.2*max(0,abs(tw)-145)**2+1000*max(0,reach-.99));candidates.append((snap(),sw,tw,reach))
  poses.append(candidates);cost.append(cs)
 acc=np.array(cost[0]);back=[];trans=np.abs(np.subtract.outer(PH,PH))*.6
 for c in cost[1:]:
  v=acc[:,None]+trans;idx=v.argmin(axis=0);back.append(idx);acc=np.array(c)+v[idx,np.arange(len(PH))]
 k=int(acc.argmin());path=[k]
 for b in reversed(back):k=int(b[k]);path.append(k)
 path.reverse();report=[]
 for fr,opts,k in zip(frames,poses,path):
  pose,sw,tw,reach=opts[k]
  for n in [f'B_{side}_{b}' for b in ('UpperArm','Forearm','Hand')]:fr['pose'][n]=pose[n]
  report.append({'swing':sw,'twist':tw,'reach':reach,'phi':PH[k]})
 return report
# Rest-derived free arm, slightly away from the sash and hip quiver.
apply(raw['Standing'][0])
for n in [n for n in names if n.startswith('B_L_') and ('Arm' in n or 'Forearm' in n or 'Hand' in n or 'Finger' in n)]:rig.pose.bones[n].matrix_basis=Matrix()
bpy.context.view_layer.update();M=armik.W(rig,'B_L_UpperArm').copy();d=(armik.W(rig,'B_L_Forearm').translation-M.translation).normalized();Q=d.rotation_difference(Vector((.40,-.08,-1)).normalized());armik.set_world(rig,'B_L_UpperArm',armik.rot_world(M,Q.to_matrix()@M.to_3x3().normalized()));free=snap()
frames_by={};reports={};standing0=raw['Standing'][0]
for role in ['Standing','Walking','Attack']:
 frames=[];N=52 if role=='Attack' else len(raw[role])
 for i in range(N):
  t=i/30;w=smooth(t/.65)*(1-smooth((t-1.2)/.5)) if role=='Attack' else 0
  pose=blend(standing0,raw['AimSource'][0],w) if role=='Attack' else raw[role][i].copy();apply(pose)
  pel=armik.W(rig,'B_Pelvis').translation;offset=pel-Vector((-.01197,.03774,1.107))
  pitch=math.radians(70*(1-w));B=Matrix.Rotation(math.radians(30*(1-w)),4,'Z')@Matrix.Rotation(math.radians(-30*(1-w)),4,'Y')@B0@Matrix.Rotation(pitch,4,'X');B.translation=(armik.W(rig,'B_R_UpperArm').translation+Vector((-.18,-.25,-.06))).lerp(armik.W(rig,'B_R_UpperArm').translation+Vector((-.05,-.34,.07)),w)
  B.translation.y+=.015*max(0,1-abs(t-1.033)/.1) if role=='Attack' else 0
  R=B@rels['R'];Lcontact=B@rels['L']
  for n in [n for n in names if n.startswith('B_L_') and ('Arm' in n or 'Forearm' in n or 'Hand' in n or 'Finger' in n)]:pose[n]=free[n].lerp(raw['AimSource'][0][n],w)
  saved=pose.copy()
  for n in [n for n in names if n.startswith('B_L_') and ('Arm' in n or 'Forearm' in n or 'Hand' in n or 'Finger' in n)]:pose[n]=free[n]
  apply(pose);Lfree=armik.W(rig,'B_L_Hand').copy();pose=saved;contact=smooth((t-.12)/.48)*(1-smooth((t-1.25)/.30)) if role=='Attack' else 0
  L=Lfree.lerp(Lcontact,contact)
  for s,weight in [('R',1),('L',contact)]:
   for n,q in G[s]['finger_local'].items():pose[n]=pose[n].lerp(Quaternion(q).to_matrix().to_4x4(),weight)
  frames.append({'pose':pose,'R':R,'L':L,'B':B,'contact':contact})
 reports[role]={s:solve_clip(frames,s) for s in 'RL'};frames_by[role]=frames
 for i,fr in enumerate(frames):
  apply(fr['pose']);fr['error']=(armik.W(rig,'B_L_Hand').translation-fr['L'].translation).length
  if role=='Attack' and .65<=i/30<=1.2:assert fr['error']<.005,fr['error']
 old=bpy.data.actions.get(role)
 if old:bpy.data.actions.remove(old)
 a=bpy.data.actions.new(role);a.use_fake_user=True;setact(a);prev={}
 for i,fr in enumerate(frames):
  for n,m in fr['pose'].items():
   pb=rig.pose.bones[n];pb.rotation_mode='QUATERNION';pb.matrix_basis=m;q=pb.rotation_quaternion.copy()
   if n in prev and q.dot(prev[n])<0:q=-q
   prev[n]=q;pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=i)
   if n=='B_Pelvis':pb.keyframe_insert('location',frame=i)
 a.use_frame_range=True;a.frame_start=0;a.frame_end=N-1
 print('PILOT',role,{s:{'swing':max(x['swing'] for x in reports[role][s]),'twist':max(abs(x['twist']) for x in reports[role][s]),'reach':max(x['reach'] for x in reports[role][s])} for s in 'RL'})
(P/'work/pilot_arm_checks.json').write_text(json.dumps(reports,indent=2))
setact(None);bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/pilot.blend'))
# Review stand-in uses the exact future stock/grip dimensions.
parts=[]
def box(c,d):
 bpy.ops.mesh.primitive_cube_add();o=bpy.context.object;o.scale=Vector(d)*.5;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.location=c;parts.append(o)
box((0,.12,.06),(.038,.65,.038));box((0,0,-.006),(.028,.032,.11));box((0,.39,.055),(.53,.04,.035));box((0,.19,.083),(.009,.48,.009))
for o in bpy.context.selected_objects:o.select_set(False)
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();prop=bpy.context.object;bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
mat=bpy.data.materials.new('Stock');mat.diffuse_color=(.29,.13,.04,1);prop.data.materials.append(mat);common.workbench_clay(scene)
out=P/'review/pilot';out.mkdir(exist_ok=True)
for role,picks in [('Standing',[0]),('Walking',[0,6,12,18]),('Attack',[0,8,15,20,30,33,39,51])]:
 for i in picks:
  apply(frames_by[role][i]['pose']);prop.matrix_world=frames_by[role][i]['B'];common.render_views(str(out/f'{role}_{i:02}'),.95,2.2,views=('front','left','three_quarter'),resolution=(360,540))
