"""Mirror the accepted Cannibal lunge onto Triton's fitted source frames and forward grip."""
import bpy,sys,json,math,hashlib
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import armik,common
SOURCE=P.parent/'mm6_natm_claude/work/rig_v5.blend';BASE=P/'work/attack_revision_base/master_textured_uv.blend'
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));sc=bpy.context.scene;srig=bpy.data.objects['Rig'];off=json.loads(sc['rig_offsets']);S={n:Matrix(v['R_src']) for n,v in off.items()};source_height=srig.data.bones['B_Pelvis'].head_local.z
source={}
for name in ('Attack','Standing'):
 a=bpy.data.actions[name];srig.animation_data.action=a;srig.animation_data.action_slot=a.slots[0];end=float(a.frame_range[1]);rows=[]
 for f in np.arange(0,end+.001,.25) if name=='Attack' else [0.]:
  sc.frame_set(int(f),subframe=float(f%1));rows.append({n:(srig.matrix_world@srig.pose.bones[n].matrix).copy() for n in S})
 source[name]={'frames':rows,'end':end}
print('SOURCE',[(k,v['end']) for k,v in source.items()],flush=True)
bpy.ops.wm.open_mainfile(filepath=str(BASE))
for im in bpy.data.images:
 if im.source=='FILE' and im.filepath.startswith('//'):
  im.filepath=str((P/'work'/im.filepath[2:]).resolve())
sc=bpy.context.scene;sc.render.fps=30;rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];prop=bpy.data.objects['TridentMesh'];off=json.loads(sc['rig_offsets']);T={n:Matrix(v['R_src']) for n,v in off.items()};M=Matrix.Diagonal((-1,1,1));names=[b.name for b in rig.data.bones]
def swap(n):return n.replace('_L_','_TEMP_').replace('_R_','_L_').replace('_TEMP_','_R_')
def mirrored(row,n):
 sn=swap(n);return M@row[sn].to_3x3().normalized()@S[sn].inverted()@M@T[n]
def act(a):
 rig.animation_data.action=a
 if a is not None and len(a.slots):rig.animation_data.action_slot=a.slots[0]
def snapshot():return {n:rig.pose.bones[n].matrix_basis.copy() for n in names}
act(bpy.data.actions['Standing']);sc.frame_set(0);standing=snapshot()
# Same fist and contact centre, with a forward grip and 40 cm more shaft ahead of the hand.
act(None)
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update();old=rig.data.bones['Trident'].matrix_local.copy();new=old@Matrix.Rotation(math.pi,4,'X')
for v in prop.data.vertices:
 q=old.inverted()@(prop.matrix_world@v.co);q.y+=.4;v.co=prop.matrix_world.inverted()@(new@q)
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT');b=rig.data.edit_bones['Trident'];b.matrix=new;b.length=.15;bpy.ops.object.mode_set(mode='OBJECT')
# Keep existing locomotion/body motion; fit the forward carry relative to its current chest.
carry=source['Standing']['frames'][0];carry_chest=mirrored(carry,'B_Spine2');armnames=['B_L_Clavicle','B_L_UpperArm','B_L_Forearm','B_L_Hand']
groups=[g.name for g in body.vertex_groups]
feet=np.array([sum(e.weight for e in v.groups if groups[e.group].endswith(('_Foot','_Toe0')))>.5 for v in body.data.vertices])
def coords():
 bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();v=np.array([tuple(body.matrix_world@x.co) for x in me.vertices]);ev.to_mesh_clear();return v
