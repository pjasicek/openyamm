"""Native-duration hit, smooth stance transitions, side collapse, and mesh-grounded soles."""
import bpy,sys,json,math,runpy,os
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));sys.dont_write_bytecode=True
sys.argv=['foot_level.py','--',str(P/os.environ.get('FINISH_INPUT','work/rig_armplanes.blend')),str(P/'work/rig_feet.blend'),'Standing','Walking:const','Running:const','Attack','Hit','Cast','Death:until=24']
runpy.run_path(str(P/'scripts/foot_level.py'),run_name='__main__')
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene;sc.render.fps=30
names=[b.name for b in rig.pose.bones]
def setact(a):
    rig.animation_data_create();rig.animation_data.action=a
    if a is not None and len(a.slots):rig.animation_data.action_slot=a.slots[0]
def snap():return {b.name:(b.rotation_quaternion.copy(),b.location.copy()) for b in rig.pose.bones}
def sample(a,f):
    setact(a);sc.frame_set(int(f),subframe=f-int(f));return snap()
def apply(p):
    for n,(q,l) in p.items():rig.pose.bones[n].rotation_mode='QUATERNION';rig.pose.bones[n].rotation_quaternion=q;rig.pose.bones[n].location=l
    bpy.context.view_layer.update()
def smooth(t):t=max(0,min(1,t));return t*t*(3-2*t)
def blend(a,b,t):return {n:(a[n][0].slerp(b[n][0] if a[n][0].dot(b[n][0])>=0 else -b[n][0],t),a[n][1].lerp(b[n][1],t)) for n in a}
def write(name,poses):
    old=bpy.data.actions.get(name)
    if old:bpy.data.actions.remove(old)
    ac=bpy.data.actions.new(name);ac.use_fake_user=True;setact(ac);prev={}
    for f,p in enumerate(poses):
        for n,(q,l) in p.items():
            if n in prev and q.dot(prev[n])<0:q=-q
            prev[n]=q;b=rig.pose.bones[n];b.rotation_mode='QUATERNION';b.rotation_quaternion=q;b.location=l
            b.keyframe_insert('rotation_quaternion',frame=f)
            if n=='B_Pelvis':b.keyframe_insert('location',frame=f)
    ac.use_frame_range=True;ac.frame_start=0;ac.frame_end=len(poses)-1
    for layer in ac.layers:
        for strip in layer.strips:
            for cb in strip.channelbags:
                for fc in cb.fcurves:
                    for k in fc.keyframe_points:k.interpolation='LINEAR'
    setact(None)
ST=sample(bpy.data.actions['Standing'],0)
clips={n:[sample(bpy.data.actions[n],f) for f in range(int(bpy.data.actions[n].frame_range[1])+1)] for n in ['Standing','Walking','Running','Attack','Hit','Death','Cast']}
# Cast lead-in puts the source release near the native one-second action lead.
cast=clips['Cast'];lead=16
clips['Cast']=[blend(ST,cast[0],smooth(i/lead)) for i in range(lead)]+cast
clips['Hit']=clips['Hit'][2:21]
clips['Fidget']=[]
for f in range(61):
    p={n:(q.copy(),l.copy()) for n,(q,l) in ST.items()};a=math.sin(math.pi*f/60)**2
    for n,axis,angle in [('B_Head',(0,1,0),-12),('B_Neck',(0,0,1),3),('B_Spine2',(1,0,0),2)]:p[n]=(p[n][0]@Quaternion(axis,math.radians(angle)*a),p[n][1])
    clips['Fidget'].append(p)
# The native corpse is curled on its side; settle the fall into a relaxed side pose.
setact(None);apply(ST)
Q=Matrix.Rotation(math.radians(75),4,'Y')@Matrix.Rotation(-math.pi/2,4,'X')
m=rig.pose.bones['B_Pelvis'].matrix.copy();pos=m.translation.copy();m=Q@m;m.translation=pos;rig.pose.bones['B_Pelvis'].matrix=m;bpy.context.view_layer.update()
lat=(Q.to_3x3()@Vector((1,0,0))).normalized()
for side,hip,knee in [('R',-10,35),('L',-45,85)]:
 for bone,angle in [('Thigh',hip),('Calf',knee)]:
  pb=rig.pose.bones[f'B_{side}_{bone}'];m=pb.matrix.copy();pos=m.translation.copy();m=Matrix.Rotation(math.radians(angle),4,lat)@m;m.translation=pos;pb.matrix=m;bpy.context.view_layer.update()
