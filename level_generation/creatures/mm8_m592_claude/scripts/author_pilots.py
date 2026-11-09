"""Guardian pilots: reviewed Ogre motion deltas about the fitted hunch and native right-claw rake."""
from pathlib import Path
import bpy,sys,json,math,numpy as np
from mathutils import Matrix,Vector,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'mm6_natm_claude/scripts'));import common,armik
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_v1.blend'));scene=bpy.context.scene;rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];names=[b.name for b in rig.data.bones];rest={n:rig.data.bones[n].matrix_local.copy() for n in names};F=json.loads(scene['guardian_claws'])
scene.render.fps=30

def action(a):
 rig.animation_data_create();rig.animation_data.action=a
 if a and a.slots:rig.animation_data.action_slot=a.slots[0]
def reset():
 action(None)
 for b in rig.pose.bones:b.matrix_basis.identity()
 bpy.context.view_layer.update()
def current():return {n:(rig.pose.bones[n].rotation_quaternion.copy(),rig.pose.bones[n].location.copy()) for n in names}
def apply(pose):
 action(None)
 for n,(q,l) in pose.items():
  b=rig.pose.bones[n];b.rotation_quaternion=q;b.location=l;b.scale=(1,1,1)
 bpy.context.view_layer.update()
def write(name,poses):
 old=bpy.data.actions.get(name)
 if old:bpy.data.actions.remove(old)
 a=bpy.data.actions.new(name);a.use_fake_user=True;action(a);previous={}
 for f,pose in enumerate(poses):
  for n,(q,l) in pose.items():
   assert all(math.isfinite(x) for x in (*q,*l)),(name,f,n)
   if n in previous and q.dot(previous[n])<0:q=-q
   previous[n]=q.copy();b=rig.pose.bones[n];b.rotation_quaternion=q;b.keyframe_insert('rotation_quaternion',frame=f)
   if n=='B_Pelvis':b.location=l;b.keyframe_insert('location',frame=f)
 a.use_frame_range=True;a.frame_start=0;a.frame_end=len(poses)-1
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
 action(None)
def turn(n,axis,degrees):
 m=armik.W(rig,n);r=Quaternion(Vector(axis),math.radians(degrees)).to_matrix()@m.to_3x3().normalized();armik.set_world(rig,n,armik.rot_world(m,r))
def surface():
 ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();c=np.array([tuple(body.matrix_world@v.co) for v in me.vertices]);ev.to_mesh_clear();return c
co=np.array([tuple(v.co) for v in body.data.vertices]);foot=np.flatnonzero((co[:,2]<.12)&(abs(co[:,0])<.5))
def ground(desired=0):
 c=surface();dz=desired-float(c[foot,2].min());m=armik.W(rig,'B_Pelvis');m.translation.z+=dz;armik.set_world(rig,'B_Pelvis',m);return dz

def mean_q(qs):
 v=np.array([list(q) for q in qs]);val,vec=np.linalg.eigh(v.T@v);q=Quaternion(vec[:,-1]);return q.normalized()
before=set(bpy.data.objects);acts_before=set(bpy.data.actions);bpy.ops.import_scene.gltf(filepath=str(P.parent/'mm6_ogr_claude/export/mm6_ogr.glb'));new=set(bpy.data.objects)-before;src=next(o for o in new if o.type=='ARMATURE');meshes=[o for o in new if o.type=='MESH'];srcnames=[n for n in names if n in src.pose.bones]
source={};report={};sourcefeet={}
for ob in meshes:
 gn=[g.name for g in ob.vertex_groups]
 sourcefeet[ob.name]={sd:[v.index for v in ob.data.vertices if sum(g.weight for g in v.groups if gn[g.group] in (f'B_{sd}_Foot',f'B_{sd}_Toe0'))>.7] for sd in 'LR'}
