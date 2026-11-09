"""User-selected two-handed overhead chop, fitted to the existing closed body and axe."""
import bpy,json,math,sys
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import armik,common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/pilots_cloth_onehand_v1.blend'));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];sc=bpy.context.scene;sc.render.fps=30;names=list(r.pose.bones.keys())
G={s:json.loads((P/f'work/grip_pose_{s}.json').read_text()) for s in 'RL'};SG=json.loads((P/'work/grip_source.json').read_text())
def act(a):
 r.animation_data.action=a
 if a and len(a.slots):r.animation_data.action_slot=a.slots[0]
def update():bpy.context.view_layer.update()
def snap():return {n:r.pose.bones[n].matrix_basis.copy() for n in names}
def apply(row):
 act(None)
 for n,m in row.items():r.pose.bones[n].matrix_basis=m
 update()
def world(n):return armik.W(r,n).copy()
def blend(a,b,t):
 m=a.to_quaternion().slerp(b.to_quaternion(),t).to_matrix().to_4x4();m.translation=a.translation.lerp(b.translation,t);return m
act(bpy.data.actions['Standing']);sc.frame_set(0);home=snap();H0={s:world(f'B_{s}_Hand') for s in 'RL'};C0=H0['R']@Vector(G['R']['handle_centre_hand_local']);A0=(H0['R'].to_3x3()@Vector(G['R']['handle_axis_hand_local'])).normalized();AM0=world('Axe')@r.data.bones['Axe'].matrix_local.inverted();localX=H0['R'].to_3x3().inverted()@AM0.to_3x3().col[0];SPACE=.34;GRIP_Z=.24
with bpy.data.libraries.load(str(P/'work/twohand_source.blend'),link=False) as (src,dst):dst.actions=['AttackTwoHandSource']
a=dst.actions[0];a.use_fake_user=True;N=round(a.frame_range[1]);raw=[];times=np.arange(0,N+.01,.5)
for f in times:
 apply(home);act(a);sc.frame_set(int(f),subframe=f%1);raw.append(snap())
# Fit the source's overhead chamber/chop envelope around the bull's horns and short arms.
# The upper hand slides 12 cm down the handle during the chamber without releasing its grip.
knots=[(0,C0,A0),(8,Vector((-.34,-.53,1.32)),Vector((.72,.12,.68))),
 (16,Vector((-.32,-.48,1.53)),Vector((.75,.05,.66))),
 (21,Vector((-.30,-.50,1.48)),Vector((.70,0,.71))),
 (25,Vector((-.12,-.40,1.10)),Vector((.25,-.95,-.19))),
 (30,Vector((-.16,-.32,.95)),Vector((.45,-.75,-.48))),
 (38,Vector((-.20,-.42,1.0)),Vector((.75,-.45,.48))),(51,C0,A0)]
path=np.array([[*c,*a.normalized()] for _,c,a in knots]);tt=np.array([f for f,_,_ in knots]);vv=np.stack([np.interp(times,tt,path[:,k]) for k in range(6)],1)
for k in range(6):vv[:,k]=np.convolve(np.pad(vv[:,k],(2,2),mode='edge'),np.array([1,4,6,4,1])/16,mode='valid')
vv[0]=path[0];vv[-1]=path[-1];apply(home);homeSpine=world('B_Spine');frames=[]
for i,row in enumerate(raw):
 f=float(times[i]);t=min(1,f/9,(N-f)/11);t=max(0,t);edge=t*t*(3-2*t);apply(row);srcSpine=world('B_Spine')
 pose={n:blend(home[n],row[n],edge*.35) if any(k in n for k in ['Spine','Clavicle','Neck','Head']) else home[n].copy() for n in names}
 for n in names:
  if any(k in n for k in ['UpperArm','Forearm','Hand','Finger']):pose[n]=home[n].copy()
 apply(pose);m=blend(homeSpine,srcSpine,edge*.30);m.translation=world('B_Spine').translation;armik.set_world(r,'B_Spine',m)
 for sd,angle in [('R',.40),('L',-.25)]:
  n=f'B_{sd}_Clavicle';m=world(n);pos=m.translation.copy();m=Matrix.Rotation(angle*float(np.interp(f,[0,8,22,30,N],[0,1,1,0,0])),4,'Y')@m;m.translation=pos;armik.set_world(r,n,m)
 for n,angle in [('B_Neck',-.12),('B_Head',-.25)]:
  m=world(n);pos=m.translation.copy();m=Matrix.Rotation(angle*float(np.interp(f,[0,8,22,30,N],[0,1,1,0,0])),4,'X')@m;m.translation=pos;armik.set_world(r,n,m)
 C=Vector(vv[i,:3]);A=Vector(vv[i,3:]).normalized();frames.append({'snap':snap(),'C':C,'dir':A,'edge':edge,'spacing':SPACE-.12*float(np.interp(f,[0,20,25,35,44,N],[0,0,1,1,0,0]))})
