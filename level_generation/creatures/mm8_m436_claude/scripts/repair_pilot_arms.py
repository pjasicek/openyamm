"""Fit the civilian shove with continuous anatomical elbow paths."""
from pathlib import Path
import bpy, sys, math, json, os, runpy
import numpy as np
from mathutils import Vector, Matrix, Quaternion
p=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(p/'scripts'))
import armik, action_curves
bpy.ops.wm.open_mainfile(filepath=str(p/'work/pilot_fitted.blend'))
rig=bpy.data.objects['Rig']; scene=bpy.context.scene

def active(a):
    rig.animation_data.action=a
    if a is not None and len(a.slots): rig.animation_data.action_slot=a.slots[0]
def snapshot(): return {b.name:b.matrix_basis.copy() for b in rig.pose.bones}
def sample(a,t):
    active(a); scene.frame_set(int(t),subframe=t-int(t)); return snapshot()
def restore(x):
    active(None)
    for n,m in x.items(): rig.pose.bones[n].matrix_basis=m
    bpy.context.view_layer.update()
def smooth(t):
    t=max(0,min(1,t)); return t*t*(3-2*t)
def write(name,frames):
    bpy.data.actions.remove(bpy.data.actions[name]); a=bpy.data.actions.new(name);a.use_fake_user=True;active(a)
    for f,x in enumerate(frames):
        for n,m in x.items():
            b=rig.pose.bones[n];b.rotation_mode='QUATERNION';b.rotation_quaternion=m.to_quaternion()
            b.keyframe_insert('rotation_quaternion',frame=f*.5)
            if n=='B_Pelvis': b.location=m.translation;b.keyframe_insert('location',frame=f*.5)
    a.use_frame_range=True;a.frame_start=0;a.frame_end=(len(frames)-1)*.5
    action_curves.continuous(a)
    for fc in action_curves.curves(a):
        for k in fc.keyframe_points:k.interpolation='LINEAR'
    return a

# R2 supplies body weight transfer; this broad civilian makes a compact defensive shove.
a=bpy.data.actions['Attack'];raw=[sample(a,i*.5) for i in range(129)];home=sample(bpy.data.actions['Standing'],0)
restore(home);offset={s:armik.W(rig,f'B_{s}_Hand').translation-armik.W(rig,f'B_{s}_UpperArm').translation for s in 'LR'}
def path(t,keys):
 for i in range(len(keys)-1):
  if t<=keys[i+1][0]:
   t0,v0=keys[i];t1,v1=keys[i+1];u=(t-t0)/(t1-t0);return Vector(v0).lerp(Vector(v1),smooth(u))
 return Vector(keys[-1][1])
prepared=[];targets={sd:[] for sd in 'LR'};hand_poses={sd:[] for sd in 'LR'}
for i,x in enumerate(raw):
 restore(x);t=i/60;w=min(smooth(t/.30),smooth((64/30-t)/.5))
 for n in ('B_Pelvis','B_Spine','B_Spine1','B_Spine2','B_Neck','B_Head','B_L_Clavicle','B_R_Clavicle'):
  b=rig.pose.bones[n];b.rotation_quaternion=home[n].to_quaternion().slerp(b.rotation_quaternion,.38)
 bpy.context.view_layer.update()
 for sd,sign in [('L',1),('R',-1)]:
  S=armik.W(rig,f'B_{sd}_UpperArm').translation.copy()
  if sd=='R':keys=[(0,offset[sd]),(.62,(-.17,-.13,-.16)),(.98,(-.025,-.52,-.045)),(1.18,(-.04,-.49,-.09)),(1.55,(-.17,-.24,-.20)),(64/30,offset[sd])]
  else:keys=[(0,offset[sd]),(.65,(.17,-.14,-.28)),(1.04,(.19,.025,-.28)),(1.55,(.16,-.08,-.30)),(64/30,offset[sd])]
  targets[sd].append(S+path(t,keys));hand_poses[sd].append(armik.W(rig,f'B_{sd}_Hand').to_quaternion())
 prepared.append(snapshot())