dead_pose=snap()
for name,poses in clips.items():
    if name in ('Attack','Hit','Death','Cast'):
        fi={'Attack':5,'Hit':3,'Death':7,'Cast':0}[name];fo={'Attack':22,'Hit':6,'Death':0,'Cast':8}[name]
        for i,p in enumerate(poses):
            w=min(smooth(i/fi) if fi else 1,smooth((len(poses)-1-i)/fo) if fo else 1)
            poses[i]=blend(ST,p,w)
    if name=='Death':
        setact(None);origin=None
        for i,p in enumerate(poses):
            apply(p);m=rig.pose.bones['B_Pelvis'].matrix.copy();pos=m.translation.copy()
            if origin is None:origin=pos.copy()
            pos.x=origin.x+(pos.x-origin.x)*.5;pos.y=origin.y+(pos.y-origin.y)*.5
            m.translation=pos
            rig.pose.bones['B_Pelvis'].matrix=m;bpy.context.view_layer.update();p2=snap();target=dict(dead_pose);target['B_Pelvis']=(target['B_Pelvis'][0],p2['B_Pelvis'][1]);poses[i]=blend(p2,target,smooth((i-36)/36))
    write(name,poses)
# Clamp the actual boot/body surface; preserve the run's airborne phase.
vg=[g.name for g in body.vertex_groups]
foot=np.array([sum(e.weight for e in v.groups if vg[e.group] in ('B_L_Foot','B_R_Foot','B_L_Toe0','B_R_Toe0'))>.5 for v in body.data.vertices])
import armik
FOOT_MASK={s:np.array([sum(e.weight for e in v.groups if vg[e.group] in (f'B_{s}_Foot',f'B_{s}_Toe0'))>.5 for v in body.data.vertices]) for s in 'LR'}
BODY_MASK=np.array([sum(e.weight for e in v.groups if any(k in vg[e.group] for k in ('UpperArm','Forearm','Hand','Finger','Clavicle')))<.2 for v in body.data.vertices])
def coords():
 ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();c=np.array([v.co[:] for v in m.vertices]);ev.to_mesh_clear();return c

def leg_ik(s,target,pole_target=None):
 hn,kn,an=[f'B_{s}_{k}' for k in ('Thigh','Calf','Foot')]
 mh,mk,ma=[rig.pose.bones[n].matrix.copy() for n in (hn,kn,an)];h,k,a=[m.translation.copy() for m in (mh,mk,ma)]
 l1,l2=(k-h).length,(a-k).length;u=(target-h).normalized();dist=min((target-h).length,(l1+l2)*.999)
 old=(a-h).normalized();pole=(k-h)-old*(k-h).dot(old);pole=old.rotation_difference(u)@pole;pole=(pole-u*pole.dot(u)).normalized()
 if pole_target is not None:
  pole=pole_target-h;pole=(pole-u*pole.dot(u)).normalized()
 ca=max(-1,min(1,(l1*l1+dist*dist-l2*l2)/(2*l1*dist)));newk=h+l1*(u*ca+pole*math.sqrt(1-ca*ca))
 q=(k-h).rotation_difference(newk-h);m=q.to_matrix().to_4x4()@mh;m.translation=h;rig.pose.bones[hn].matrix=m;bpy.context.view_layer.update()
 mk2=rig.pose.bones[kn].matrix.copy();a2=rig.pose.bones[an].head.copy();q=(a2-mk2.translation).rotation_difference(target-mk2.translation);m=q.to_matrix().to_4x4()@mk2;m.translation=mk2.translation;rig.pose.bones[kn].matrix=m;bpy.context.view_layer.update()
 m=rig.pose.bones[an].matrix.copy();at=m.translation.copy();m=ma.copy();m.translation=at;rig.pose.bones[an].matrix=m;bpy.context.view_layer.update()