for name in ('Walking','Running'):
 a=next(a for a in set(bpy.data.actions)-acts_before if a.name.split('|')[-1].split('@')[-1].split('.')[0]==name);src.animation_data.action=a;src.animation_data.action_slot=a.slots[0];f0,f1=a.frame_range;n=round(f1-f0);frames=[]
 for f in range(n+1):
  scene.frame_set(int(f0+f),subframe=(f0+f)%1);qs={k:(src.matrix_world@src.pose.bones[k].matrix).to_quaternion() for k in srcnames};root=(src.matrix_world@src.pose.bones['B_Pelvis'].matrix).translation.copy();zs=[]
  for ob in meshes:
   ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();zs.extend((ob.matrix_world@v.co).z for v in me.vertices);ev.to_mesh_clear()
  feet={}
  for sd in 'LR':
   low=[]
   for ob in meshes:
    ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();low.extend((ob.matrix_world@me.vertices[i].co).z for i in sourcefeet[ob.name][sd]);ev.to_mesh_clear()
   feet[sd]={'sole':min(low),'ankle':(src.matrix_world@src.pose.bones[f'B_{sd}_Foot'].matrix).translation.copy(),'knee':(src.matrix_world@src.pose.bones[f'B_{sd}_Calf'].matrix).translation.copy(),'hip':(src.matrix_world@src.pose.bones[f'B_{sd}_Thigh'].matrix).translation.copy()}
   A=feet[sd]['ankle'];T=(src.matrix_world@src.pose.bones[f'B_{sd}_Toe0'].matrix).translation;d=T-A;feet[sd]['pitch']=math.atan2(d.z,math.hypot(d.x,d.y))
  frames.append((qs,root,min(zs),feet))
 source[name]=frames
for o in new:bpy.data.objects.remove(o,do_unlink=True)
for a in set(bpy.data.actions)-acts_before:bpy.data.actions.remove(a)
reset();out={}
def leg(sd,target,pole,Rfoot):
 th,ca,ft=[f'B_{sd}_{x}' for x in ('Thigh','Calf','Foot')];H=armik.W(rig,th).translation;K=armik.W(rig,ca).translation;A=armik.W(rig,ft).translation;a=(K-H).length;b=(A-K).length;u=Vector(target)-H;distance=min(u.length,(a+b)*.999);u.normalize();v=Vector(pole);v=(v-u*v.dot(u)).normalized();c=float(np.clip((a*a+distance*distance-b*b)/(2*a*distance),-1,1));Kn=H+a*(u*c+v*math.sqrt(1-c*c))
 for bone,child,point in ((th,ca,Kn),(ca,ft,H+u*distance)):
  M=armik.W(rig,bone);old=armik.W(rig,child).translation-M.translation;R=old.normalized().rotation_difference((point-M.translation).normalized()).to_matrix()@M.to_3x3().normalized();armik.set_world(rig,bone,armik.rot_world(M,R))
 armik.set_world(rig,ft,armik.rot_world(armik.W(rig,ft),Rfoot));rig.pose.bones[f'B_{sd}_Toe0'].matrix_basis.identity();bpy.context.view_layer.update()
