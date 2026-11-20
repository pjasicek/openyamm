"""Adapt the completed wolfman's whole-body rake to the Guardian's fitted source-frame rig."""
from pathlib import Path
import ast,hashlib,json,math,sys
import bpy,numpy as np
from mathutils import Matrix,Vector,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'mm6_natm_claude/scripts'));import armik,common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/attack_revision_02_before/work/rig_uv.blend'))
scene=bpy.context.scene;scene.render.fps=30;rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];names=[b.name for b in rig.data.bones]
tree=ast.parse((P/'scripts/author_pilots.py').read_text());wanted={'action','reset','current','apply','turn','surface','leg'}
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in wanted],type_ignores=[]),'pilot_helpers','exec'),globals())
action(bpy.data.actions['Standing']);scene.frame_set(0);ready=current();home={n:armik.W(rig,n).copy() for n in names};action(None)
anchors={sd:home[f'B_{sd}_Foot'].translation.copy() for sd in 'LR'};poles={}
for sd in 'LR':
 H=home[f'B_{sd}_Thigh'].translation;K=home[f'B_{sd}_Calf'].translation;u=(anchors[sd]-H).normalized();poles[sd]=((K-H)-u*(K-H).dot(u)).normalized()
co=np.array([tuple(v.co) for v in body.data.vertices]);footids=np.flatnonzero((co[:,2]<.12)&(abs(co[:,0])<.5))
def fingerprint(a):
 return hashlib.sha256(repr([(f.data_path,f.array_index,[(tuple(k.co),k.interpolation) for k in f.keyframe_points]) for l in a.layers for s in l.strips for b in s.channelbags for f in b.fcurves]).encode()).hexdigest()
unchanged={a.name:fingerprint(a) for a in bpy.data.actions if a.name not in ('Attack','Cast')}
before=set(bpy.data.objects);acts=set(bpy.data.actions);srcpath=P.parents[2]/'assets_source/worlds/mm6/models/mm6_wwf.glb';bpy.ops.import_scene.gltf(filepath=str(srcpath));objects=set(bpy.data.objects)-before;src=next(o for o in objects if o.type=='ARMATURE');srcact=next(a for a in set(bpy.data.actions)-acts if a.name=='Attack.001' or a.name.startswith('Attack_') or a.name=='Attack')
src.animation_data.action=srcact;src.animation_data.action_slot=srcact.slots[0]
mp={'B_Pelvis':'Hips','B_Spine':'Spine02','B_Spine1':'Spine01','B_Spine2':'Spine','B_Neck':'neck','B_Head':'Head'}
for sd,long in [('L','Left'),('R','Right')]:
 for a,b in [('Clavicle','Shoulder'),('UpperArm','Arm'),('Forearm','ForeArm'),('Hand','Hand'),('Thigh','UpLeg'),('Calf','Leg'),('Foot','Foot'),('Toe0','ToeBase')]:mp[f'B_{sd}_{a}']=long+b
mp={n:s for n,s in mp.items() if s in src.pose.bones}
def sw(n):return src.matrix_world@src.pose.bones[mp[n]].matrix
scene.frame_set(0);s0={n:sw(n).copy() for n in mp};scale=sum((home[b].translation-home[a].translation).length for a,b in [('B_L_Thigh','B_L_Calf'),('B_L_Calf','B_L_Foot')])/sum((s0[b].translation-s0[a].translation).length for a,b in [('B_L_Thigh','B_L_Calf'),('B_L_Calf','B_L_Foot')])
# Keep the wolfman's fast strike; extend preparation/recovery around the Guardian's native 1 s damage event.
time_map=[(0,0),(.28,.02),(.60,4/24),(.86,5/24),(.95,7/24),(1.035,9/24),(1.50,.5)]
# Small side-to-side weight transfer keeps the double rake from reading as a mirrored pose.
side_keys=[(0,0),(.78,5.5),(1.04,-4.5),(1.5,0)]
def side_tilt(t):
 for (a,x),(b,y) in zip(side_keys,side_keys[1:]):
  if t<=b:
   u=max(0,min(1,(t-a)/(b-a)));return x+(y-x)*u*u*(3-2*u)
 return 0.0