def plant_both():
 for _ in range(3):
  c=coords();targets={s:rig.pose.bones[f'B_{s}_Foot'].head.copy() for s in 'LR'}
  for s,t in targets.items():t.z-=float(c[FOOT_MASK[s],2].min())
  # Lower the pelvis just enough for both fixed-length legs to reach their grounded soles.
  for it in range(30):
   reach=[]
   for s,t in targets.items():
    h,k,a=[rig.pose.bones[f'B_{s}_{n}'].head for n in ('Thigh','Calf','Foot')];reach.append((t-h).length/((k-h).length+(a-k).length))
   if max(reach)<.997:break
   m=rig.pose.bones['B_Pelvis'].matrix.copy();m.translation.z-=.004;rig.pose.bones['B_Pelvis'].matrix=m;bpy.context.view_layer.update()
  for s,t in targets.items():leg_ik(s,t)

def settle_arms(f):
 weight=smooth((f-42)/20)
 if weight<=0:return
 for s,sgn in [('R',-1),('L',1)]:
  old={f'B_{s}_{k}':rig.pose.bones[f'B_{s}_{k}'].rotation_quaternion.copy() for k in ('UpperArm','Forearm','Hand')}
  sh=rig.pose.bones[f'B_{s}_UpperArm'].head.copy();target=sh+Vector((.4 if s=='R' else .28,.12 if s=='R' else -.40,0));target.z=.15 if s=='R' else .065
  hn=f'B_{s}_Hand';hand=rig.data.bones[hn];fw=hand.matrix_local.inverted()@rig.data.bones[f'B_{s}_Finger2'].head_local;fw.normalize()
  g=json.loads((P/f'work/grip_pose{"" if s=="R" else "_L"}.json').read_text());side=Vector(g['handle_axis_hand_local']);side=(side-fw*side.dot(fw)).normalized()
  worldf=Vector((.5,.86 if s=='R' else -.86,0)).normalized();worldside=Vector((0,0,1)).cross(worldf);local=Matrix((fw,side,fw.cross(side))).transposed();world=Matrix((worldf,worldside,worldf.cross(worldside))).transposed()
  armik.solve(rig,s,target,pole=sh+Vector((.7 if s=='R' else .5,.1 if s=='R' else -.45,.05)),hand_rot=world@local.transposed())
  for n,q in old.items():rig.pose.bones[n].rotation_quaternion=q.slerp(rig.pose.bones[n].rotation_quaternion,weight)
  bpy.context.view_layer.update()

for name in clips:
    ac=bpy.data.actions[name];poses=[];lows=[]
    for f in range(int(ac.frame_range[1])+1):
        p=sample(ac,f);setact(None);apply(p)
        ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();z=np.array([v.co.z for v in me.vertices]);ev.to_mesh_clear()
        low=float(z[BODY_MASK].min() if name=='Death' else z[foot].min());dz=-min(0,low) if name=='Running' else -low
        m=rig.pose.bones['B_Pelvis'].matrix.copy();m.translation.z+=dz;rig.pose.bones['B_Pelvis'].matrix=m;bpy.context.view_layer.update()
        if name in ('Standing','Attack','Hit','Fidget'):plant_both()
        if name=='Death':
            lower=smooth((f-36)/22)*.10
            m=rig.pose.bones['B_Pelvis'].matrix.copy();m.translation.z-=lower;rig.pose.bones['B_Pelvis'].matrix=m;bpy.context.view_layer.update()
            widen=smooth((f-18)/9)*(1-smooth((f-42)/15))
            if widen>0:
                for side,sign in [('R',-1),('L',1)]:
                    h=rig.pose.bones[f'B_{side}_Hand'].matrix.copy();target=h.translation+Vector((sign*.18*widen,0,0));armik.solve(rig,side,target,hand_rot=h.to_3x3().normalized())
            settle_arms(f)
            weight=smooth((f-36)/30)
            if weight>0:
                pelvis=rig.pose.bones['B_Pelvis'].head.copy();ankle=rig.pose.bones['B_R_Foot'].head.copy()
                target=pelvis+Vector((-.35,-.58,-.22));target=ankle.lerp(target,weight)
                leg_ik('R',target,pole_target=pelvis+Vector((.35,-.3,-.2)))
                c=coords();low=float(c[FOOT_MASK['R'],2].min());target=rig.pose.bones['B_R_Foot'].head.copy();target.z+=weight*(.01-low)
                leg_ik('R',target,pole_target=pelvis+Vector((.35,-.3,-.2)))
                for side in 'LR':
                    c=coords();low=float(c[FOOT_MASK[side],2].min());target=rig.pose.bones[f'B_{side}_Foot'].head.copy();target.z+=weight*(.01-low);leg_ik(side,target)
        poses.append(snap());lows.append(low)
    write(name,poses);print('FLOOR',name,min(lows),max(lows))
