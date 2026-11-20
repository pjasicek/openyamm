"""Repair the reviewed casting pause and attack arm poses on the selected textured master."""
from pathlib import Path
import bpy, sys, math, json, os, runpy
import numpy as np
from mathutils import Vector, Matrix, Quaternion
p=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(p/'scripts'))
import armik, action_curves
bpy.ops.wm.open_mainfile(filepath=str(p/'review/motion_revision_02/rig_textured_uv_before.blend'))
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

# Replace the duplicate hold with a continuous gather, reaching the same release at 35/30 seconds.
a=bpy.data.actions['Cast'];cast=[]
for i in range(101):
    t=i*.5
    if t<35:
        x=t/35;u=35*(.25*x-(3/14)*x*x+(11/28)*x*x*x)
        source=u if u<=8 else u+20
    else: source=t
    cast.append(sample(a,source))
write('Cast',cast)

# The source's lateral torso lean and upward free elbow exaggerated the fitted shoulder silhouette.
a=bpy.data.actions['Attack'];raw=[sample(a,i*.5) for i in range(121)];home=sample(bpy.data.actions['Standing'],0)
prepared=[];targets={sd:[] for sd in "LR"};hand_poses={sd:[] for sd in "LR"}
for i,x in enumerate(raw):
    restore(x);t=i*.5;w=min(smooth(t/9),smooth((60-t)/12))
    head=armik.W(rig,'B_Head').to_quaternion()
    hands={s:armik.W(rig,f'B_{s}_Hand').copy() for s in 'LR'}
    shoulders=[armik.W(rig,f'B_{s}_UpperArm').translation.copy() for s in 'LR']
    lateral=(shoulders[0]-shoulders[1]).normalized();level=Vector((lateral.x,lateral.y,0)).normalized()
    q=Quaternion().slerp(lateral.rotation_difference(level),.65*w)
    spine=armik.W(rig,'B_Spine');armik.set_world(rig,'B_Spine',armik.rot_world(spine,q.to_matrix()@spine.to_3x3()))
    H=armik.W(rig,'B_Head');armik.set_world(rig,'B_Head',armik.rot_world(H,head.to_matrix()))
    for sd,sign in [('L',1),('R',-1)]:
        un,fn,hn=[f'B_{sd}_{n}' for n in ('UpperArm','Forearm','Hand')]
        S=armik.W(rig,un).translation.copy();target=hands[sd].translation.copy()
        if sd=='L':
            guard=S+Vector((.17,-.21,-.23));target=target.lerp(guard,w*.92)
        else:
            wind=smooth(t/9)*(1-smooth((t-29)/9))
            target+=Vector((.065,.015,.045))*wind
        targets[sd].append(target);hand_poses[sd].append(hands[sd].to_quaternion())
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
    restore(x);t=i*.5;w=min(smooth(t/9),smooth((60-t)/12))
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
        sw,tw=armik.split_swing_twist(neutral.to_quaternion().inverted()@hand_poses[sd][i],axis)
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
    restore(fitted);frames.append(snapshot())
write('Attack',frames)
active(None)
path=p/'work/rig_textured_uv.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path))
os.environ['TWIST_POSES_ONLY']='1';os.environ['TWIST_ACTIONS']='Attack,Cast'
sys.argv=['twist_bones','--',str(path),str(path)]
runpy.run_path(str(p/'scripts/twist_bones.py'),run_name='__main__')
rig=bpy.data.objects['Rig'];scene=bpy.context.scene
# Guard against reintroducing a frozen anticipation or changing the event timing.
a=bpy.data.actions['Cast'];positions=[]
for f in range(13,45):
    sample(a,f*30/48);positions.append(armik.W(rig,'B_L_Hand').translation.copy())
steps=[(b-a).length for a,b in zip(positions,positions[1:])]
assert min(steps)>0.0001,steps
assert abs(a.frame_range[1]-50)<1e-6
assert abs(bpy.data.actions['Attack'].frame_range[1]-60)<1e-6
(p/'review/motion_revision_02/author_checks.json').write_text(json.dumps({'cast_min_wrist_step_m_at_48fps':min(steps),'cast_max_wrist_step_m_at_48fps':max(steps),'cast_release_seconds':35/30,'attack_impact_seconds':77/60},indent=2))
print('MOTION REVISION WRITTEN',min(steps))
