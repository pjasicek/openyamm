"""Fit the selected source clips to the native Cyclops stance, pickup and release."""
from pathlib import Path
import bpy,math,json,sys,numpy as np
from mathutils import Vector,Matrix,Quaternion
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import armik,common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/motion_sources.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];import surface_fit;surface_fit.apply(body);import fit_skin;fit_skin.apply(body,rig);scene=bpy.context.scene;names=[b.name for b in rig.data.bones]
def action(a):
 rig.animation_data_create();rig.animation_data.action=a
 if a and a.slots:rig.animation_data.action_slot=a.slots[0]
def sample(a,f):
 action(a);scene.frame_set(int(f),subframe=f-int(f));pose=current()
 # The mesh already has relaxed curved fingers; source curls double that curvature.
 for n in names:
  if 'Finger' in n:pose[n]=(Quaternion(),Vector())
 return pose
def current():return {n:(rig.pose.bones[n].rotation_quaternion.copy(),rig.pose.bones[n].location.copy()) for n in names}
def apply(pose):
 action(None)
 for n,(q,l) in pose.items():
  pb=rig.pose.bones[n];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q;pb.location=l;pb.scale=(1,1,1)
 bpy.context.view_layer.update()
def blend(a,b,t):return {n:(a[n][0].slerp(b[n][0],t),a[n][1].lerp(b[n][1],t)) for n in names}
def smooth(t):t=np.clip(t,0,1);return float(t*t*(3-2*t))
def write(name,frames,rate=30):
 if name in bpy.data.actions:bpy.data.actions.remove(bpy.data.actions[name])
 a=bpy.data.actions.new(name);a.use_fake_user=True;action(a);prev={}
 for f,pose in enumerate(frames):
  for n,(q,l) in pose.items():
   if n in prev and q.dot(prev[n])<0:q=-q
   prev[n]=q;pb=rig.pose.bones[n];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q;pb.location=l;pb.scale=(1,1,1)
   pb.keyframe_insert('rotation_quaternion',frame=f*30/rate)
   if n=='B_Pelvis':pb.keyframe_insert('location',frame=f*30/rate)
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for key in fc.keyframe_points:key.interpolation='LINEAR'
 a.use_frame_range=True;a.frame_start=0;a.frame_end=(len(frames)-1)*30/rate;action(None);return a
def floor(only_penetration=False):
 ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();low=min((body.matrix_world@v.co).z for v in me.vertices);ev.to_mesh_clear()
 if only_penetration:low=min(0,low)
 m=armik.W(rig,'B_Pelvis');m.translation.z+=.004-low;armik.set_world(rig,'B_Pelvis',m)
 return low
def turn(n,axis,deg):
 m=armik.W(rig,n);r=Matrix.Rotation(math.radians(deg),3,Vector(axis));armik.set_world(rig,n,armik.rot_world(m,r@m.to_3x3()))
def leg(side,target,footrot):
 upper,knee,ankle=[f'B_{side}_{n}' for n in ['Thigh','Calf','Foot']]
 H=armik.W(rig,upper).translation;K=armik.W(rig,knee).translation;A=armik.W(rig,ankle).translation
 l1=(K-H).length;l2=(A-K).length;d=Vector(target)-H;dist=min(d.length,(l1+l2)*.999);u=d.normalized();pole=Vector((0,-1,0));v=(pole-u*pole.dot(u)).normalized()
 c=max(-1,min(1,(l1*l1+dist*dist-l2*l2)/(2*l1*dist)));newk=H+l1*(u*c+v*math.sqrt(1-c*c))
 for bone,child,tgt in [(upper,knee,newk),(knee,ankle,H+u*dist)]:
  m=armik.W(rig,bone);old=armik.W(rig,child).translation-m.translation;q=old.rotation_difference(tgt-m.translation);armik.set_world(rig,bone,armik.rot_world(m,q.to_matrix()@m.to_3x3()))
 armik.set_world(rig,ankle,armik.rot_world(armik.W(rig,ankle),footrot))
