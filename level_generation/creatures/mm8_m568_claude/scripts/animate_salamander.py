"""Native Salamander motion: fixed-length serpent, measured two-hand grips and released death prop."""
import bpy,bmesh,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_uv.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
D=json.loads((P/'work/rig.json').read_text());G=json.loads((P/'work/grip_pose.json').read_text());B=D['bones'];J0=np.array(D['tail']['joints']);K=D['tail']['root_index'];L=np.linalg.norm(np.diff(J0,axis=0),axis=1)
R={n:rig.data.bones[n].matrix_local.copy() for n in B};REL={n:R[b['parent']].inverted()@R[n] if b['parent'] else R[n] for n,b in B.items()}
FPS=48;sc.render.fps=FPS
DUR={'Standing':3.,'Walk':1.,'Running':.75,'Fidget':.625,'Attack':4/3,'Cast':1.25,'Hit':.625,'Death':.75,'Dead':1.}
def norm(v):return v/max(np.linalg.norm(v),1e-9)
def ss(x):x=np.clip(x,0,1);return float(x*x*(3-2*x))
def env(t,a,b,c):return ss((t-a)/(b-a))*(1-ss((t-b)/(c-b)))
def mat(rot,p):m=rot.to_4x4();m.translation=Vector(p);return m
def frame(a,n):
 a=norm(np.array(a));n=norm(np.array(n)-a*np.dot(n,a));return Matrix(np.column_stack([a,n,np.cross(a,n)]))
# One native forked polearm, with geometry only where it changes the silhouette.
materials=[]
for name,color in [('Shaft',(.045,.035,.025,1)),('Steel',(.45,.48,.51,1)),('Wrap',(.06,.48,.08,1))]:
 m=bpy.data.materials.new('Polearm'+name);m.diffuse_color=color;materials.append(m)
objects=[]
def cylinder(radius,lo,hi,material):
 bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=radius,depth=hi-lo,location=(0,0,(lo+hi)/2));o=bpy.context.object;o.data.materials.append(material);objects.append(o)
