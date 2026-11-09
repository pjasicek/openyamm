"""Native dagger toss: prepare, release, track the spin, catch overhead, and lower the hand."""
import bpy, sys, json, math, numpy as np
from pathlib import Path
from mathutils import Matrix, Vector, Quaternion
P=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(P/'scripts'))
import armik
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_carry_twist.blend'))
rig=bpy.data.objects['Rig']; sc=bpy.context.scene
G=json.loads((P/'work/grip_pose.json').read_text()); AX=Vector(G['handle_axis_hand_local'])
def act(a):
    rig.animation_data.action=a
    if a is not None and len(a.slots): rig.animation_data.action_slot=a.slots[0]
def restore(snap):
    act(None)
    for n,m in snap.items(): rig.pose.bones[n].matrix_basis=m.copy()
    bpy.context.view_layer.update()
act(bpy.data.actions['Standing']); sc.frame_set(0)
ST={b.name:b.matrix_basis.copy() for b in rig.pose.bones}
R0=armik.W(rig,'B_R_Hand').translation.copy(); L0=armik.W(rig,'B_L_Hand').translation.copy()
D0=(armik.W(rig,'B_R_Hand').to_3x3()@AX).normalized()
# Cubic Hermite paths retain velocity through the release rather than stopping at each key pose.
def curve(t,keys):
    times=np.array([k[0] for k in keys]); pts=np.array([tuple(k[1]) for k in keys])
    i=min(max(int(np.searchsorted(times,t)-1),0),len(keys)-2)
    tang=[]
    for j in range(len(keys)):
        tang.append(np.zeros(3) if j in (0,len(keys)-1) else (pts[j+1]-pts[j-1])/(times[j+1]-times[j-1]))
    h=times[i+1]-times[i]; u=float(np.clip((t-times[i])/h,0,1))
    return Vector((2*u**3-3*u*u+1)*pts[i]+(u**3-2*u*u+u)*h*tang[i]+(-2*u**3+3*u*u)*pts[i+1]+(u**3-u*u)*h*tang[i+1])
def smooth(x):
    x=float(np.clip(x,0,1)); return x*x*(3-2*x)
rkeys=[(0,R0),(.30,(-.27,-.22,1.10)),(.60,(-.28,-.24,1.39)),(.86,(-.29,-.20,1.53)),
       (1.25,(-.29,-.20,1.57)),(1.46,(-.28,-.21,1.49)),(2.2,R0)]
lkeys=[(0,L0),(.18,(.27,-.24,1.10)),(.45,(.08,-.27,1.31)),(.90,(.06,-.27,1.34)),(1.35,(.10,-.27,1.32)),(1.85,(.27,-.24,1.10)),(2.2,L0)]
N=66; frames=[]
for f in range(N+1):
    t=f/30; restore(ST)
    # The eyes follow the airborne blade; a little chest turn follows the throwing shoulder.
    look=smooth((t-.35)/.25)*(1-smooth((t-1.25)/.45))
    for n,angle in [('B_Neck',-.12*look),('B_Head',-.17*look)]:
        m=armik.W(rig,n); p=m.translation.copy(); m=Matrix.Rotation(angle,4,'X')@m; m.translation=p
        armik.set_world(rig,n,m)
    left=curve(t,lkeys)
    armik.solve(rig,'L',left,pole=Vector((.45,-.04,1.16)))
    fa=armik.W(rig,'B_L_Forearm').to_3x3().normalized()
    rel=rig.data.bones['B_L_Forearm'].matrix_local.to_3x3().inverted()@rig.data.bones['B_L_Hand'].matrix_local.to_3x3()
    neutral=fa@rel
    home=ST['B_L_Hand'].to_quaternion()
    amount=smooth(t/.3)*(1-smooth((t-1.7)/.5))
    armik.set_world(rig,'B_L_Hand',armik.rot_world(armik.W(rig,'B_L_Hand'),neutral))
    snap={b.name:b.matrix_basis.copy() for b in rig.pose.bones}
    up=Vector((-.10,-.15,1)).normalized(); mix=smooth((t-.2)/.4)*(1-smooth((t-1.5)/.7))
    direction=D0.lerp(up,mix).normalized()
    frames.append({'snap':snap,'wrist':curve(t,rkeys),'dir':direction})
act(None)
choices=armik.arm_dp(rig,'R',frames,AX,twist_neutral=30,k_twist=.6,k_dphi=1,k_dpsi=.8)
phi=np.array([c['phi'] for c in choices],float); psi=np.degrees(np.unwrap(np.radians([c['psi'] for c in choices])))
for a in (phi,psi):
    a[:]=np.convolve(np.pad(a,(2,2),mode='edge'),np.array([1,2,3,2,1])/9,'valid')
poses=[]; stats=[]
for f,fr in enumerate(frames):
    sw,tw=armik.apply_arm(rig,'R',fr['snap'],fr['wrist'],AX,fr['dir'],phi[f],psi[f]); stats.append((sw,tw))
    opening=smooth((f/30-.56)/.10)*(1-smooth((f/30-1.18)/.07))
    for n,q in G['finger_local'].items():
        rig.pose.bones[n].rotation_quaternion=Quaternion(q).slerp(Quaternion(),opening*.85)
    poses.append({b.name:(b.rotation_quaternion.copy(),b.location.copy()) for b in rig.pose.bones})
old=bpy.data.actions.get('Fidget')
if old: bpy.data.actions.remove(old)
a=bpy.data.actions.new('Fidget'); a.use_fake_user=True; act(a); prev={}
for f,p in enumerate(poses):
    for n,(q,l) in p.items():
        b=rig.pose.bones[n]; b.rotation_mode='QUATERNION'
        if n in prev and q.dot(prev[n])<0: q=-q
        prev[n]=q.copy(); b.rotation_quaternion=q; b.location=l
        b.keyframe_insert('rotation_quaternion',frame=f)
        if n=='B_Pelvis': b.keyframe_insert('location',frame=f)
a.use_frame_range=True; a.frame_start=0; a.frame_end=N
act(None)
(P/'work/fidget_plan.json').write_text(json.dumps({'release_frame':18,'catch_frame':37.5,'duration_seconds':2.2,'spin_turns':1,
    'gravity_mps2':9.81,'right_wrist_swing_max':max(x[0] for x in stats),'twist_range':[min(x[1] for x in stats),max(x[1] for x in stats)]},indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_fidget.blend'))
print('FIDGET',N+1,'frames, release 18 catch 37.5; wrist swing',max(x[0] for x in stats))