# The fast run needs half-frame root corrections as well as integer-frame contacts.
ac=bpy.data.actions['Running'];corrections=[]
for f in np.arange(.5,ac.frame_range[1],1):
 p=sample(ac,float(f));setact(None);apply(p);low=float(coords()[foot,2].min())
 if low<0:
  m=rig.pose.bones['B_Pelvis'].matrix.copy();m.translation.z-=low;rig.pose.bones['B_Pelvis'].matrix=m;bpy.context.view_layer.update();corrections.append((float(f),rig.pose.bones['B_Pelvis'].location.copy()))
setact(ac)
for f,loc in corrections:
 rig.pose.bones['B_Pelvis'].location=loc;rig.pose.bones['B_Pelvis'].keyframe_insert('location',frame=f)
setact(None)
# A held corpse is exactly the finished collapse, including its side roll.
last=sample(bpy.data.actions['Death'],bpy.data.actions['Death'].frame_range[1]);write('Dead',[last,last])
# Geometric event markers, evaluated at the outgoing source speed.
g=json.loads((P/'work/grip_pose.json').read_text());a=bpy.data.actions['Attack'];tip=[];dirs=[]
for f in range(int(a.frame_range[1])+1):
    sample(a,f);m=rig.pose.bones['B_R_Hand'].matrix;d=m.to_3x3()@Vector(g['handle_axis_hand_local']);tip.append(np.array(m@Vector(g['handle_centre_hand_local'])+d*1.361));dirs.append(np.array(d))
speed=np.linalg.norm(np.diff(tip,axis=0),axis=1);candidates=[i for i in range(len(speed)) if dirs[i][1]<-.5 and tip[i][1]<-.6]
k=max(candidates,key=lambda i:speed[i]);impact=(k+.5)/30
pal=[];ac=bpy.data.actions['Cast']
for f in range(int(ac.frame_range[1])+1):sample(ac,f);pal.append(np.array(rig.pose.bones['B_L_Hand'].head))
sp=np.linalg.norm(np.diff(pal,axis=0),axis=1);kc=int(np.argmax(sp));castimpact=(kc+.5)/30
(P/'work/clip_timing.json').write_text(json.dumps({'attack_impact_s':impact,'cast_impact_s':castimpact,'native_action_s':1.0,'hit_s':.6,'death_s':bpy.data.actions['Death'].frame_range[1]/30,'attack_tip_speed_mps':float(speed[k]*30),'blade_edge_hand_local':list((rig.pose.bones['B_R_Hand'].matrix.to_3x3().inverted()@Vector(tip[k+1]-tip[k])).normalized())},indent=1))
setact(None);bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_timed.blend'))
os.environ['BAKE_ONLY']='1';os.environ['FA']='0.6';os.environ['FA_RAMP']='0.15,0.85'
sys.argv=['twist_bones.py','--',str(P/'work/rig_timed.blend'),str(P/'work/rig_final_motion.blend')]
runpy.run_path(str(P/'scripts/twist_bones.py'),run_name='__main__')