# Select a continuous anatomical elbow plane without excessive humeral roll.
options={};paths={}
for sd,sign in [('L',1),('R',-1)]:
    rows=[];pole=Vector((sign*.35,.10,-1))
    for i,x in enumerate(prepared):
        restore(x);rows.append(armik.arm_options(rig,sd,targets[sd][i],pole))
    cost=np.array([o[0] for o in rows[0]]);backs=[]
    for previous,current in zip(rows,rows[1:]):
        qa=np.array([list(o[1].to_quaternion()) for o in previous]);qb=np.array([list(o[1].to_quaternion()) for o in current])
        angle=np.degrees(2*np.arccos(np.clip(abs(qa@qb.T),0,1)))
        matrix=cost[:,None]+angle**2*1.2;back=np.argmin(matrix,axis=0)
        cost=matrix[back,np.arange(len(back))]+[o[0] for o in current];backs.append(back)
    j=int(np.argmin(cost));path=[j]
    for back in reversed(backs):j=int(back[j]);path.append(j)
    path.reverse()
    phi=np.unwrap(np.radians([rows[i][j][4] for i,j in enumerate(path)]))
    phi=np.convolve(np.pad(phi,(2,2),mode='edge'),[1/16,4/16,6/16,4/16,1/16],'valid')
    options[sd]=[]
    for i,x in enumerate(prepared):
        restore(x);options[sd].append(armik.arm_options(rig,sd,targets[sd][i],pole,[math.degrees(phi[i])])[0])
frames=[]
for i,x in enumerate(prepared):
    restore(x);t=i*.5;w=min(smooth(t/9),smooth((64-t)/12))
    for sd in 'LR':
        un,fn,hn=[f'B_{sd}_{n}' for n in ('UpperArm','Forearm','Hand')]
        _,R,Rf,T,_=options[sd][i]
        armik.set_world(rig,un,armik.rot_world(armik.W(rig,un),R))
        armik.set_world(rig,fn,armik.rot_world(armik.W(rig,fn),Rf))
        F=armik.W(rig,fn).copy();H=armik.W(rig,hn).copy()
        # Keep the wrist within its anatomical cone as the elbow drops into the guard.
        fr=rig.data.bones[fn].matrix_local.to_3x3();hr=rig.data.bones[hn].matrix_local.to_3x3()
        neutral=F.to_3x3()@fr.inverted()@hr
        roots=[rig.data.bones[f'B_{sd}_Finger{k}'].head_local for k in range(5)]
        axis=hr.inverted()@(sum(roots,Vector())/5-rig.data.bones[hn].head_local).normalized()
        sw,tw=armik.split_swing_twist(neutral.to_quaternion().inverted()@neutral.to_quaternion().slerp(hand_poses[sd][i],.15),axis)
        if sw.angle>math.pi:sw=-sw
        if sw.angle>math.radians(55):sw=Quaternion().slerp(sw,math.radians(55)/sw.angle)
        tw=max(-math.radians(75),min(math.radians(75),tw))
        R=neutral@(sw@Quaternion(axis,tw)).to_matrix()
        armik.set_world(rig,hn,armik.rot_world(H,R))
    fitted=snapshot()
    # Ease the anatomical elbow planes into the unchanged guard endpoints.
    for sd in 'LR':
        for bn in ('UpperArm','Forearm','Hand'):
            n=f'B_{sd}_{bn}';fitted[n]=raw[i][n].lerp(fitted[n],w)
    restore(fitted)
    body=bpy.data.objects['Body'];ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();low=min(me.vertices[v.index].co.z for v in body.data.vertices if v.co.z<.15);ev.to_mesh_clear();P=armik.W(rig,'B_Pelvis');P.translation.z+=.004-low;armik.set_world(rig,'B_Pelvis',P);frames.append(snapshot())
write('Attack',frames)
active(None)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/pilot_fitted.blend'))
