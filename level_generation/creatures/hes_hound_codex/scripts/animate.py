"""Native-inspired wolf motion, authored at 60 fps with planted IK feet and grounded remains."""
import bpy
import json
import math
import sys
import os
from pathlib import Path
import numpy as np
from mathutils import Vector, Matrix, Quaternion

PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT/'scripts'))
import posing as P
bpy.ops.wm.open_mainfile(filepath=str(PROJECT/'work/rig_uv_clean.blend'))
rig=bpy.data.objects['Hound_Rig'];mesh=bpy.data.objects['Hound'];sc=bpy.context.scene
FPS=60;sc.render.fps=FPS
P.reset(rig)
REST={b.name:b.matrix.copy() for b in rig.pose.bones}
FEET={(kind,s):REST[f'{kind}Paw_{s}'].translation.copy() for kind in ['Front','Hind'] for s in 'LR'}
V=Vector

def smooth(t):
    t=min(1,max(0,t));return t*t*(3-2*t)

def rot(name,axis,degrees):
    if abs(degrees)>1e-7:P.rotate_world(rig,name,axis,degrees)

def body(pitch=0,spine=0,head=0,yaw=0,roll=0,offset=(0,0,0),jaw=0,tail=0,phase=0):
    P.reset(rig)
    root=rig.pose.bones['Spine1'];root.matrix=Matrix.Translation(V(offset))@root.matrix
    bpy.context.view_layer.update()
    rot('Spine1','Y',roll);rot('Spine1','X',pitch)
    rot('Spine2','X',spine*.5);rot('Spine3','X',spine*.5)
    rot('Neck1','X',head*.4);rot('Head','X',head*.6)
    rot('Neck1','Z',yaw*.5);rot('Head','Z',yaw*.5);rot('Jaw','X',jaw)
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
    free={kind:params.get('free_'+kind.lower(),params.get('free',0)) for kind in ('Front','Hind')}
    chains={'Front':['UpperArm','ForeArm','FrontPaw'],'Hind':['Thigh','Shin','HindPaw']}
    fk={}
    if max(free.values())>0:
        for side in 'LR':
            for bone,key in [('UpperArm','front'),('ForeArm','elbow'),('FrontPaw','fpaw'),
                             ('Thigh','hind'),('Shin','knee'),('HindPaw','hpaw')]:
                axis=(Quaternion(V((1,0,0)),math.radians(params.get('pitch',0)))
                      @ Quaternion(V((0,1,0)),math.radians(params.get('roll',0))) @ V((1,0,0)))
                rot(f'{bone}_{side}',axis,params.get(key,0))
        fk={b.name:(b.rotation_quaternion.copy(),b.location.copy()) for b in rig.pose.bones}
    for (kind,side),base in FEET.items():
        if free[kind]>=1: continue
        off=params.get(f'{kind.lower()}_{side}_offset',params.get(kind.lower()+'_offset',(0,0,0)))
        leg(kind,side,base+V(off),params.get('paw',0) if kind=='Front' else 0)
    for kind,weight in free.items():
        if 0<weight<1:
            for side in 'LR':
                for name in chains[kind]:
                    b=rig.pose.bones[f'{name}_{side}'];q,loc=fk[b.name]
                    b.rotation_quaternion=b.rotation_quaternion.slerp(q,weight)
                    b.location=b.location.lerp(loc,weight)
            bpy.context.view_layer.update()

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

READY={'head':-3,'tail':0,'offset':(0,0,-.012)}

def standing(t):
    p=dict(READY)
    p['head']+=1.2*math.sin(math.pi*t)
    p['phase']=t/2
    pose(p)

# Toe contact and pitch follow the rat's improved gait, with measured hound limb lengths.
P.reset(rig)
dom=[mesh.vertex_groups[max(v.groups,key=lambda g:g.weight).group].name for v in mesh.data.vertices]
rest_co=np.array([v.co[:] for v in mesh.data.vertices])
TOES={}
PAW_VEC={}
for kind,side in FEET:
    indices=[i for i,n in enumerate(dom) if n==f'{kind}Paw_{side}']
    assert indices,(kind,side)
    xyz=rest_co[indices]
    low=xyz[xyz[:,2]<xyz[:,2].min()+.004]
    toe=V(low[np.argmin(low[:,1])])
    toe.z=.002
    TOES[kind,side]=toe
    PAW_VEC[kind,side]=toe-FEET[kind,side]