assert side_tilt(0)==0 and side_tilt(1.5)==0
assert abs(side_tilt(.78)-5.5)<1e-8 and abs(side_tilt(1.04)+4.5)<1e-8
poses=[];samples=[]
for i in range(91):
 t=i/60;st=float(np.interp(t,*np.array(time_map).T));sf=st*30;scene.frame_set(int(sf),subframe=sf%1);source={n:sw(n).copy() for n in mp};apply(ready)
 for n in names:
  if n not in mp:continue
  D=source[n].to_quaternion()@s0[n].to_quaternion().inverted();M=armik.W(rig,n);M=armik.rot_world(M,D.to_matrix()@home[n].to_3x3().normalized())
  if n=='B_Pelvis':
   delta=source[n].translation-s0[n].translation;M.translation=home[n].translation+Vector((delta.x*scale,delta.y*scale*1.35,delta.z*scale*1.15))
  armik.set_world(rig,n,M)
 tilt=side_tilt(t)
 turn('B_Pelvis',(0,1,0),tilt*.3)
 M=armik.W(rig,'B_Pelvis');M.translation.x+=tilt*.004;armik.set_world(rig,'B_Pelvis',M)
 turn('B_Spine',(0,1,0),tilt*.4);turn('B_Spine1',(0,1,0),tilt*.3)
 turn('B_Head',(0,1,0),-tilt*.2)
 # Keep the forward-driving pelvis inside both fixed-foot leg reach spheres.
 lower=0.0
 for sd in 'LR':
  H=armik.W(rig,f'B_{sd}_Thigh').translation;K=armik.W(rig,f'B_{sd}_Calf').translation;A=armik.W(rig,f'B_{sd}_Foot').translation
  reach=((K-H).length+(A-K).length)*.985;v=H-anchors[sd];z=math.sqrt(max(.001,reach*reach-v.x*v.x-v.y*v.y));lower=max(lower,v.z-z)
 M=armik.W(rig,'B_Pelvis');M.translation.z-=lower;armik.set_world(rig,'B_Pelvis',M)
 for sd in 'LR':leg(sd,anchors[sd],poles[sd],home[f'B_{sd}_Foot'].to_3x3().normalized())
 env=float(np.interp(st,[0,4/24,5/24,7/24,9/24,.5],[0,.45,.6,1,.8,0]));rig.pose.bones['Jaw'].rotation_quaternion=Quaternion((1,0,0),math.radians(-3+18*env))
 for sd in 'LR':
  for k in range(3):
   n=f'B_{sd}_Finger{k}'
   if n in rig.pose.bones:rig.pose.bones[n].rotation_quaternion=Quaternion((0,0,1),math.radians((k-1)*4*env))
 bpy.context.view_layer.update();soles=surface()[footids,2];M=armik.W(rig,'B_Pelvis');M.translation.z+=max(0,-float(soles.min()));armik.set_world(rig,'B_Pelvis',M)
 poses.append(current());samples.append({'time':t,'side_tilt_degrees':tilt,'source_time':st,'pelvis':list(armik.W(rig,'B_Pelvis').translation),'head':list(armik.W(rig,'B_Head').translation),'feet':{sd:list(armik.W(rig,f'B_{sd}_Foot').translation) for sd in 'LR'},'wrists':{sd:list(armik.W(rig,f'B_{sd}_Hand').translation) for sd in 'LR'}})
for ob in objects:bpy.data.objects.remove(ob,do_unlink=True)
for a in set(bpy.data.actions)-acts:bpy.data.actions.remove(a)
old=bpy.data.actions['Attack'];bpy.data.actions.remove(old);a=bpy.data.actions.new('Attack');a.use_fake_user=True;action(a);previous={};poses[0]=ready;poses[-1]=ready
for i,pose in enumerate(poses):
 for n,(q,l) in pose.items():
  if n in previous and q.dot(previous[n])<0:q=-q
  previous[n]=q.copy();b=rig.pose.bones[n];b.rotation_quaternion=q;b.keyframe_insert('rotation_quaternion',frame=i*.5)
  if n=='B_Pelvis':b.location=l;b.keyframe_insert('location',frame=i*.5)
a.use_frame_range=True;a.frame_start=0;a.frame_end=45
# Update existing twist controls without altering their fitted weights.
tree=ast.parse((P.parent/'mm6_natm_claude/scripts/twist_bones.py').read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='twist_about'],type_ignores=[]),'twist_helper','exec'),globals())
action(a)
for i in range(91):
 f=i*.5;scene.frame_set(int(f),subframe=f%1)
 for sd in 'LR':
  fb,hb=rig.data.bones[f'B_{sd}_Forearm'],rig.data.bones[f'B_{sd}_Hand'];axis=(fb.matrix_local.inverted()@hb.head_local).normalized();rel=(rig.pose.bones[fb.name].matrix.inverted()@rig.pose.bones[hb.name].matrix).to_quaternion();rest=(fb.matrix_local.inverted()@hb.matrix_local).to_quaternion();pb=rig.pose.bones[f'B_{sd}_ForearmTwist'];pb.rotation_quaternion=Quaternion(axis,.6*twist_about(rel@rest.inverted(),axis));pb.keyframe_insert('rotation_quaternion',frame=f)
  ub=rig.data.bones[f'B_{sd}_UpperArm'];axis=(ub.matrix_local.inverted()@fb.head_local).normalized();pb=rig.pose.bones[f'B_{sd}_UpperArmTwist'];pb.rotation_quaternion=Quaternion(axis,-.5*twist_about(rig.pose.bones[ub.name].matrix_basis.to_quaternion(),axis));pb.keyframe_insert('rotation_quaternion',frame=f)
for l in a.layers:
 for s in l.strips:
  for b in s.channelbags:
   for f in b.fcurves:
    for k in f.keyframe_points:k.interpolation='LINEAR'
assert all(fingerprint(bpy.data.actions[n])==h for n,h in unchanged.items())
O=P/'review/attack_revision_03';O.mkdir(exist_ok=True,parents=True);report={'source':str(srcpath.relative_to(P.parents[2])),'source_sha256':hashlib.sha256(srcpath.read_bytes()).hexdigest(),'source_clip':'Attack','source_duration':.5,'duration':1.5,'source_scale':scale,'time_map':time_map,'side_tilt_keys':side_keys,'pelvis_side_shift_m_per_degree':.004,'unchanged_clip_hashes':unchanged,'samples':samples};(O/'adaptation.json').write_text(json.dumps(report,indent=2)+'\n')
action(None);bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/attack_revision_03.blend'));common.workbench_clay(scene);action(a)
for i,t in enumerate([0,.3,.6,.8,.9,.95,1.035,1.2,1.5]):
 f=t*30;scene.frame_set(int(f),subframe=f%1);common.render_views(str(O/f'wolfman_guardian_{i}'),1.25,3.5,views=('front','left','three_quarter'),resolution=(600,600))
print('ATTACK_REVISED',len(poses),'poses; unrelated actions unchanged',flush=True)