cylinder(.014,-1.12,.78,materials[0])
for z in [-.25,.25]:cylinder(.018,z-.10,z+.10,materials[2])
cylinder(.024,.68,.79,materials[1]);cylinder(.019,-1.14,-1.10,materials[1])
outline=[(-.045,.72),(-.15,.79),(-.19,.97),(-.09,.88),(-.065,.82),(-.031,.91),(0,1.20),(.031,.91),(.065,.82),(.09,.88),(.19,.97),(.15,.79),(.045,.72)]
verts=[(x,y,z) for y in [-.012,.012] for x,z in outline];n=len(outline);faces=[tuple(range(n-1,-1,-1)),tuple(range(n,n*2))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
me=bpy.data.meshes.new('Fork');me.from_pydata(verts,[],faces);me.materials.append(materials[1]);o=bpy.data.objects.new('Fork',me);sc.collection.objects.link(o);objects.append(o)
bm=bmesh.new();bm.from_mesh(me);bmesh.ops.triangulate(bm,faces=list(bm.faces));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
bpy.ops.object.select_all(action='DESELECT')
for o in objects:o.select_set(True)
bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();weapon=bpy.context.object;weapon.name=weapon.data.name='PolearmMesh';bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
wg=weapon.vertex_groups.new(name='Polearm');wg.add(list(range(len(weapon.data.vertices))),1.,'REPLACE');mod=weapon.modifiers.new('RigidPolearm','ARMATURE');mod.object=rig;weapon.parent=rig
# A rigid socket at the central tip is used by the existing cast/projectile binding.
socket=bpy.data.objects.new('Socket_Polearm_Tip',None);sc.collection.objects.link(socket);socket.parent=rig;socket.parent_type='BONE';socket.parent_bone='Polearm';socket.matrix_parent_inverse=Matrix.Translation((0,-rig.data.bones['Polearm'].length,0));socket.location=R['Polearm'].inverted()@Vector((0,0,1.20))
C0=np.array([-.04,-.35,1.38]);A0=norm(np.array([-.83,-.12,.545]))
def pose(role,t):
 if role=='Dead':role,t='Death',DUR['Death']
 phase=2*math.pi*t/DUR[role];gait=role in ['Walk','Running'];fall=ss((t-.15)/.53) if role=='Death' else 0.;hit=env(t,0,.17,.625) if role=='Hit' else env(t,0,.11,.28)*.55 if role=='Death' else 0.
 wind=env(t,0,.40,.78) if role=='Attack' else 0.;strike=env(t,.48,1.,4/3) if role=='Attack' else 0.;cast=env(t,0,1.,1.25) if role=='Cast' else 0.;fidget=env(t,0,.31,.625) if role=='Fidget' else 0.
 pitch=.012*math.sin(phase) if role=='Standing' else -.20*hit-.13*wind-.15*strike
 wave=(.52 if role=='Running' else .38) if gait else .025
 pts=J0.copy()
 for i in list(range(K-1,-1,-1))+list(range(K,len(L))):
  up=i<K;d=Vector(J0[i]-J0[i+1] if up else J0[i+1]-J0[i]);d.normalize();u=(K-i)/K if up else (i-K)/(len(L)-K)
  if up:
   yaw=(.045*math.sin(phase-u*3) if gait else 0)+fall*1.15*u
   d=Matrix.Rotation(yaw,3,'Y')@Matrix.Rotation(pitch*u-fall*1.42*(.5+.5*u),3,'X')@d;d.z*=1-fall;d.normalize();nxt=pts[i+1]+L[i]*np.array(d)
   if fall and nxt[2]<.17:
    dz=np.clip(.17-pts[i+1,2],-L[i]*.95,L[i]*.95);nxt=pts[i+1]+norm(np.array([d.x,d.y,0]))*math.sqrt(L[i]**2-dz**2)+[0,0,dz]
   pts[i]=nxt
  else:
   yaw=wave*math.sin(phase-u*5)*(.25+.75*u)+fall*.55*u
   d=Matrix.Rotation(yaw,3,'Z')@d
   curl=(.22*strike+.17*hit)*u*u;d=Matrix.Rotation(curl,3,'X')@d;pts[i+1]=pts[i]+L[i]*np.array(d)
 M={'Root':R['Root'].copy()};M['Root'].translation=Vector(pts[K])
 for i in range(len(L)):
  n=f'Serpent_{i:02d}';a,b=(pts[i+1],pts[i]) if i<K else (pts[i],pts[i+1]);old=Vector(np.array(B[n]['tail'])-np.array(B[n]['head']));M[n]=mat(old.rotation_difference(Vector(b-a)).to_matrix()@R[n].to_3x3(),a)
 for n,b in B.items():
  if n in M:continue
  m=M[b['parent']]@REL[n]
  if n in ['B_Spine','B_Spine1','B_Spine2','B_Neck','B_Head']:
   angle=(-.045*hit-.025*wind) if n.startswith('B_Spine') else .05*hit+.035*strike if n=='B_Head' else 0
   carry=M['B_Pelvis'].to_3x3()@R['B_Pelvis'].to_3x3().transposed()
   if angle:m=mat(carry@Matrix.Rotation(angle,3,'X')@carry.transposed()@m.to_3x3(),m.translation)
  M[n]=m
 carrier=M['B_Spine2']@R['B_Spine2'].inverted();cr=carrier.to_3x3()
 axis=norm(A0+np.array([.20*wind+.60*strike+.70*fidget+.55*hit+.5*cast,.12*strike+.04*cast+.20*fidget,.4*wind+.55*strike+.6*fidget+.65*hit+.4*cast]))
 center=C0+np.array([-.15*fidget,-.04*wind-.09*strike-.06*hit-.12*cast-.12*fidget-.08*math.sin(math.pi*fidget),.13*wind+.33*strike+.16*fidget+.34*hit+.28*cast])
 if gait:center+=np.array([0,.018*math.sin(phase),.012*math.cos(phase)])
 wc=np.array(carrier@Vector(center));wa=norm(np.array(cr@Vector(axis)))
 held_wc=wc.copy();held_wa=wa.copy()
 release=ss((t-.24)/.36) if role=='Death' else 0
 if release:
  wc=(1-release)*wc+release*np.array([-1.05,-.70,.04])+np.array([-.20*math.sin(math.pi*release),-.65*math.sin(math.pi*release),0]);wa=norm((1-release)*wa+release*np.array([-.6,-.8,0]))
 px=norm(np.cross([0,1,0],wa))
 if np.linalg.norm(px)<.1:px=np.array([1.,0,0])
 proprot=Matrix(np.column_stack([px,np.cross(wa,px),wa]));M['Polearm']=mat(proprot@R['Polearm'].to_3x3(),wc)
 errors=[];twists=[]
 for sd,sgn in [('L',1),('R',-1)]:
  un,fn,tn,hn=['B_'+sd+'_'+x for x in ['UpperArm','Forearm','ForearmTwist','Hand']];grip=G[sd]
  ar=R[hn].to_3x3()@Vector(grip['handle_axis_hand_local']);nr=R[hn].to_3x3()@Vector(grip['palm_normal_hand_local'])
  desirednormal=np.array(cr@Vector((0,1 if sd=='L' else -1,0)));hr=frame(held_wa,desirednormal)@frame(ar,nr).transposed()@R[hn].to_3x3()
  contact=held_wc+held_wa*(.25 if sd=='R' else -.25);target=Vector(contact)-hr@Vector(grip['handle_centre_hand_local'])
  free=fidget if sd=='L' else 0
  free=max(free,release)
  if free:
   resttarget=Vector((sgn*(.75 if release else .47),.10 if release else -.18,1.98 if not release else 1.32));target=target.lerp(carrier@resttarget,free);hr=hr.to_quaternion().slerp((cr@R[hn].to_3x3()).to_quaternion(),free).to_matrix()
  shoulder=np.array(M[un].translation);restE=Vector(B[fn]['head']);restW=Vector(B[hn]['head']);a=np.linalg.norm(np.array(restE)-B[un]['head']);b=np.linalg.norm(np.array(restW-restE));v=np.array(target)-shoulder;distance=np.linalg.norm(v);dist=np.clip(distance,abs(a-b)+.003,a+b-.002);direction=norm(v);target=Vector(shoulder+direction*dist)
  errors.append(abs(distance-dist)*(1-free))
  pole=np.array(carrier@Vector((sgn*.60,.13,1.50)))-shoulder;pole=norm(pole-direction*(pole@direction));along=(a*a-b*b+dist*dist)/(2*dist);elbow=shoulder+direction*along+pole*math.sqrt(max(0,a*a-along*along))
  for n,start,end,restend in [(un,shoulder,elbow,B[fn]['head']),(fn,elbow,np.array(target),B[hn]['head'])]:
   orig=cr@Vector(np.array(restend)-B[n]['head']);rot=orig.rotation_difference(Vector(end-start)).to_matrix()@cr@R[n].to_3x3();M[n]=mat(rot,start)
  delta=hr@R[hn].to_3x3().transposed()@(M[fn].to_3x3()@R[fn].to_3x3().transposed()).transposed();q=delta.to_quaternion();axisfore=(target-Vector(elbow)).normalized();v=Vector((q.x,q.y,q.z));amount=v.dot(axisfore);angle=2*math.atan2(amount,q.w);angle=(angle+math.pi)%(2*math.pi)-math.pi;twists.append(abs(angle))
  base=M[fn].to_3x3();M[fn]=mat(Matrix.Rotation(angle*.25,3,axisfore)@base,elbow);M[tn]=mat(Matrix.Rotation(angle*.75,3,axisfore)@base,(Vector(elbow)+target)/2);M[hn]=mat(hr,target)
  for f in range(5):
   for suffix in ['','1','2']:
    n=f'B_{sd}_Finger{f}'+suffix;quat=Quaternion(grip['finger_local'][n]);quat=Quaternion().slerp(quat,1-.75*release);M[n]=M[B[n]['parent']]@REL[n]@quat.to_matrix().to_4x4()
 for n in B:
  parent=B[n]['parent'];rig.pose.bones[n].matrix_basis=REL[n].inverted()@(M[parent].inverted()@M[n] if parent else M[n])
 bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();floor=min(v.co.z for v in me.vertices);ev.to_mesh_clear();lift=max(0,-floor)
 if lift:rig.pose.bones['Root'].location+=R['Root'].to_3x3().transposed()@Vector((0,0,lift))
 if release:
  bpy.context.view_layer.update();ev=weapon.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();low=min(v.co.z for v in me.vertices);ev.to_mesh_clear()
  if low<.018 or release>.999:
   pb=rig.pose.bones['Polearm'];world=pb.matrix.copy();world.translation.z+=.018-low;pb.matrix=world
 bpy.context.view_layer.update()
 return {'grip_error':max(errors),'forearm_twist':max(twists),'fall':fall}
C=np.array([v.co[:] for v in body.data.vertices]);E=np.array([e.vertices[:] for e in body.data.edges]);EL=np.linalg.norm(C[E[:,1]]-C[E[:,0]],axis=1);valid=EL>.001;reports={}
for old in list(bpy.data.actions):bpy.data.actions.remove(old)
for role,duration in DUR.items():
 count=round(duration*FPS);keys={n:[] for n in B};floors=[];errors=[];ratios=[];twists=[];first=last=None
 for frameidx in range(count+1):
  rig.animation_data_clear();metrics=pose(role,frameidx/FPS);errors.append(metrics['grip_error']);twists.append(metrics['forearm_twist']);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();c=np.array([v.co[:] for v in me.vertices]);ev.to_mesh_clear();first=c.copy() if first is None else first;last=c;floors.append(float(c[:,2].min()));ratio=np.linalg.norm(c[E[:,1]]-c[E[:,0]],axis=1)/np.maximum(EL,1e-8);ratios.append([float(np.percentile(ratio[valid],99)),float(ratio[valid].max())])
  for n in B:
   pb=rig.pose.bones[n];quat=pb.rotation_quaternion.copy()
   if keys[n] and quat.dot(keys[n][-1][1])<0:quat.negate()
   keys[n].append((pb.location.copy(),quat))
 action=bpy.data.actions.new(role);action.use_fake_user=True;rig.animation_data_create();rig.animation_data.action=action
 for frameidx in range(count+1):
  for n in B:
   pb=rig.pose.bones[n];pb.location,pb.rotation_quaternion=keys[n][frameidx];pb.keyframe_insert('location',frame=frameidx+1,group=n);pb.keyframe_insert('rotation_quaternion',frame=frameidx+1,group=n)
 for layer in action.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for kp in fc.keyframe_points:kp.interpolation='LINEAR'
 reports[role]={'duration':count/FPS,'min_z':min(floors),'grip_target_error':max(errors),'max_forearm_twist_degrees':math.degrees(max(twists)),'loop_delta':float(np.linalg.norm(last-first,axis=1).max()),'stretch_p99_max':np.max(ratios,axis=0).tolist()};print(role,reports[role],flush=True)
rig.animation_data.action=bpy.data.actions['Standing'];sc.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/anim_v1.blend'));(P/'work/animation_audit.json').write_text(json.dumps(reports,indent=2)+'\n')
# Full-body views at contact and recoil extremes are the pilot review, before accepting the rig.
sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.show_cavity=True;sc.display.shading.color_type='MATERIAL';sc.render.resolution_x=sc.render.resolution_y=700;sc.render.resolution_percentage=100
cam=bpy.data.objects.new('ReviewCamera',bpy.data.cameras.new('ReviewCamera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=3.8
for role,time in [('Standing',0),('Walk',.25),('Attack',.4),('Attack',1.),('Hit',.17),('Fidget',.31),('Death',.4),('Death',.75)]:
 rig.animation_data.action=bpy.data.actions[role];sc.frame_set(round(time*FPS)+1)
 for label,pos in [('front',(0,-6,2)),('side',(6,.3,2)),('quarter',(4,-6,3))]:
  target=Vector((0,.3,1.1));cam.location=pos;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(P/'review'/f'pilot_{role}_{int(time*100):02d}_{label}.png');bpy.ops.render.render(write_still=True)