footids={sd:np.flatnonzero((co[:,2]<.12)&(abs(co[:,0])<.5)&(co[:,0]*(1 if sd=='L' else -1)>0)) for sd in 'LR'}
for name,frames in source.items():
 mean={n:mean_q([f[0][n] for f in frames[:-1]]) for n in srcnames};roots=np.array([tuple(f[1]) for f in frames]);rootmean=roots.mean(0);zfloor=min(fr[3][sd]['sole'] for fr in frames for sd in 'LR');scale=.65;poses=[];floor_shifts=[]
 relative={sd:np.mean([np.array(fr[3][sd]['ankle']-fr[1]) for fr in frames[:-1]],axis=0) for sd in 'LR'}
 sole0={sd:float(np.percentile([fr[3][sd]['sole'] for fr in frames[:-1]],25)) for sd in 'LR'}
 pitch0={sd:float(np.median([fr[3][sd]['pitch'] for fr in frames[:-1] if fr[3][sd]['sole']<=sole0[sd]+.01])) for sd in 'LR'}
 assert all(math.isfinite(v) for v in pitch0.values())
 for f,(qs,root,z,feet) in enumerate(frames):
  reset()
  for n in srcnames:
   d=qs[n]@mean[n].inverted();d=d.normalized()
   if d.w<0:d=-d
   factor=.55 if n in ('B_Spine','B_Spine1','B_Spine2','B_Neck','B_Head') else .85 if any(x in n for x in ('Arm','Hand','Clavicle')) else 1
   d=Quaternion().slerp(d,factor);m=armik.W(rig,n);R=d.to_matrix()@rest[n].to_3x3();m=armik.rot_world(m,R)
   if n=='B_Pelvis':m.translation=rest[n].translation+Vector((np.array(root)-rootmean)*scale)
   armik.set_world(rig,n,m)
  rig.pose.bones['Jaw'].rotation_quaternion=Quaternion((1,0,0),math.radians(-3))
  for sd in 'LR':
   for part in ('Thigh','Calf','Foot','Toe0'):rig.pose.bones[f'B_{sd}_{part}'].matrix_basis.identity()
   bpy.context.view_layer.update()
   home=rest[f'B_{sd}_Foot'].translation;delta=np.array(feet[sd]['ankle']-root)-relative[sd];pitch=feet[sd]['pitch']-pitch0[sd];pitch=float(np.clip(pitch,-math.radians(65),math.radians(35)));R=Matrix.Rotation(-pitch,3,'X')@rest[f'B_{sd}_Foot'].to_3x3();relativefoot=(co[footids[sd]]-np.array(home))@np.array((R@rest[f'B_{sd}_Foot'].to_3x3().inverted()).transposed());desired=max(0,feet[sd]['sole']-sole0[sd])*scale;target=Vector((home.x+delta[0]*.25,home.y+delta[1]*scale,desired-float(relativefoot[:,2].min())))
   hs=feet[sd]['hip'];aa=feet[sd]['ankle'];kk=feet[sd]['knee'];su=(aa-hs).normalized();pole=(kk-hs)-su*(kk-hs).dot(su);pole=Vector(((-.2 if sd=='R' else .2),min(-.3,pole.y),pole.z*.3))
   leg(sd,target,pole,R)
  floor_shifts.append(ground(max(0,min(feet[sd]['sole']-sole0[sd] for sd in 'LR'))*scale));poses.append(current())
 poses[-1]=poses[0];out[name]=poses;report[name]={'duration':(len(poses)-1)/30,'source':'Completed MM6 Ogre','adaptation':'World motion deltas about mean source rotations applied to Guardian fitted hunch; original clip phase and speed; source flight height retained.','floor_shift_range':list(map(float,(min(floor_shifts),max(floor_shifts)))), 'source_floor':zfloor,'source_soles':[[fr[3][sd]['sole'] for sd in 'LR'] for fr in frames], 'source_pitch':[[fr[3][sd]['pitch'] for sd in 'LR'] for fr in frames], 'pitch_zero':pitch0,'sole_zero':sole0}
reset();standing=[]
for f in range(61):
 reset();phase=2*math.pi*f/60;turn('B_Spine',(1,0,0),.5*math.sin(phase));turn('B_Head',(1,0,0),-.35*math.sin(phase));rig.pose.bones['Jaw'].rotation_quaternion=Quaternion((1,0,0),math.radians(-3));ground();standing.append(current())
standing[-1]=standing[0];out['Standing']=standing;ready=standing[0]

def path(t,rows):
 ts=np.array([r[0] for r in rows]);vs=np.array([r[1] for r in rows],float);i=int(np.clip(np.searchsorted(ts,t)-1,0,len(ts)-2));a,b=ts[i:i+2];u=float(np.clip((t-a)/(b-a),0,1))
 def tangent(j):return np.zeros(vs.shape[1]) if j in (0,len(ts)-1) else (vs[j+1]-vs[j-1])/(ts[j+1]-ts[j-1])
 v=(2*u**3-3*u**2+1)*vs[i]+(u**3-2*u**2+u)*(b-a)*tangent(i)+(-2*u**3+3*u**2)*vs[i+1]+(u**3-u**2)*(b-a)*tangent(i+1)
 return Vector(v) if len(v)>1 else v
R0=rest['B_R_Hand'].translation;L0=rest['B_L_Hand'].translation
rpath=[(0,R0),(.125,(-.72,-.30,1.08)),(.25,(-.56,-.15,1.82)),(.375,(-.45,-.63,1.45)),(.50,(.03,-.78,.98)),(.625,(-.34,-.57,.67)),(.75,(-.65,-.23,.62)),(.875,R0),(1,R0)]
lpath=[(0,L0),(.25,(.72,-.22,.70)),(.5,(.84,-.10,.74)),(.75,L0),(1,L0)]
rf=(sum((Vector(f['base']) for f in F['R']),Vector())/3-R0).normalized()
directions=[(0,rf),(.125,(-.1,-.8,.5)),(.25,(-.1,0,1)),(.375,(.2,-.95,.1)),(.5,(.45,-.3,-.84)),(.625,(-.1,-.3,-.95)),(.75,rf),(1,rf)]
qanchors=[]
for t,d in directions:
 q=rf.rotation_difference(Vector(d).normalized())@rest['B_R_Hand'].to_quaternion()
 if qanchors and q.dot(qanchors[-1][1])<0:q=-q
 qanchors.append((t,q))