print('PATH',[(i,[round(x,3) for x in f['C']],[round(x,3) for x in f['dir']]) for i,f in enumerate(frames) if i%5==0],flush=True)
ng=[g.name for g in b.vertex_groups];pv=np.array([v.value for v in b.data.attributes['piece'].data]);aw=np.array([sum(g.weight for g in v.groups if any(k in ng[g.group] for k in ['UpperArm','Forearm','Hand','Finger'])) for v in b.data.vertices]);targets=[tuple(f.vertices) for f in b.data.polygons if all(pv[i] in [0,1] and aw[i]<.15 for i in f.vertices)]
rest=np.array([(*v.co,1.) for v in b.data.vertices]);weights=np.zeros((len(rest),len(ng)))
for v in b.data.vertices:
 for g in v.groups:weights[v.index,g.group]=g.weight
shoulder={sd:np.where((aw>.7)&(rest[:,0]*sgn>.33)&(rest[:,0]*sgn<.48)&(pv==0))[0] for sd,sgn in [('R',-1),('L',1)]}
invrest={n:r.data.bones[n].matrix_local.inverted() for n in ng}
def posed_tree():
 ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();tree=BVHTree.FromPolygons([v.co[:] for v in me.vertices],targets);ev.to_mesh_clear();return tree
def avoid_body(rig,sd,fr):
 S,E,H=[world(f'B_{sd}_{n}').translation for n in ['UpperArm','Forearm','Hand']];worst=0.;total=0.
 for aa,bb,steps,radius in [(S,E,np.linspace(.55,1,5),.10),(E,H,np.linspace(0,1,9),(.105 if sd=='R' else .095))]:
  for t in steps:
   pt=aa.lerp(bb,float(t));loc,n,fi,dist=fr['tree'].find_nearest(pt,.16)
   if loc is not None:
    signed=dist if (pt-loc).dot(n)>0 else -dist;penetration=max(0,radius-signed);worst=max(worst,penetration);total+=penetration
 ids=shoulder[sd];points=np.zeros((len(ids),3))
 for j,n in enumerate(ng):
  if np.any(weights[ids,j]):points+=(rest[ids]@np.array(r.pose.bones[n].matrix@invrest[n]).T)[:,:3]*weights[ids,j,None]
 skin_depth=0.
 for p in points:
  loc,n,fi,dist=fr['tree'].find_nearest(Vector(p),.08)
  if loc is not None and (Vector(p)-loc).dot(n)<-.7*dist:skin_depth=max(skin_depth,dist)
 return 4500*worst+800*total+80000*skin_depth
fit=[f['snap'] for f in frames];report={}
for sd in 'RL':
 axis=Vector(G[sd]['handle_axis_hand_local']);centre=Vector(G[sd]['handle_centre_hand_local']);af=[]
 for i,fr in enumerate(frames):
  apply(fit[i]);C=fr['C']+(fr['dir']*fr['spacing'] if sd=='L' else Vector());R,_,_,_=armik.hand_for_axis(r,sd,axis,fr['dir']);af.append({'snap':snap(),'wrist':C-R@centre,'dir':fr['dir'],'centre':C,'edge':fr['edge'],'tree':posed_tree()})
 path=armik.arm_dp(r,sd,af,axis,phis=range(-180,181,10),psis=range(0,360,10),k_twist=.6,k_dphi=1,k_dpsi=.8,pose_cost=avoid_body)
 for key in ['phi','psi']:
  v=np.unwrap(np.radians([x[key] for x in path]));v=np.convolve(np.pad(v,(3,3),mode='edge'),np.array([1,6,15,20,15,6,1])/64,mode='valid')
  for row,x in zip(path,np.degrees(v)):row[key]=float(x)
 vals=[]
 for i,(fr,ch) in enumerate(zip(af,path)):
  d=fr['dir'];targetR=A0.rotation_difference(d).to_matrix()@H0[sd].to_3x3();up=Vector((0,0,1));e=(up-d*up.dot(d)).normalized();fl=Vector((0,1,0))-axis*axis.y;fl.normalize();fw=targetR@fl;goal=math.degrees(math.atan2(fw.dot(d.cross(e)),fw.dot(e)));psi=goal+((ch['psi']-goal+180)%360-180)*fr['edge'];phi=(ch['phi']+(10*math.exp(-((float(times[i])-4)/2.5)**2) if sd=='R' else 0))*min(1,float(times[i])/2,(N-float(times[i]))/2);R=armik.hand_rot(axis,d,psi);sw,tw=armik.apply_arm(r,sd,fr['snap'],fr['centre']-R@centre,axis,d,phi,psi)
  for n,q in G[sd]['finger_local'].items():r.pose.bones[n].rotation_mode='QUATERNION';r.pose.bones[n].rotation_quaternion=Quaternion(q).slerp(Quaternion(G[sd]['open_finger_local'][n]),.025*fr['edge'])
  update();fit[i]=snap();error=(world(f'B_{sd}_Hand')@centre-fr['centre']).length;vals.append((sw,tw,error))
  if sd=='R':frames[i]['C']=world('B_R_Hand')@centre
 print('PHI',sd,[(round(float(times[k]),1),round(p['phi'],1)) for k,p in enumerate(path) if k%8==0],flush=True)
 report[sd]={'wrist_swing_max_deg':max(v[0] for v in vals),'twist_range_deg':[min(v[1] for v in vals),max(v[1] for v in vals)],'path_reach_adjustment_m' if sd=='R' else 'grip_error_m':max(v[2] for v in vals)};print('FIT',sd,report[sd],flush=True)