def curve(keys,t):
 for i in range(len(keys)-1):
  ta,a=keys[i];tb,b=keys[i+1]
  if t<=tb:
   f=smooth((t-ta)/(tb-ta));return np.asarray(a)*(1-f)+np.asarray(b)*f
 return np.asarray(keys[-1][1])
def free_arms(extra=0):
 for side,sign in [('L',1),('R',-1)]:
  u=f'B_{side}_UpperArm';f=f'B_{side}_Forearm';h=f'B_{side}_Hand'
  delta=.035+extra
  if abs(delta)<1e-6:continue
  M=armik.W(rig,h);target=M.translation+Vector((sign*delta,-max(0,extra)*.5,0));pole=armik.W(rig,f).translation+Vector((sign*.025*min(1,abs(delta)/.035),0,0))
  armik.solve(rig,side,target,pole=pole,hand_rot=M.to_3x3())
def hinge_elbows():
 for side in 'LR':
  u=f'B_{side}_UpperArm';f=f'B_{side}_Forearm';h=f'B_{side}_Hand'
  U,F,H=[armik.W(rig,n) for n in [u,f,h]];axis=(U.to_3x3()@Vector((0,0,-1))).normalized();direction=H.translation-F.translation
  projected=direction-axis*direction.dot(axis)
  q=direction.rotation_difference(projected)
  armik.set_world(rig,f,armik.rot_world(F,q.to_matrix()@F.to_3x3()));armik.set_world(rig,h,armik.rot_world(armik.W(rig,h),H.to_3x3()))
# Soles use the fitted boot surface, with the ankle-to-toe direction as anatomical forward.
sole={}
for side in 'LR':
 foot=rig.data.bones[f'B_{side}_Foot'];toe=rig.data.bones[f'B_{side}_Toe0'];inv=foot.matrix_local.inverted()
 ids=[v.index for v in body.data.vertices if v.co.z<.009 and any(g.group==body.vertex_groups[foot.name].index and g.weight>.5 for g in v.groups)]
 assert len(ids)>=3,(side,len(ids));sole[side]=[inv@body.data.vertices[i].co for i in ids]
def plant(mode):
 for side in 'LR':
  fn=f'B_{side}_Foot';M=armik.W(rig,fn);bone=rig.data.bones[fn];rest=bone.matrix_local
  points=[M@v for v in sole[side]];low=min(v.z for v in points)
  weight=1.0 if mode=='rest' else float(np.clip((.12-low)/.10,0,1))
  normal=M.to_3x3()@rest.to_3x3().inverted()@Vector((0,0,1))
  q=normal.rotation_difference(Vector((0,0,1)));R=q.to_matrix()@M.to_3x3()
  points=np.array([rest@v for v in sole[side]]);along=-points[:,1];forward=R@rest.to_3x3().inverted()@Vector(points[along>=np.quantile(along,.7)].mean(0)-points[along<=np.quantile(along,.3)].mean(0))
  yaw=math.atan2(forward.x,-forward.y);R=Matrix.Rotation(-yaw,3,'Z')@R
  # The upright boot retains a small toe-off while airborne.
  R=R
  local=sole[side];target=M.translation.copy();height=min((R@v+target).z for v in local)
  if mode=='rest':target.z+=.004-height
  else:target.z+=max(.004,min(.124,height))-height
  leg(side,target,R)
  rig.pose.bones[f'B_{side}_Toe0'].rotation_quaternion=Quaternion()
 bpy.context.view_layer.update()