def place_toe(kind,side,toe,pitch=0):
    q=Quaternion(V((1,0,0)),math.radians(pitch))
    wrist=toe-q@PAW_VEC[kind,side]
    leg(kind,side,wrist,pitch)
    return (rig.pose.bones[f'{kind}Paw_{side}'].head-wrist).length

GAITS={
 'Walking':dict(period=.7,stride=.72,duty=.58,lift=.13,bob=.009,rock=1.5,flex=2,
                phases={('Front','L'):0,('Hind','R'):0,('Front','R'):.5,('Hind','L'):.5}),
 'Running':dict(period=.5,stride=1.25,duty=.30,lift=.20,bob=.03,rock=4,flex=6,
                phases={('Hind','L'):0,('Hind','R'):.06,('Front','L'):.42,('Front','R'):.52}),
}
MISSES={}

def gait(t,name):
    c=GAITS[name]
    phase=(t/c['period'])%1
    rock=c['rock']*math.sin(2*math.pi*(phase-.42))
    flex=c['flex']*math.cos(2*math.pi*(phase-.85))
    body(pitch=rock,spine=flex,head=-rock-flex-3,tail=4,
         offset=(0,0,-.075-c['bob']*(.5+.5*math.cos(4*math.pi*(phase-.15)))),phase=phase)
    for (kind,side),shift in c['phases'].items():
        p=(phase-shift)%1
        duty=c['duty'];span=c['stride']*duty
        if p<duty:
            dy=-span/2+c['stride']*p
            dz=0
            pitch=22*smooth((p/duty-.65)/.35)
        else:
            u=(p-duty)/(1-duty)
            dy=span/2-span*smooth(u)
            dz=c['lift']*math.sin(math.pi*u)
            pitch=22*(1-smooth(u/.35))+15*math.sin(math.pi*u)
        toe=TOES[kind,side]+V((0,dy+(.08 if kind=='Front' else -.08),dz))
        miss=place_toe(kind,side,toe,pitch)
        MISSES[name]=max(MISSES.get(name,0),miss)

# The MM8 wolf's planted crouch, rear-up, airborne bite and front-first landing, fitted to this taller rig.
BITE=[(0,READY),
      (.12,{'pitch':5,'spine':3,'head':2,'offset':(0,.03,-.055),'jaw':8,'tail':-12}),
      (.25,{'pitch':-6,'spine':-3,'head':-6,'offset':(0,0,-.09),'jaw':18,'tail':10}),
      (.38,{'pitch':-24,'spine':-4,'head':12,'offset':(0,-.015,-.01),'hind_offset':(0,.01,0),
            'free_front':1,'front':-38,'elbow':30,'fpaw':-18,'jaw':18,'tail':28}),
      (.54,{'pitch':-2,'spine':-4,'head':-2,'offset':(0,-.15,.30),'free_front':1,'free_hind':1,
            'front':-50,'elbow':20,'fpaw':-15,'hind':40,'knee':10,'hpaw':10,'jaw':18}),
      (.64,{'pitch':6,'spine':2,'head':10,'offset':(0,-.18,.26),'free_front':1,'free_hind':1,
            'front':-40,'elbow':22,'hind':5,'knee':30,'jaw':18,'tail':5}),
      (.72,{'pitch':10,'spine':4,'head':14,'offset':(0,-.18,.27),'free_front':1,'free_hind':1,
            'front':-18,'elbow':10,'hind':-5,'knee':30,'jaw':3,'tail':16}),
      (.82,{'pitch':10,'spine':4,'head':4,'offset':(0,-.12,.045),'front_offset':(0,-.10,0),
            'free_hind':.6,'hind':-10,'knee':28,'hind_offset':(0,-.04,.06),'jaw':6,'tail':24}),
      (.92,{'pitch':3,'head':-4,'offset':(0,-.04,-.07),'front_offset':(0,-.04,0),'jaw':2,'tail':8}),
      (1.05,READY)]