bpy.data.actions.remove(bpy.data.actions['Attack']);a=bpy.data.actions.new('Attack');a.use_fake_user=True;last={}
for i,row in enumerate(fit):
 f=float(times[i]);apply(row)
 for sd in 'RL':
  fb=r.data.bones[f'B_{sd}_Forearm'];hb=r.data.bones[f'B_{sd}_Hand'];ub=r.data.bones[f'B_{sd}_UpperArm'];axis=(fb.matrix_local.inverted()@hb.head_local).normalized();dq=(r.pose.bones[fb.name].matrix.inverted()@r.pose.bones[hb.name].matrix).to_quaternion()@(fb.matrix_local.inverted()@hb.matrix_local).to_quaternion().inverted();_,tw=armik.split_swing_twist(dq,axis);r.pose.bones[f'B_{sd}_ForearmTwist'].rotation_mode='QUATERNION';r.pose.bones[f'B_{sd}_ForearmTwist'].rotation_quaternion=Quaternion(axis,.5*tw)
  axis=(ub.matrix_local.inverted()@fb.head_local).normalized();_,tw=armik.split_swing_twist(r.pose.bones[ub.name].matrix_basis.to_quaternion(),axis);r.pose.bones[f'B_{sd}_UpperArmTwist'].rotation_mode='QUATERNION';r.pose.bones[f'B_{sd}_UpperArmTwist'].rotation_quaternion=Quaternion(axis,-.5*tw)
 update();H=world('B_R_Hand');C=H@Vector(G['R']['handle_centre_hand_local']);A=(H.to_3x3()@Vector(G['R']['handle_axis_hand_local'])).normalized();X=H.to_3x3()@localX;X=(X-A*X.dot(A)).normalized();X=Quaternion(A,math.radians(-45)*float(np.interp(f,[0,12,18,31,40,N],[0,0,1,1,0,0])))@X;Y=A.cross(X);m=Matrix((X,Y,A)).transposed().to_4x4();m.translation=C-A*GRIP_Z;r.pose.bones['Axe'].matrix=m@r.data.bones['Axe'].matrix_local;update();act(a)
 for n in names:
  pb=r.pose.bones[n];q=pb.matrix_basis.to_quaternion()
  if n in last and q.dot(last[n])<0:q=-q
  last[n]=q.copy();pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q;pb.scale=(1,1,1);pb.keyframe_insert('rotation_quaternion',frame=f)
  if n in ['B_Pelvis','Axe'] or n.startswith('Skirt_'):pb.keyframe_insert('location',frame=f)
 act(None)
a.use_frame_range=True;a.frame_start=0;a.frame_end=N
for lay in a.layers:
 for st in lay.strips:
  for cb in st.channelbags:
   for fc in cb.fcurves:
    for k in fc.keyframe_points:k.interpolation='LINEAR'
bpy.data.actions.remove(bpy.data.actions['AttackTwoHandSource']);act(a);sc.frame_set(0);bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/pilots_cloth.blend'));(P/'review/twohand_fit.json').write_text(json.dumps(report,indent=2));common.workbench_clay(sc)
for i,f in enumerate([0,8,16,23,28,34,42,51]):
 sc.frame_set(f);common.render_views(str(P/f'review/twohand_{i}'),1.1,3.6,views=('front','left','three_quarter'),resolution=(340,480))