# Calibrate the source stance to the real soles, then close the locomotion cycles.
for name in ['Standing','Walking','Running','Fidget']:
 a=bpy.data.actions[name];end=int(a.frame_range[1]);frames=[]
 initial=sample(a,0);initial_world=armik.W(rig,'B_Pelvis').translation.copy()
 for f in range(end+1):
  pose=sample(a,f);apply(pose)
  m=armik.W(rig,'B_Pelvis');m.translation.x-=initial_world.x;m.translation.y-=initial_world.y;armik.set_world(rig,'B_Pelvis',m)
  free_arms()
  if name=='Walking':
   for side in 'LR':
    hn=f'B_{side}_Hand';H=armik.W(rig,hn);wr=rig.data.bones[hn].head_local;k1=rig.data.bones[f'B_{side}_Finger1'].head_local;k4=rig.data.bones[f'B_{side}_Finger4'].head_local
    n=(k1-wr).cross(k4-wr).normalized()*(1 if side=='R' else -1);normal=H.to_3x3()@rig.data.bones[hn].matrix_local.to_3x3().inverted()@n
    origin=(H.translation+sum((armik.W(rig,f'B_{side}_Finger{i}').translation for i in range(5)),Vector())/5)/2
    goal=armik.W(rig,f'B_{side}_Thigh').translation-origin;goal.z=0;q=normal.rotation_difference(goal)
    R=Quaternion().slerp(q,.35).to_matrix()@H.to_3x3();armik.set_world(rig,hn,armik.rot_world(H,R))
  plant('rest' if name in ['Standing','Fidget'] else 'gait');floor();frames.append(current())
 # Native held idle and source cycles share one exact endpoint.
 frames[-1]=frames[0];write(name,frames)
stand=sample(bpy.data.actions['Standing'],0);apply(stand)
feet={s:armik.W(rig,f'B_{s}_Foot').copy() for s in 'LR'};pelvis=armik.W(rig,'B_Pelvis').translation.copy()
rest_hands={side:armik.W(rig,f'B_{side}_Hand').copy() for side in 'LR'}
# Add the source reaction to the relaxed stance; its raised guard is not part of the native Cyclops.
a=bpy.data.actions['Hit'];start=sample(a,0);end=a.frame_range[1];frames=[]
for f in range(20):
 u=f/19;src=sample(a,u*end);gain=.6*smooth(u/.18)*smooth((1-u)/.22)
 pose={n:((src[n][0]@start[n][0].inverted()@stand[n][0]).slerp(stand[n][0],1-gain),stand[n][1].copy()) for n in names}
 for n in names:
  if any(x in n for x in ['Clavicle','UpperArm','Forearm','Hand']):pose[n]=stand[n]
 apply(pose)
 free_arms(-.035+.06*math.sin(math.pi*u))
 plant('rest');floor();frames.append(current())
write('Hit',frames)
# Keep the selected heavy backward collapse; anchor its start and retain the displacement needed for the fall.
a=bpy.data.actions['Death'];end=a.frame_range[1];start=sample(a,0);apply(start);startpos=armik.W(rig,'B_Pelvis').translation.copy();frames=[]
for f in range(79):
 u=f/78;source_pose=sample(a,u*end);pose=blend(stand,source_pose,smooth(u/.07))
 apply(pose)
 m=armik.W(rig,'B_Pelvis');m.translation.x-=startpos.x;m.translation.y-=startpos.y;armik.set_world(rig,'B_Pelvis',m);floor();frames.append(current())
for _ in range(3):
 old=frames;frames=[old[0]]+[blend(old[i],blend(old[i-1],old[i+1],.5),.5) for i in range(1,len(old)-1)]+[old[-1]]
for i,pose in enumerate(frames):
 if i==0:frames[i]=stand;continue
 apply(pose)
 chest=armik.W(rig,'B_Spine2').to_3x3()@rig.data.bones['B_Spine2'].matrix_local.to_3x3().inverted()
 for side,sign in [('L',-1),('R',1)]:
  turn(f'B_{side}_UpperArm',chest@Vector((0,1,0)),sign*20*smooth(i/2)*(1-smooth((i/30-.10)/.30)))
 hinge_elbows();floor()
 m=armik.W(rig,'B_Pelvis');m.translation.z+=.008*smooth(i/12);armik.set_world(rig,'B_Pelvis',m);frames[i]=current()