# Keep the charge's .4-second wind-up and .53-second bite; the faster leap is driven by the hindquarters.
POUNCE=[(0,READY),
        (.20,{'pitch':6,'spine':3,'head':-8,'offset':(0,.04,-.07),'jaw':10,'tail':-16}),
        (.32,{'pitch':-12,'spine':-3,'head':6,'offset':(0,.02,-.04),'free_front':.4,
              'front':-30,'elbow':22,'jaw':18,'tail':16}),
        (.40,{'pitch':-22,'spine':-4,'head':12,'offset':(0,0,-.02),'free_front':1,
              'front':-40,'elbow':25,'fpaw':-15,'jaw':18,'tail':26}),
        (.47,{'pitch':-3,'spine':-4,'head':2,'offset':(0,-.18,.24),'free_front':1,'free_hind':1,
              'front':-55,'elbow':20,'fpaw':-15,'hind':35,'knee':12,'jaw':18}),
        (.53,{'pitch':10,'spine':3,'head':12,'offset':(0,-.20,.22),'free_front':1,'free_hind':1,
              'front':-25,'elbow':10,'hind':0,'knee':30,'jaw':3,'tail':14}),
        (.65,{'pitch':10,'spine':3,'head':4,'offset':(0,-.12,.02),'front_offset':(0,-.10,0),
              'free_hind':.5,'hind':-10,'knee':25,'hind_offset':(0,-.04,.05),'jaw':5,'tail':22}),
        (.80,{'pitch':3,'head':-4,'offset':(0,-.03,-.055),'front_offset':(0,-.03,0),'tail':8}),
        (.95,READY)]
HIT=[(0,READY),
     (.08,{'pitch':-8,'spine':-5,'head':-12,'yaw':-16,'roll':-9,'offset':(.04,.10,-.04),'jaw':16,'tail':-15}),
     (.17,{'pitch':2,'head':8,'yaw':-10,'roll':-6,'offset':(.065,.11,-.075),
           'front_L_offset':(.055,.07,.07),'front_R_offset':(0,.03,0),'hind_offset':(.025,.03,0),'jaw':8,'tail':-8}),
     (.28,{'pitch':6,'head':1,'yaw':5,'roll':3,'offset':(.025,.045,-.055),
           'front_L_offset':(.04,.06,0),'front_R_offset':(0,.02,0),'tail':8}),
     (.40,{'head':-4,'offset':(.015,0,-.02)}),(.50,READY)]
DEATH=[(0,{**READY,'free':0}),(.18,{'pitch':8,'head':-8,'offset':(0,.02,-.15),
      'free':.3,'front':-10,'elbow':25,'hind':-15,'knee':30,'jaw':14}),
      (.48,{'roll':55,'pitch':8,'head':3,'offset':(.08,.04,-.30),'free':1,
             'front':-25,'elbow':20,'hind':15,'knee':25,'jaw':12,'tail':-10}),
      (.85,{'roll':94,'pitch':0,'head':5,'offset':(.12,.04,-.41),'free':1,
             'front':5,'elbow':12,'hind':-15,'knee':20,'jaw':7,'tail':0}),
      (1.15,{'roll':90,'pitch':0,'head':4,'offset':(.12,.04,-.42),'free':1,
             'front':5,'elbow':12,'hind':-15,'knee':20,'jaw':7,'tail':0})]

def fidget(t):
    p=dict(READY)
    u=t/1.6
    p['head']+=10*math.sin(math.pi*u)
    p['yaw']=10*math.sin(6*math.pi*u)*math.sin(math.pi*u)**2
    p['tail']=3*math.sin(2*math.pi*u)
    p['jaw']=4*math.sin(math.pi*u)
    pose(p)

def coordinates():
    ev=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get())
    me=ev.to_mesh()
    co=np.array([v.co[:] for v in me.vertices])
    ev.to_mesh_clear()
    return co