axis=Vector((.9942427,.1071379,-.001769))
written={}
for name in ('Standing','Walking','Running','Hit','Fidget','Death','Attack'):
 oldact=bpy.data.actions[name];rows=[]
 if name=='Attack':
  # Keep the accepted fast drive/recovery; a longer draw-back puts the thrust at MM8's native 1.0 s impact.
  duration=1.65;frames=np.arange(0,duration*30+.001,.25)
 else:frames=np.arange(0,float(oldact.frame_range[1])+.001,.25)
 saved=[]
 for f in frames:
  act(oldact);sc.frame_set(int(min(f,float(oldact.frame_range[1]))),subframe=float(f%1));saved.append(snapshot())
 for f,snap in zip(frames,saved):
  act(None)
  for n,m in (standing if name=='Attack' else snap).items():rig.pose.bones[n].matrix_basis=m
  bpy.context.view_layer.update()
  if name=='Attack':
   t=f/30
   # Original Cannibal drive peaks at 0.626 s; shift its brisk strike after a readable anticipation.
   keytimes=[(0,0),(.70,.38),(1.0,.56),(1.15,.76),(duration,1.5)]
   st=np.interp(t,[a for a,b in keytimes],[b for a,b in keytimes]);fi=min(len(source['Attack']['frames'])-1,st*30*4);i=int(fi);j=min(i+1,len(source['Attack']['frames'])-1);w=fi-i
   row={}
   for n in S:
    a=source['Attack']['frames'][i][n];b=source['Attack']['frames'][j][n];q=a.to_quaternion().slerp(b.to_quaternion(),w);mm=q.to_matrix().to_4x4();mm.translation=a.translation.lerp(b.translation,w);row[n]=mm
   for n in T:
    if 'Finger' in n:continue
    R=mirrored(row,n);mm=R.to_4x4();mm.translation=armik.W(rig,n).translation
    if n=='B_Pelvis':mm.translation=M@row[n].translation*(rig.data.bones[n].head_local.z/source_height)
    armik.set_world(rig,n,mm)
   # The Cannibal's buckler arm becomes the Triton's free counterbalancing arm.
   for n,m in standing.items():
    if 'Finger' in n:rig.pose.bones[n].matrix_basis=m
  else:
   C=armik.W(rig,'B_Spine2').to_3x3().normalized()@carry_chest.inverted()
   for n in armnames:
    mm=(C@mirrored(carry,n)).to_4x4();mm.translation=armik.W(rig,n).translation;armik.set_world(rig,n,mm)
  if name=='Death':
   # Reuse the fitted fall arm, easing out of the forward carry before the torso meets the floor.
   w=float(np.clip((f/30-.15)/.85,0,1));w=w*w*(3-2*w)
   for n in armnames:
    pb=rig.pose.bones[n];pb.rotation_quaternion=pb.matrix_basis.to_quaternion().slerp(snap[n].to_quaternion(),w)
   bpy.context.view_layer.update()
   H=armik.W(rig,'B_L_Hand');d=(H.to_3x3()@axis).normalized();height=H.translation.z-.07
   z=float(np.clip(d.z,-max(.01,height)/1.1,max(.01,height)/.705185));flat=Vector((d.x,d.y,0)).normalized();aim=flat*math.sqrt(max(0,1-z*z))+Vector((0,0,z))
   R=d.rotation_difference(aim).to_matrix()@H.to_3x3();armik.set_world(rig,'B_L_Hand',armik.rot_world(H,R))
  if name=='Attack':
   # Mesh-measured support height preserves the source stepping and heel lift.
   dz=.001-float(coords()[feet,2].min());mm=armik.W(rig,'B_Pelvis');mm.translation.z+=dz;armik.set_world(rig,'B_Pelvis',mm)
  rows.append(snapshot())
 if name=='Death':
  # Choose the roll and elbow plane over the whole fall, retaining the existing wrist path.
  targets=[]
  for row in rows[::4]:
   for n,m in row.items():rig.pose.bones[n].matrix_basis=m
   bpy.context.view_layer.update();H=armik.W(rig,'B_L_Hand');targets.append({'snap':row,'wrist':H.translation.copy(),'dir':H.to_3x3()@axis})
  solution=armik.arm_dp(rig,'L',targets,axis,phis=range(-30,31,10),k_twist=.5,twist_neutral=15,k_dphi=.9,k_dpsi=.8)
  psi=np.unwrap(np.radians([x['psi'] for x in solution]))*180/math.pi
  for i,row in enumerate(rows):
   for n,m in row.items():rig.pose.bones[n].matrix_basis=m
   bpy.context.view_layer.update();H=armik.W(rig,'B_L_Hand');u=min(i/4,len(solution)-1);phi=float(np.interp(u,np.arange(len(solution)),[x['phi'] for x in solution]));roll=float(np.interp(u,np.arange(len(solution)),psi))
   armik.apply_arm(rig,'L',row,H.translation.copy(),axis,H.to_3x3()@axis,phi,roll)
   rows[i]=snapshot()
 if name in ('Attack','Death'):
  # A 50 ms filter removes source/retiming corners without slowing the actual drive.
  original=rows;rows=[];filtered=[n for n in names if n not in ('Trident',) and 'Finger' not in n and ('Arm' in n or 'Hand' in n or 'Clavicle' in n)]
  for i,row in enumerate(original):
   for n,m in row.items():rig.pose.bones[n].matrix_basis=m
   for n in filtered:
    if name=='Death' and n not in armnames:continue
    ref=row[n].to_quaternion();v=np.zeros(4)
    for k in range(-18,19):
     q=original[min(len(original)-1,max(0,i+k))][n].to_quaternion();q=-q if q.dot(ref)<0 else q;v+=np.array(q)*math.exp(-.5*(k/6)**2)
    rig.pose.bones[n].rotation_quaternion=Quaternion(v/np.linalg.norm(v))
   rows.append(snapshot())
 bpy.data.actions.remove(oldact);a=bpy.data.actions.new(name);a.use_fake_user=True;a.use_frame_range=True;a.frame_start=0;a.frame_end=float(frames[-1]);act(a);prev={}
 for f,row in zip(frames,rows):
  for n,mm in row.items():
   pb=rig.pose.bones[n];pb.rotation_mode='QUATERNION';q=mm.to_quaternion()
   if n in prev and q.dot(prev[n])<0:q=-q
   prev[n]=q;pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=float(f))
   if n=='B_Pelvis':pb.location=mm.translation;pb.keyframe_insert('location',frame=float(f))
 written[name]=float(frames[-1])/30
 print('FITTED',name,written[name],flush=True)