write('Death',frames);write('Dead',[frames[-1],frames[-1]])
# The throw keeps source torso timing, with a native pickup and shared two-hand contact path.
source=bpy.data.actions['AttackSource'];fj=json.loads((p/'work/finger_joints.json').read_text());hand={}
for side in 'LR':
 h=rig.data.bones[f'B_{side}_Hand'];wr=h.head_local;R=h.matrix_local.to_3x3()
 f=(Vector(fj[side][f'B_{side}_Finger2'])-wr).normalized();t=Vector(fj[side][f'B_{side}_Finger1'])-Vector(fj[side][f'B_{side}_Finger4']);t=(t-f*t.dot(f)).normalized();B=Matrix((f,t,f.cross(t))).transposed()
 # Wrist-to-palm centre measured on the four knuckles, kept in hand local space.
 kn=sum((Vector(fj[side][f'B_{side}_Finger{i}']) for i in range(1,5)),Vector())/4
 hand[side]={'basis':R.inverted()@B,'palm':R.inverted()@((kn-wr)*.65)}
selected=json.loads((p/'work/selected_grip.json').read_text());grip_matrices={side:Matrix(selected['hands'][side]['matrix']) for side in 'LR'}
frames=[];path=[];reaches=[];wrists=[];records=[]
rockkeys=[(0,[0,-.35,1.2]),(.23,[0,-.35,.85]),(.38,[0,-.42,1.2]),(.60,[0,-.45,1.66]),(.84,[0,-.35,2.60]),(.86,[0,-.35,2.60]),(1.0,[0,-.62,2.30]),(1.15,[0,-.8,1.5]),(1.6,[0,-.55,.8])]
for frame in range(97):
 t=frame/60;sf=float(np.interp(t,[0,.23,.38,.60,.82,.91,1,1.15,1.6],[0,0,0,28,40,45,49,55,83]));src=sample(source,sf)
 for n in names:
  if any(n==f'B_{s}_{b}' for s in 'LR' for b in ['Thigh','Calf','Foot','Toe0','UpperArm','Forearm','Hand']) or n in ['B_Pelvis','B_L_Clavicle','B_R_Clavicle']:src[n]=stand[n]
 gain=smooth(t/.15)*smooth((1.6-t)/.35);pose=blend(stand,src,gain)
 for side in 'LR':
  n=f'B_{side}_Clavicle';pose[n]=(pose[n][0].slerp(Quaternion(),.8*gain),pose[n][1])
 for n in ['B_Spine','B_Spine1','B_Spine2','B_Neck','B_Head']:
  amount=.25;pose[n]=(stand[n][0].slerp(pose[n][0],amount),pose[n][1])
 apply(pose)
 crouch=float(curve([(0,0),(.23,1),(.38,.6),(.6,0),(1.1,.15),(1.6,0)],t))
 m=armik.W(rig,'B_Pelvis');m.translation=pelvis+Vector((0,.10*crouch,-.55*crouch));armik.set_world(rig,'B_Pelvis',m)
 turn('B_Spine',(1,0,0),32*crouch)
 for s in 'LR':leg(s,feet[s].translation,feet[s].to_3x3())
 centre=Vector(curve(rockkeys,t));centre.y-=.14*smooth(t/.23)*smooth((.78-t)/.18)
 rock_rotation=Matrix.Rotation(math.radians(float(curve([(0,50),(.23,50),(.4,0),(.6,0),(.82,-50),(.86,-50),(1,-20),(1.6,0)],t))),3,'X')
 rock_rotation=Matrix.Rotation(math.radians(20*smooth((centre.z-1.8)/.8)),3,'X')@rock_rotation
 for side,sign in [('L',-1),('R',1)]:turn(f'B_{side}_Clavicle',(0,1,0),sign*30*smooth((centre.z-1.8)/.8))
 for side,sign in [('L',-1),('R',1)]:turn(f'B_{side}_Clavicle',(0,0,1),sign*0*smooth((centre.z-1.8)/.8))
 grip=smooth((t-.02)/.25)
 angle=float(curve([(0,0),(.23,0),(.38,-90),(.60,-180),(.91,-180),(1,-140),(1.12,-100),(1.6,0)],t))
 carry={}
 for side in 'LR':
  M=grip_matrices[side];carry[side]={'target':centre+rock_rotation@(M.translation-Vector(selected['centre'])),'rotation':rock_rotation@M.to_3x3()}
  for n,q in selected['hands'][side]['fingers'].items():rig.pose.bones[n].rotation_quaternion=Quaternion().slerp(Quaternion(q),grip)
 bpy.context.view_layer.update()
 records.append({'pose':current(),'centre':centre.copy(),'grip':grip,'angle':angle,'carry':carry,'endpoint':frame==0,'approach':smooth(t/.04)*(1-grip)})
 path.append({'frame':frame,'centre':list(centre),'visible':.28<=t<1.0,'grip_weight':grip,'rotation':list(rock_rotation.to_quaternion())})