CLIPS={'Standing':(2,True,standing),
       'Walking':(.7,True,lambda t:gait(t,'Walking')),
       'Running':(.5,True,lambda t:gait(t,'Running')),
       'Bite':(1.05,False,lambda t:pose(keys(BITE,t))),
       'Pounce':(.95,False,lambda t:pose(keys(POUNCE,t))),
       'Hit':(.50,False,lambda t:pose(keys(HIT,t))),
       'Death':(1.15,False,lambda t:pose(keys(DEATH,t))),
       'Dead':(1,True,lambda t:pose(DEATH[-1][1])),
       'Fidget':(1.6,False,fidget)}
report={}
for name,(seconds,loop,fn) in CLIPS.items():
    n=round(seconds*FPS)
    poses=[];mins=[];lifts=[];paw_heights=[]
    if rig.animation_data: rig.animation_data.action=None
    for f in range(n+1):
        fn((f%n)/FPS if loop else f/FPS)
        if name in ('Death','Dead'):
            settle=1 if name=='Dead' else smooth((f/FPS-.3)/.55)
            for side,angle in [('L',30),('R',-35)]:
                for bone in ['UpperArm','Thigh']: rot(f'{bone}_{side}','Y',angle*settle)
            rot('Tail1','Y',-30*settle)
        co=coordinates()
        assert np.isfinite(co).all()
        lift=max(0.,-.003-float(co[:,2].min()))
        if name=='Dead' or (name=='Death' and f>=n*.7): lift=.003-float(co[:,2].min())
        if lift:
            root=rig.pose.bones['Spine1']
            root.matrix=Matrix.Translation(V((0,0,lift)))@root.matrix
            bpy.context.view_layer.update()
        mins.append(float(coordinates()[:,2].min()))
        lifts.append(lift)
        xyz=coordinates()
        paw_heights.append([float(xyz[[i for i,n in enumerate(dom) if n==f'{k}Paw_{side}'],2].min())
                            for k in ('Front','Hind') for side in 'LR'])
        poses.append({b.name:(b.rotation_quaternion.copy(),b.location.copy()) for b in rig.pose.bones})
    act=bpy.data.actions.new(name)
    act.use_fake_user=True
    rig.animation_data_create()
    rig.animation_data.action=act
    prev={}
    for f,pose_data in enumerate(poses):
        for b in rig.pose.bones:
            q,loc=pose_data[b.name]
            if b.name in prev and prev[b.name].dot(q)<0: q=-q
            prev[b.name]=q
            b.rotation_quaternion=q
            b.location=loc
            b.scale=(1,1,1)
            for channel in ['rotation_quaternion','location','scale']: b.keyframe_insert(channel,frame=f)
    act.use_frame_range=True
    act.frame_start=0
    act.frame_end=n
    report[name]={'duration':seconds,'frames':n,'loop':loop,'minimum_z':min(mins),
                  'maximum_lowest_z':max(mins),'root_correction_range':[min(lifts),max(lifts)],
                  'worst_ik_miss':MISSES.get(name,0),
                  'clearance_by_frame':mins,'paw_minima_FL_FR_HL_HR':paw_heights}
    assert min(mins)>-.015,(name,min(mins))
    assert MISSES.get(name,0)<.005,(name,MISSES.get(name))
    if name in ('Bite','Pounce'):
        planted_until=.25 if name=='Bite' else .20
        assert max(max(v) for v in paw_heights[:round(planted_until*FPS)+1])<.025,(name,'floating crouch')
        launch=.38 if name=='Bite' else .40
        impact=.72 if name=='Bite' else .53
        assert max(max(v[2:]) for v in paw_heights[:round(launch*FPS)+1])<.025,(name,'hind paws lifted before launch')
        assert mins[round(impact*FPS)]>.08,(name,'bite already landed')
        assert max(mins)>.20,(name,'no airborne leap')
    print('CLIP',name,{k:v for k,v in report[name].items() if not isinstance(v,list)},flush=True)
rig.animation_data.action=bpy.data.actions['Standing']
sc.frame_set(0)
(PROJECT/'work/animation_report.json').write_text(json.dumps(report,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(PROJECT/'work/anim_v1.blend'))
sys.stdout.flush()
sys.stderr.flush()
os._exit(0)

