"""Native-inspired wolf motion, authored at 24 fps with planted IK feet and grounded remains."""
import bpy
import json
import math
import sys
from pathlib import Path
import numpy as np
from mathutils import Vector, Matrix, Quaternion

PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT.parent/'mm6_rat_claude/scripts'))
import posing as P
bpy.ops.wm.open_mainfile(filepath=str(PROJECT/'work/rig_v1.blend'))
rig=bpy.data.objects['Wolf_Rig'];mesh=bpy.data.objects['Wolf'];sc=bpy.context.scene
FPS=24;sc.render.fps=FPS
P.reset(rig)
REST={b.name:b.matrix.copy() for b in rig.pose.bones}
FEET={(kind,s):REST[f'{kind}Paw_{s}'].translation.copy() for kind in ['Front','Hind'] for s in 'LR'}
V=Vector

def smooth(t):
    t=min(1,max(0,t));return t*t*(3-2*t)

def rot(name,axis,degrees):
    if abs(degrees)>1e-7:P.rotate_world(rig,name,axis,degrees)

def body(pitch=0,spine=0,head=0,yaw=0,roll=0,offset=(0,0,0),jaw=0,tail=-10,phase=0):
    P.reset(rig)
    root=rig.pose.bones['Spine1'];root.matrix=Matrix.Translation(V(offset))@root.matrix
    bpy.context.view_layer.update()
    rot('Spine1','Y',roll);rot('Spine1','X',pitch)
    rot('Spine2','X',spine*.5);rot('Spine3','X',spine*.5)
    rot('Neck1','X',head*.4);rot('Head','X',head*.6)
    rot('Neck1','Z',yaw*.5);rot('Head','Z',yaw*.5);rot('Jaw','X',-jaw)
    for i in range(1,7):
        rot(f'Tail{i}','X',tail if i==1 else 0)
        rot(f'Tail{i}','Z',3*i/6*math.sin(2*math.pi*phase-i*.4))

def leg(kind,side,target,pitch=0):
    upper,lower=(f'UpperArm_{side}',f'ForeArm_{side}') if kind=='Front' else (f'Thigh_{side}',f'Shin_{side}')
    pole=V(target)+V((.04 if side=='L' else -.04,.3 if kind=='Front' else -.3,.08))
    P.two_bone_ik(rig,upper,lower,target,pole)
    bone=rig.pose.bones[f'{kind}Paw_{side}']
    q=Quaternion(V((1,0,0)),math.radians(pitch))@REST[bone.name].to_quaternion()
    bone.matrix=Matrix.LocRotScale(bone.head.copy(),q,V((1,1,1)))
    bpy.context.view_layer.update()

def pose(params):
    args={k:params[k] for k in ['pitch','spine','head','yaw','roll','offset','jaw','tail','phase'] if k in params}
    body(**args)
    free=params.get('free',0)
    fk={}
    if free>0:
        for side in 'LR':
            for bone,angle in [('UpperArm',params.get('front',0)),('ForeArm',params.get('elbow',0)),
                               ('Thigh',params.get('hind',0)),('Shin',params.get('knee',0))]:
                rot(f'{bone}_{side}','X',angle)
        fk={b.name:(b.rotation_quaternion.copy(),b.location.copy()) for b in rig.pose.bones}
    if free<1:
        for (kind,side),base in FEET.items():
            off=params.get('front_offset' if kind=='Front' else 'hind_offset',(0,0,0))
            leg(kind,side,base+V(off),params.get('paw',0) if kind=='Front' else 0)
        if free>0:
            for b in rig.pose.bones:
                q,loc=fk[b.name]
                b.rotation_quaternion=b.rotation_quaternion.slerp(q,free)
                b.location=b.location.lerp(loc,free)
            bpy.context.view_layer.update()

READY={'pitch':9,'spine':4,'head':-12,'tail':-8,'front_offset':(0,-.035,0)}

def keys(frames,t):
    for (t0,a),(t1,b) in zip(frames[:-1],frames[1:]):
        if t<=t1:
            u=smooth((t-t0)/(t1-t0));out={}
            for k in a.keys()|b.keys():
                av,bv=a.get(k,0),b.get(k,0)
                if isinstance(av,tuple) or isinstance(bv,tuple):
                    av=V(av if isinstance(av,tuple) else (0,0,0));bv=V(bv if isinstance(bv,tuple) else (0,0,0))
                    out[k]=tuple(av.lerp(bv,u))
                else:out[k]=av+(bv-av)*u
            return out
    return frames[-1][1]

def standing(t):
    p=dict(READY);p['head']+=1.5*math.sin(math.pi*t);p['phase']=t/2;pose(p)

def gait(t,period,stride,duty,lift):
    phase=(t/period)%1
    body(pitch=7,head=-4,tail=-35,spine=2*math.sin(4*math.pi*phase),
         offset=(0,0,-.014+.006*math.cos(4*math.pi*phase)),phase=phase)
    for kind,side,shift in [('Front','L',0),('Hind','R',0),('Front','R',.5),('Hind','L',.5)]:
        p=(phase+shift)%1;span=stride*duty
        if p<duty:dy=-span/2+stride*p;dz=0;pitch=0
        else:
            u=(p-duty)/(1-duty);dy=span/2-span*smooth(u);dz=lift*math.sin(math.pi*u);pitch=20*math.sin(math.pi*u)
        leg(kind,side,FEET[kind,side]+V((0,dy,dz)),pitch)