from fit_boulder_arms import fit
release=records[59];apply(stand);standing_hands={side:armik.W(rig,f'B_{side}_Hand').copy() for side in 'LR'}
for f in range(60,97):
 u=(f-59)/37;pose=blend(release['pose'],stand,smooth(u));carry={}
 for side,sign in [('L',1),('R',-1)]:
  A=release['carry'][side];B=standing_hands[side];target=A['target'].lerp(B.translation,smooth(u))
  target.x+=sign*.08*math.sin(math.pi*u);target.y-=.08*math.sin(math.pi*u)
  H=A['rotation'].to_quaternion().slerp(B.to_quaternion(),smooth(u)).to_matrix()
  carry[side]={'target':target,'rotation':H}
 records[f]=dict(records[f],pose=pose,carry=carry,grip=1.,pole_grip=1-smooth(u),relax_hand=smooth(u/.4),endpoint=f==96)
chosen=fit(rig,records,hand,apply);frames=[];reaches=[];wrists=[]
for record_index,record in enumerate(records):
 apply(record['pose'])
 for side in 'LR':
  target,H,pole,reach,metrics=chosen[side][record_index]
  armik.solve(rig,side,target,pole=pole,hand_rot=H)
  reaches.append(reach);wrists.append(armik.wrist_cost(rig,side,H))
 low=floor();path[record_index]['centre'][2]+=.004-low;frames.append(current())
write('Attack',frames,rate=60)
# Source helper actions never enter the exported clip set.
for name in ['AttackSource']:
 if name in bpy.data.actions:bpy.data.actions.remove(bpy.data.actions[name])
(p/'work/boulder_path.json').write_text(json.dumps(path,indent=2))
report={'arm_search_max':{k:max(row[4][k] for side in 'LR' for row in chosen[side]) for k in ['swing','twist','upper_roll']},'chosen_frames':{side:[row[4] for row in chosen[side]] for side in 'LR'},'attack_release_seconds':1.0,'attack_duration_seconds':1.6,'attack_reach_max':max(reaches),'wrist_swing_max_degrees':max(v[0] for v in wrists),'wrist_twist_max_degrees':max(abs(v[1]) for v in wrists),'hit_seconds':19/30,'death_seconds':2.6,'clips':{a.name:(a.frame_range[1]-a.frame_range[0])/30 for a in bpy.data.actions if a.use_fake_user}}
print('MOTION',report,flush=True);(p/'work/motion_fit.json').write_text(json.dumps(report,indent=2));action(None)
for pb in rig.pose.bones:pb.matrix_basis.identity();pb.scale=(1,1,1)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/motion_fitted.blend'))
# Temporary ellipsoid shows two-hand contact while the reference-derived prop is being generated.
bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12);rock=bpy.context.object;rock.name='BoulderProxy';rock.scale=(.29,.20,.19)
common.workbench_clay(scene)
for i,f in enumerate([0,7,12,18,24,27,30,34,40,48]):
 a=bpy.data.actions['Attack'];action(a);scene.frame_set(f);rock.location=Vector(path[f*2]['centre']);rock.rotation_mode='QUATERNION';rock.rotation_quaternion=path[f*2]['rotation'];rock.hide_render=not path[f*2]['visible']
 common.render_views(str(p/f'review/fitted_Attack_{i:02}'),1.4,3.1,views=('front','left'),resolution=(500,700))
