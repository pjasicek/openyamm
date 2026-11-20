"""Bovine walk with long planted phases, hoof IK, restrained armour flex and native action choreography."""
from pathlib import Path
import sys, json, math
import bpy
import numpy as np
from mathutils import Vector, Matrix, Quaternion

P = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parent/'mm6_rat_claude/scripts'))
import posing as pose
bpy.ops.wm.open_mainfile(filepath=str(P/'work/uv_master.blend'))
rig, mesh = bpy.data.objects['Gorgon_Rig'], bpy.data.objects['Gorgon']
sc=bpy.context.scene
sc.render.fps=48
FPS=sc.render.fps
for old in list(bpy.data.actions):
    bpy.data.actions.remove(old)
pose.reset(rig)
rest={b.name:b.matrix.copy() for b in rig.pose.bones}
X,Y,Z=Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1))
points=np.array([tuple(v.co) for v in mesh.data.vertices])
foot={}
for kind in ('Front','Hind'):
    for side,sign in [('L',1),('R',-1)]:
        name=f'{kind}Hoof_{side}'
        mask=(points[:,0]*sign>0)&((points[:,1]<0)==(kind=='Front'))&(points[:,2]<.035)
        foot[kind,side]=rest[name].translation.copy()-Vector((0,0,float(points[mask,2].min())))

def rot(name,axis,degrees):
    pose.rotate_world(rig,name,axis,degrees)

def smooth(t):
    t=max(0,min(1,t))
    return t*t*(3-2*t)

def leg(kind,side,offset=Vector(),pitch=0,articulate=False):
    hoof=f'{kind}Hoof_{side}';pastern=f'{kind}Pastern_{side}'
    upper,lower=(f'UpperArm_{side}',f'ForeArm_{side}') if kind=='Front' else (f'Thigh_{side}',f'Shin_{side}')
    target=foot[kind,side]+offset
    rotation=Quaternion(X,math.radians(pitch))
    lower_vector=rotation@(rest[hoof].translation-rest[pastern].translation)
    pastern_rotation=rotation
    if articulate:
        # The fetlock inclines with the planted leg; keeping it vertical forced an implausible crouch.
        direction=(target-rig.pose.bones[upper].head).normalized()
        rest_vector=rest[hoof].translation-rest[pastern].translation
        lower_vector=direction*rest_vector.length
        pastern_rotation=rest_vector.normalized().rotation_difference(direction)
    carpus=target-lower_vector
    pole=carpus+Vector((.02 if side=='L' else -.02,.35 if kind=='Front' else -.35,.04))
    pose.two_bone_ik(rig,upper,lower,carpus,pole)
    for name in (pastern,hoof):
        b=rig.pose.bones[name]
        b.matrix=Matrix.LocRotScale(b.head.copy(),(pastern_rotation if name==pastern else rotation)@rest[name].to_quaternion(),Vector((1,1,1)))
        bpy.context.view_layer.update()

def body(drop=-.015,pitch=0,roll=0,head=0,yaw=0,travel=0):
    pose.reset(rig)
    b=rig.pose.bones['Spine1']
    b.matrix=Matrix.Translation((0,travel,drop))@b.matrix
    bpy.context.view_layer.update()
    rot('Spine1',X,pitch);rot('Spine1',Y,roll)
    rot('Neck1',X,head*.35);rot('Head',X,head*.65)
    rot('Neck1',Z,yaw*.4);rot('Head',Z,yaw*.6)

def tail(t,amplitude=3):
    for i in range(1,6):
        rot(f'Tail{i}',Z,amplitude*(i/5)*math.sin(2*math.pi*t-.55*i))

def planted():
    for kind,side in foot:
        leg(kind,side)

def stand(t):
    s=math.sin(math.pi*t)
    body(drop=-.015+.0015*s,head=1.2*s,yaw=1.8*s)
    planted();tail(t/2,2)

def gait(t,running=False):
    period=.75 if running else 1.0
    phase=t/period%1
    stride=.60 if running else .48
    duty=.50 if running else .62
    body(drop=-.045-.003*math.cos(4*math.pi*phase),pitch=.6*math.sin(4*math.pi*phase),
         roll=.8*math.sin(2*math.pi*phase),head=-1.2*math.sin(4*math.pi*phase))
    # Lateral sequence: LH, LF, RH, RF; running uses diagonal support.
    shifts={('Hind','L'):0,('Front','L'):.75,('Hind','R'):.5,('Front','R'):.25}
    if running:
        shifts={('Hind','L'):0,('Front','R'):0,('Hind','R'):.5,('Front','L'):.5}
    for key,shift in shifts.items():
        q=(phase+shift)%1
        distance=stride*duty
        if q<duty:
            dy=-distance/2+stride*q
            dz=pitch=0
        else:
            u=(q-duty)/(1-duty)
            dy=distance/2-distance*smooth(u)
            dz=(.035 if running else .018)*math.sin(math.pi*u)**1.5
            pitch=12*math.sin(math.pi*u)
        kind,side=key
        upper=f'UpperArm_{side}' if kind=='Front' else f'Thigh_{side}'
        dy+=rest[upper].translation.y-rest[f'{kind}Hoof_{side}'].translation.y
        leg(*key,Vector((0,dy,dz)),pitch,articulate=True)
    tail(phase,4 if running else 2.5)

