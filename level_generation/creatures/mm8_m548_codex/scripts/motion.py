"""Native-inspired quadruped motion on measured joints; shared rat IK helpers."""
import bpy, sys, math
from pathlib import Path
from mathutils import Vector, Matrix, Quaternion
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parent/'mm6_rat_claude/scripts'))
import posing
rig=bpy.data.objects['CrystalDragonRig'];mesh=bpy.data.objects['CrystalDragon'];sc=bpy.context.scene
posing.reset(rig)
REST={b.name:b.matrix.copy() for b in rig.pose.bones}
X=Vector((1,0,0));Y=Vector((0,1,0));Z=Vector((0,0,1))
FPS=24
CLIPS={'Standing':(2,True),'Walking':(1,True),'Running':(.75,True),'Attack':(1,False),'Hit':(.625,False),'Fidget':(.625,False),'Death':(1,False),'Dead':(1,False)}
def rot(name,axis,angle):
    posing.rotate_world(rig,name,axis,angle)
def world_quat(name,q):
    b=rig.pose.bones[name];b.matrix=Matrix.LocRotScale(b.head.copy(),q,Vector((1,1,1)));bpy.context.view_layer.update()
def leg(kind,side,offset=(0,0,0),pitch=0):
    s=1 if side=='L' else -1
    paw=('FrontPaw_' if kind=='front' else 'HindPaw_')+side
    target=REST[paw].translation+Vector(offset)
    if kind=='front':
        posing.two_bone_ik(rig,'UpperArm_'+side,'ForeArm_'+side,target,target+Vector((s*.02,.3,.1)))
    else:
        t='Tarsus_'+side;v=REST[paw].translation-REST[t].translation
        q=Quaternion(X,math.radians(pitch))
        hock=target-q@v
        posing.two_bone_ik(rig,'Thigh_'+side,'Shin_'+side,hock,hock+Vector((s*.03,-.3,.1)))
        world_quat(t,q@REST[t].to_quaternion())
    world_quat(paw,Quaternion(X,math.radians(pitch))@REST[paw].to_quaternion())
def root(offset=(0,0,0)):
    b=rig.pose.bones['Spine1'];b.matrix=Matrix.Translation(Vector(offset))@b.matrix;bpy.context.view_layer.update()
def co():
    import numpy as np
    ev=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
    a=np.empty(len(me.vertices)*3);me.vertices.foreach_get('co',a);ev.to_mesh_clear();return a.reshape(-1,3)
def smooth(t):
    t=max(0,min(1,t));return t*t*(3-2*t)
def keys(t,points):
    for (a,va),(b,vb) in zip(points[:-1],points[1:]):
        if t<=b:
            u=smooth((t-a)/(b-a));return [x+(y-x)*u for x,y in zip(va,vb)]
    return points[-1][1]
def pose(name,t):
    posing.reset(rig)
    if name in ('Walking','Running'):
        duration=CLIPS[name][0];phase=t/duration;stride=.32 if name=='Walking' else .43;duty=.62 if name=='Walking' else .55
        root((0,0,-.028-.008*math.cos(phase*4*math.pi)))
        rot('Spine2',Z,2*math.sin(phase*2*math.pi));rot('Neck1',Z,-2*math.sin(phase*2*math.pi))
        for kind,side,off in [('front','L',0),('hind','R',0),('front','R',.5),('hind','L',.5)]:
            q=(phase+off)%1;s=stride*duty
            if q<duty:dy=-s/2+s*q/duty;dz=0;pitch=0
            else:
                u=(q-duty)/(1-duty);dy=s/2-s*smooth(u);dz=.045*math.sin(math.pi*u);pitch=12*math.sin(math.pi*u)
            leg(kind,side,(0,dy,dz),pitch)
        rot('Tail1',Z,5*math.sin(phase*2*math.pi));rot('Tail2',Z,3*math.sin(phase*2*math.pi-.5))
    elif name in ('Death','Dead'):
        t=1 if name=='Dead' else t
        # Native recoil, one front paw raised, then a low side collapse with the neck extended.
        roll,drop,neck,head,fold=keys(t,[(0,(0,0,0,0,0)),(.25,(0,0,-22,15,0)),(.45,(3,-.04,-35,12,.1)),(.75,(8,-.18,55,-48,.7)),(1,(8,-.23,90,-82,1))])
        root((0,0,drop));rot('Spine1',Y,roll);rot('Spine2',X,fold*10)
        rot('Neck1',X,neck*.55);rot('Neck2',X,neck*.45);rot('Head',X,head)
        for side in 'LR':
            sign=1 if side=='L' else -1
            leg('front',side,(sign*.10*fold,-.14*fold,0))
            leg('hind',side,(sign*.12*fold,.08*fold,0))
        rot('Jaw',X,8*math.sin(math.pi*t))
    else:
        if name=='Standing':
            phase=2*math.pi*t/2;root((0,0,-.003));rot('Neck1',X,1.2*math.sin(phase));rot('Head',Z,2*math.sin(phase));rot('Tail1',Z,3*math.sin(phase))
            paw=0
        elif name=='Attack':
            dy,dz,neck,head,paw,jaw=keys(t,[(0,(0,0,0,0,0,0)),(.20,(.01,0,-18,10,.04,6)),(.35,(-.035,-.035,52,-60,0,12)),(.52,(-.04,-.05,60,-70,0,8)),(.72,(-.015,-.02,28,-32,0,4)),(1,(0,0,0,0,0,0))])
            root((0,dy,dz));rot('Spine2',X,neck*.13);rot('Spine3',X,neck*.07)
            rot('Neck1',X,neck*.55);rot('Neck2',X,neck*.45);rot('Head',X,head);rot('Jaw',X,jaw)
        elif name=='Hit':
            u=t/.625;a=math.sin(math.pi*u)**2;root((0,.014*a,-.008*a));rot('Neck1',X,-16*a);rot('Head',X,8*a);paw=.045*a
        else:
            u=t/.625;a=math.sin(math.pi*u);root((0,0,-.003));rot('Head',Z,12*math.sin(2*math.pi*u)*a);rot('Head',X,5*a);rot('Tail1',Z,8*math.sin(2*math.pi*u)*a);paw=0
        for kind in ['front','hind']:
            for side in 'LR':leg(kind,side,(0,0,paw if kind=='front' and side=='L' else 0))
    low=float(co()[:,2].min())
    if name in ('Death','Dead'):root((0,0,-low+.002))
    elif low<-.003:root((0,0,-low))