def hand_rotation(t):
 i=int(np.clip(np.searchsorted([x[0] for x in qanchors],t)-1,0,len(qanchors)-2));a,qa=qanchors[i];b,qb=qanchors[i+1];return qa.slerp(qb,(t-a)/(b-a)).to_matrix()
poses=[];checks=[]
for f in range(46):
 t=float(np.interp(f/30,[0,.5,.75,.875,1,1.125,1.25,1.375,1.5],[0,.125,.25,.375,.5,.625,.75,.875,1]));apply(ready);lift=float(path(t,[(0,(0,)),(.25,(7,)),(.5,(-4,)),(.75,(0,)),(1,(0,))])[0]);twist=float(path(t,[(0,(0,)),(.25,(-6,)),(.5,(7,)),(.75,(0,)),(1,(0,))])[0]);turn('B_Spine',(1,0,0),lift);turn('B_Spine2',(0,0,1),twist);turn('B_Head',(1,0,0),-lift*.55)
 reach=armik.solve(rig,'R',path(t,rpath),pole=path(t,[(0,rest['B_R_Forearm'].translation),(.125,(-1.05,.05,1.1)),(.75,(-1.05,.05,1.1)),(1,rest['B_R_Forearm'].translation)]),hand_rot=hand_rotation(t));armik.solve(rig,'L',path(t,lpath),pole=(1.0,.08,.95),hand_rot=rest['B_L_Hand'].to_3x3())
 pb=rig.pose.bones['B_R_Hand'];sw,tw=armik.split_swing_twist(pb.rotation_quaternion,Vector((0,1,0)))
 if sw.w<0:sw=-sw
 pb.rotation_quaternion=Quaternion().slerp(sw,min(1,math.radians(59)/max(sw.angle,1e-8)))@Quaternion((0,1,0),max(-math.radians(85),min(math.radians(85),tw)))
 env=math.sin(math.pi*min(1,t/.8))**2 if t<.8 else 0
 for side in 'RL':
  for i,claw in enumerate(F[side]):rig.pose.bones[claw['name']].rotation_quaternion=Quaternion((0,0,1),math.radians((i-1)*8*env))
 rig.pose.bones['Jaw'].rotation_quaternion=Quaternion((1,0,0),math.radians(-3+12*env))
 blend=min(1,t/.12,(1-t)/.16);blend=blend*blend*(3-2*blend)
 for sd in 'RL':
  for part in ('UpperArm','Forearm','Hand'):
   n=f'B_{sd}_{part}';pb=rig.pose.bones[n];pb.rotation_quaternion=ready[n][0].slerp(pb.rotation_quaternion,blend)
 bpy.context.view_layer.update();ground();poses.append(current());checks.append({'time':f/30,'native_phase':t,'reach':reach,'wrist':list(armik.wrist_cost(rig,'R',armik.W(rig,'B_R_Hand').to_3x3().normalized()))})
poses[0]=ready;poses[-1]=ready;out['Attack']=poses;report['Attack']={'duration':1.5,'timing':'Extended native anticipation; stroke near native 1.0-second gameplay contact, original recovery speed.','native_anchors':'motion_selection.json','checks':checks}
for name,poses in out.items():write(name,poses)
reset();scene.render.fps=30;bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/pilots_authored.blend'));(P/'review/pilot_motion.json').write_text(json.dumps(report,indent=2)+'\n');print('PILOTS', {n:len(p) for n,p in out.items()},flush=True)
common.workbench_clay(scene);outdir=P/'review/pilots';outdir.mkdir(exist_ok=True)
for name in out:
 action(bpy.data.actions[name]);end=int(bpy.data.actions[name].frame_range[1]);samples=range(0,end+1,3) if name=='Attack' else sorted(set((0,end//4,end//2,3*end//4,end)))
 for f in samples:
  scene.frame_set(f);common.render_views(str(outdir/f'{name}_{f:03d}'),1.15,3.1,views=('front','left','three_quarter'),resolution=(650,650))