def keyed(keys,t):
    for (a,va),(b,vb) in zip(keys,keys[1:]):
        if t<=b:
            u=smooth((t-a)/(b-a))
            return {k:va.get(k,0)+(vb.get(k,0)-va.get(k,0))*u for k in va.keys()|vb.keys()}
    return keys[-1][1]

def action(t,kind):
    if kind=='Attack':
        keys=[(0,{}),(.35,{'pitch':-15,'head':-6,'lift':.10,'travel':.018}),
              (.70,{'pitch':-8,'head':4,'lift':.055}),(.875,{'pitch':7,'head':23,'travel':-.018}),
              (1.125,{'head':6}), (1.375,{})]
    elif kind=='Hit':
        keys=[(0,{}),(.125,{'pitch':4,'head':16,'travel':.013,'sag':-.017}),
              (.375,{'head':-7,'yaw':-5}),(.625,{})]
    else:
        keys=[(0,{}),(.2,{'head':-9,'yaw':10}),(.42,{'head':4,'yaw':-7}),(.625,{})]
    a=keyed(keys,t)
    body(drop=-.025+a.get('sag',0),pitch=a.get('pitch',0),head=a.get('head',0),
         yaw=a.get('yaw',0),travel=a.get('travel',0))
    for k,s in foot:
        leg(k,s,Vector((0,0,a.get('lift',0) if k=='Front' else 0)), -14 if a.get('lift',0)>.04 and k=='Front' else 0)
    tail(t,3)

def death(t):
    a=keyed([(0,{'roll':0,'drop':-.015}),(.20,{'roll':18,'drop':-.09,'head':20}),
             (.50,{'roll':90,'drop':-.17,'head':-4}),(.75,{'roll':94,'drop':-.19,'head':-8})],t)
    body(drop=a['drop'],roll=a['roll'],head=a.get('head',0))
    u=smooth(t/.5)
    for s in 'LR':
        rot(f'UpperArm_{s}',X,-20*u);rot(f'ForeArm_{s}',X,48*u)
        rot(f'Thigh_{s}',X,-28*u);rot(f'Shin_{s}',X,35*u)
        rot(f'HindPastern_{s}',X,-15*u)
    tail(.3,4*u)
    # Ground the evaluated collapse, then ease underside limbs up to allow the armoured flank to settle.
    for s in 'LR':
        if s=='L':
            rot(f'UpperArm_{s}',Z,-35*u);rot(f'Thigh_{s}',Z,-30*u)
    co=evaluated()
    b=rig.pose.bones['Spine1']
    b.matrix=Matrix.Translation((0,0,-float(co[:,2].min())))@b.matrix
    bpy.context.view_layer.update()

def evaluated():
    obj=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get());data=obj.to_mesh()
    co=np.array([tuple(v.co) for v in data.vertices]);obj.to_mesh_clear()
    return co

clips={'Standing':(2,True,stand),'Walking':(1,True,gait),'Running':(.75,True,lambda t:gait(t,True)),
       'Attack':(1.375,False,lambda t:action(t,'Attack')),'Hit':(.625,False,lambda t:action(t,'Hit')),
       'Fidget':(.625,False,lambda t:action(t,'Fidget')),'Death':(.75,False,death),
       'Dead':(1,False,lambda t:death(.75))}
report={}
for name,(seconds,loop,fn) in clips.items():
    rig.animation_data_create();rig.animation_data.action=None
    n=round(seconds*FPS);frames=[];lowest=1
    for f in range(n+1):
        fn((f%n)/FPS if loop else f/FPS)
        lowest=min(lowest,float(evaluated()[:,2].min()))
        frames.append({b.name:(b.location.copy(),b.rotation_quaternion.copy(),b.scale.copy()) for b in rig.pose.bones})
    act=bpy.data.actions.new(name);act.use_fake_user=True;rig.animation_data.action=act
    previous={}
    for f,frame in enumerate(frames,1):
        for b in rig.pose.bones:
            loc,q,scale=frame[b.name]
            if b.name in previous and q.dot(previous[b.name])<0:q=-q
            previous[b.name]=q
            b.location,b.rotation_quaternion,b.scale=loc,q,scale
            for channel in ('location','rotation_quaternion','scale'):b.keyframe_insert(channel,frame=f)
    report[name]={'duration':n/FPS,'loop':loop,'minimum_z':lowest}
    print(name,report[name],flush=True)
rig.animation_data.action=bpy.data.actions['Standing'];sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/anim_v1.blend'))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/uv_master.blend'))
(P/'work/animation_report.json').write_text(json.dumps(report,indent=2)+'\n')
assert min(x['minimum_z'] for x in report.values())>-.015, 'Floor penetration requires repair'