# Helpers follow the revised arm poses, sampled on the same 120Hz grid.
FA=.6;UA=.5;code=(P/'scripts/twist_bones.py').read_text();exec(code[code.index('def twist_about('):code.index("for act in [a for a in bpy.data.actions if a.use_fake_user]:")])
for a in list(bpy.data.actions):
 if a.name in written:bake_twist(a)
for a in list(bpy.data.actions):
 if a.name not in written:continue
 act(a)
 for f in np.arange(0,float(a.frame_range[1])+.001,.25):
  sc.frame_set(int(f),subframe=float(f%1))
  for side,sgn in [('L',1),('R',-1)]:
   C=armik.W(rig,f'B_{side}_Clavicle');Cr=rig.data.bones[f'B_{side}_Clavicle'].matrix_local;D=C@Cr.inverted()
   arm=armik.W(rig,f'B_{side}_Forearm').translation-armik.W(rig,f'B_{side}_UpperArm').translation
   local=D.to_3x3().inverted()@arm;lift=max(0,math.atan2(local.z,math.hypot(local.x,local.y))+math.radians(15))*.8
   n=f'Pauldron_{side}';B=rig.data.bones[n].matrix_local;R=D.to_3x3()@Matrix.Rotation(lift*sgn,3,Vector((0,-1,0)))@B.to_3x3();mm=R.to_4x4();mm.translation=D@B.translation;armik.set_world(rig,n,mm)
   rig.pose.bones[n].keyframe_insert('rotation_quaternion',frame=float(f))
for a in bpy.data.actions:
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for key in fc.keyframe_points:key.interpolation='LINEAR'
act(None);bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/lunge_candidate.blend'));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/master_textured_uv.blend'))
report={'source':str(SOURCE),'sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'method':'Mirrored accepted Cannibal source-frame world rotations; fitted left forward grip; native 1.0-second impact','source_attack_seconds':source['Attack']['end']/30,'duration_seconds':written['Attack'],'tip_local':[0,1.1,0],'butt_local':[0,-.705185,0]}
(P/'work/lunge_candidate.json').write_text(json.dumps(report,indent=2)+'\n')
common.workbench_clay(sc,True)
for name,ts in [('Standing',[0]),('Attack',[0,.5,.85,1.,1.15,1.65]),('Death',[1.,2.5,3.63])]:
 act(bpy.data.actions[name])
 for t in ts:
  f=t*30;sc.frame_set(int(f),subframe=f%1);common.render_views(str(P/'review'/f'lunge_v3_{name}_{t:.2f}'),1.0,2.5,views=('front','left','three_quarter'),resolution=(450,600))

import runpy
runpy.run_path(str(P/"scripts/export_runtime.py"),run_name="__main__")