ATTACK=[(0,READY),(.25,{**READY,'pitch':15,'spine':8,'offset':(0,.025,-.01),'jaw':5}),
        (.5,{'pitch':-22,'spine':-8,'head':16,'offset':(0,.015,.06),'front_offset':(0,.02,.23),
              'hind_offset':(0,0,.03),'jaw':15,'paw':-25,'tail':-20}),
        (.875,{'pitch':14,'spine':8,'head':-5,'offset':(0,-.08,.01),'front_offset':(0,-.09,.01),
                'hind_offset':(0,-.02,.07),'jaw':10,'tail':-30}),
        (1.125,READY)]
HIT=[(0,READY),(.25,{'pitch':-38,'spine':-8,'head':-4,'offset':(0,.04,0),
                    'front_offset':(0,.06,.26),'jaw':16,'tail':-30}),(.625,READY)]
DEATH=[(0,{**READY,'free':0}),(.25,{'pitch':-65,'spine':-8,'head':-8,'offset':(0,.05,.02),
                                 'free':1,'front':-50,'elbow':35,'hind':-15,'knee':20,'jaw':18,'tail':-30}),
       (.45,{'pitch':-35,'roll':65,'spine':-5,'head':-8,'offset':(0,.10,-.1),
              'free':1,'front':-25,'elbow':20,'hind':15,'knee':20,'jaw':12,'tail':-35}),
       (.625,{'pitch':0,'roll':93,'spine':0,'head':5,'offset':(0,.10,-.32),
               'free':1,'front':7,'elbow':0,'hind':-10,'knee':10,'jaw':8,'tail':-40})]

def fidget(t):
    p=dict(READY);u=t/.625;p['pitch']+=5*math.sin(math.pi*u);p['head']-=3*math.sin(2*math.pi*u)
    p['tail']+=12*math.sin(2*math.pi*u);p['jaw']=5*math.sin(math.pi*u);pose(p)

def coordinates():
    ev=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
    co=np.array([v.co[:] for v in me.vertices]);ev.to_mesh_clear();return co

CLIPS={'Standing':(2,True,standing),
       'Walking':(1,True,lambda t:gait(t,1,.34,.58,.065)),
       'Running':(.625,True,lambda t:gait(t,.625,.48,.48,.09)),
       'Attack':(1.125,False,lambda t:pose(keys(ATTACK,t))),
       'Hit':(.625,False,lambda t:pose(keys(HIT,t))),
       'Death':(.625,False,lambda t:pose(keys(DEATH,t))),
       'Dead':(1,True,lambda t:pose(DEATH[-1][1])),
       'Fidget':(.625,False,fidget)}
PILOT=False
report={}
for name,(seconds,loop,fn) in CLIPS.items():
    if PILOT and name not in ['Standing','Walking','Attack']:continue
    n=round(seconds*FPS);poses=[];mins=[]
    if rig.animation_data:rig.animation_data.action=None
    for f in range(n+1):
        fn((f%n)/FPS if loop else f/FPS)
        co=coordinates();assert np.isfinite(co).all()
        # Lift penetration from the evaluated skin, including fur and paws, without changing bone lengths.
        lift=max(0.,-.003-float(co[:,2].min()))
        if name=='Dead' or (name=='Death' and f>=n*.7):lift=.003-float(co[:,2].min())
        if lift:
            root=rig.pose.bones['Spine1'];root.matrix=Matrix.Translation(V((0,0,lift)))@root.matrix
            bpy.context.view_layer.update()
        mins.append(float(coordinates()[:,2].min()))
        poses.append({b.name:(b.rotation_quaternion.copy(),b.location.copy()) for b in rig.pose.bones})
    act=bpy.data.actions.new(name);act.use_fake_user=True
    rig.animation_data_create();rig.animation_data.action=act;prev={}
    for f,pose_data in enumerate(poses):
        for b in rig.pose.bones:
            q,loc=pose_data[b.name]
            if b.name in prev and prev[b.name].dot(q)<0:q=-q
            prev[b.name]=q;b.rotation_quaternion=q;b.location=loc;b.scale=(1,1,1)
            for channel in ['rotation_quaternion','location','scale']:b.keyframe_insert(channel,frame=f+1)
    report[name]={'duration':seconds,'frames':n,'loop':loop,'minimum_z':min(mins)}
    assert min(mins)>-.015,(name,min(mins))
    print('CLIP',name,report[name],flush=True)
rig.animation_data.action=bpy.data.actions['Standing'];sc.frame_set(1)
(PROJECT/'work/animation_report.json').write_text(json.dumps(report,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(PROJECT/'work/anim_v1.blend'))
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);mesh.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(PROJECT/'export/wolf_pilot.glb'),use_selection=True,
    export_format='GLB',export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,
    export_skins=True,export_all_influences=False,export_morph=False,export_reset_pose_bones=True,
    export_anim_slide_to_zero=True)
