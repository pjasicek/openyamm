"""Native-led centaur actions, four planted hooves, rigid bow, fitted grip and animated nock."""
from pathlib import Path
import bpy,sys,json,math
import numpy as np
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parent/'mm6_rat_claude/scripts'));import posing as Q
bpy.ops.wm.open_mainfile(filepath=str(P/'work/corrected_uv_v2.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];eq=bpy.data.objects['Equipment'];sc=bpy.context.scene
G=json.loads((P/'work/equipment.json').read_text());sc.render.fps=48
for k in (1,2,3):G['finger_local']['LThumb'+str(k)]=Quaternion().slerp(Quaternion(G['finger_local']['LThumb'+str(k)]),.55 if k==1 else .7)
rest={b.name:b.matrix_local.copy()for b in rig.data.bones};handrest=Matrix(G['rest_hand_matrix']).to_3x3();bowrest=Matrix(G['bow_rest_matrix']).to_3x3()
centre_local=Vector(G['centre_hand_local']);tau=2*math.pi

def smooth(x):x=max(0,min(1,x));return x*x*(3-2*x)
def blend(a,b,t):return Vector(a).lerp(Vector(b),smooth(t))
def orient(name,R):
    b=rig.pose.bones[name];b.matrix=Matrix.Translation(b.head)@R.to_4x4();bpy.context.view_layer.update()
def bow(center,axis=(0,0,1),normal=(0,-1,0),pole=(.95,-.3,1.65)):
    y=Vector(axis).normalized();z=Vector(normal);z=(z-y*z.dot(y)).normalized();x=y.cross(z)
    B=Matrix((x,y,z)).transposed();H=B@bowrest.inverted()@handrest
    wrist=Vector(center)-H@centre_local
    Q.two_bone_ik(rig,'LArm','LForeArm',wrist,pole);orient('LHand',H)
    for name,q in G['finger_local'].items():rig.pose.bones[name].rotation_quaternion=q
    bpy.context.view_layer.update()
def right_hand(target,up=False):
    Q.two_bone_ik(rig,'RArm','RForeArm',target,(-.85,-.15,1.95 if up else 1.6))
    desired=Vector((0,-1,.1 if up else -.65)).normalized()
    R=rest['RHand'].to_3x3();R=R.col[1].rotation_difference(desired).to_matrix()@R
    orient('RHand',R)
    for n in ('Index','Middle','Ring','Pinky'):
        for k in (1,2,3):Q.rotate_world(rig,'R'+n+str(k),R.col[0],-18 if up else -10)

def leg(side,front,dy=0,lift=0):
    pre='Front'if front else'Hind';sg=1 if side=='L'else -1
    hoof=pre+'Hoof_'+side;ankle=rest[hoof].translation+Vector((0,dy,lift))
    if front:
        Q.two_bone_ik(rig,pre+'Upper_'+side,pre+'Lower_'+side,ankle,(sg*.32,-.15,.62))
    else:
        cannon=rest['HindCannon_'+side];hock=ankle-Vector((0,-.025,-.337))
        Q.two_bone_ik(rig,'HindUpper_'+side,'HindLower_'+side,hock,(sg*.36,-.1,.8))
        Q.aim_bone(rig,'HindCannon_'+side,ankle)
    orient(hoof,rest[hoof].to_3x3())

def gait(t,run=False):
    stride=1.15 if run else .7;duty=.52 if run else .62
    root=rig.pose.bones['Root'];M=root.matrix.copy();M.translation.z-=.24 if run else .10;root.matrix=M;bpy.context.view_layer.update()
    Q.rotate_world(rig,'HorseSpine','X',-2*math.sin(tau*t*2));Q.rotate_world(rig,'Spine','X',3 if run else 1)
    for side,phase in [('L',0),('R',.5)]:
        for front in (True,False):
            u=(t+phase+(0 if front else .5))%1
            if u<duty:dy=-stride/2+stride*u/duty;lift=0
            else:
                s=(u-duty)/(1-duty);dy=stride/2-stride*smooth(s);lift=(.24 if run else .15)*math.sin(math.pi*s)
            leg(side,front,dy,lift)

def floor():
    dg=bpy.context.evaluated_depsgraph_get();pts=[]
    for o in (body,):
        ev=o.evaluated_get(dg);m=ev.to_mesh();pts.extend([v.co.z for v in m.vertices if abs(v.co.x)+abs(v.co.y)>.02]);ev.to_mesh_clear()
    root=rig.pose.bones['Root'];M=root.matrix.copy();M.translation.z+=.008-min(pts);root.matrix=M;bpy.context.view_layer.update()

def pose(name,t):
    t=1 if name=='Dead'else t
    Q.reset(rig);rig.pose.bones['Arrow'].scale=(.001,)*3
    cycle=math.sin(tau*t)
    Q.rotate_world(rig,'Chest','X',.8*cycle);Q.rotate_world(rig,'Head','Z',2*math.sin(tau*t+.4))
    for k in range(1,6):Q.rotate_world(rig,'Tail'+str(k),'Z',(2+k*.7)*math.sin(tau*t-k*.38))
    carry=Vector((.52,-.87,1.43));bc=carry.copy();ba=Vector((0,-.14,1));rn=Vector((-.45,-.62,1.43));rup=False;pole=Vector((.95,-.3,1.65));bn=Vector((0,-1,0))
    if name in ('Walking','Running'):
        gait(t,name=='Running');bc.z-=.05;bc.y+=.035*cycle;rn.y+=.06*cycle
    elif name=='Fidget':
        Q.rotate_world(rig,'Head','Z',-28*math.sin(math.pi*t)**2);Q.rotate_world(rig,'Chest','Z',-5*math.sin(math.pi*t)**2)
        for k in range(1,6):Q.rotate_world(rig,'Tail'+str(k),'Z',12*math.sin(tau*t-k*.2))
    elif name=='Attack':
        # Reach quiver, nock, draw, release at 1.0 s, then recover.
        release=2/3;raise_=smooth((t-.18)/.23);recover=smooth((t-.68)/.32)
        bc=carry.lerp(Vector((.12,-1.27,2.05)),raise_*(1-recover));ba=Vector((0,-.05,1))
        if t<.20:rn=blend(rn,(-.49,-.37,1.68),t/.20)
        elif t<.36:rn=blend((-.49,-.37,1.68),(-.08,-1.02,2.02),(t-.20)/.16)
        elif t<release:rn=blend((-.08,-1.02,2.02),(-.22,-.78,2.18),(t-.36)/(release-.36))
        else:rn=blend((-.15,-.52,2.04),(-.45,-.62,1.43),(t-release)/.40)
        rup=True;Q.rotate_world(rig,'Chest','Z',-10*raise_*(1-recover));Q.rotate_world(rig,'Head','Z',10*raise_*(1-recover))
    elif name=='Cast':
        lift=math.sin(math.pi*t)**2;rn=rn.lerp(Vector((-.36,-.88,2.31)),lift);rup=True
        Q.rotate_world(rig,'Chest','X',-6*lift);Q.rotate_world(rig,'Head','X',-5*lift)
    elif name=='Hit':
        hit=math.sin(math.pi*smooth(t))**2
        Q.rotate_world(rig,'Spine','X',-13*hit);Q.rotate_world(rig,'Chest','Z',9*hit);bc+=Vector((.06,.10,.10))*hit;rn+=Vector((-.1,.1,.15))*hit
    elif name in ('Death','Dead'):
        t=1 if name=='Dead'else t
        rear=math.sin(math.pi*min(1,t/.65));fall=smooth((t-.28)/.6)
        Q.rotate_world(rig,'HorsePelvis','X',-21*rear)
        Q.rotate_world(rig,'Spine','X',-12*rear+32*fall)
        for side in ('L','R'):
            Q.rotate_world(rig,'FrontUpper_'+side,'X',-25*rear+12*fall)
            Q.rotate_world(rig,'FrontLower_'+side,'X',65*rear+28*fall)
            Q.rotate_world(rig,'HindUpper_'+side,'X',25*fall)
            Q.rotate_world(rig,'HindLower_'+side,'X',-48*fall)
            if fall<.15:leg(side,False)
        bc=carry.lerp(Vector((.25,-.67,2.72)),rear);rn=rn.lerp(Vector((-.35,-.58,2.60)),rear);ba=Vector((.8,-.1,.6)).lerp(Vector((0,-1,0)),fall);rup=True
        bc=bc.lerp(Vector((.28,-.85,1.65)),fall);pole=pole.lerp(Vector((.22,-.7,1.7)),fall);bn=bn.lerp(Vector((1,0,0)),fall)
    bow(bc,ba,bn,pole);right_hand(rn,rup)
    if name=='Attack'and .30<t<2/3:
        nock=rig.pose.bones['StringNock'].head.lerp(rig.pose.bones['RIndex3'].tail,smooth((t-.30)/.08))
        b=rig.pose.bones['StringNock'];M=b.matrix.copy();M.translation=nock;b.matrix=M
        a=rig.pose.bones['Arrow'];direction=(rig.pose.bones['Bow'].head+Vector((0,0,.055))-nock).normalized();R=Vector((0,-1,0)).rotation_difference(direction).to_matrix()@rest['Arrow'].to_3x3();a.matrix=Matrix.Translation(nock)@R.to_4x4();a.scale=(1,1,1)if t>.36 else(.001,)*3
    if name in ('Death','Dead'):
        fall=smooth(((1 if name=='Dead'else t)-.28)/.6)
        Q.rotate_world(rig,'Root','Y',90*fall);floor()
    bpy.context.view_layer.update()

clips={'Standing':48,'Walking':18,'Running':16,'Attack':36,'Cast':36,'Hit':21,'Death':42,'Dead':24,'Fidget':30}
for a in list(bpy.data.actions):bpy.data.actions.remove(a)
rig.animation_data_create();report={}
for name,n in clips.items():
    n*=2;previous={}
    a=bpy.data.actions.new(name);a.use_fake_user=True;rig.animation_data.action=a
    for f in range(n+1):
        sc.frame_set(f);pose(name,f/n)
        for b in rig.pose.bones:
            if b.name in previous and b.rotation_quaternion.dot(previous[b.name])<0:b.rotation_quaternion.negate()
            previous[b.name]=b.rotation_quaternion.copy()
            for path in ('location','rotation_quaternion','scale'):b.keyframe_insert(path,frame=f,group=b.name)
    for layer in a.layers:
        for strip in layer.strips:
            bag=strip.channelbag(a.slots[0])
            for fc in bag.fcurves:
                for key in fc.keyframe_points:key.interpolation='CONSTANT'if 'Arrow' in fc.data_path and fc.data_path.endswith('.scale')else'LINEAR'
    a['role']=name.lower();a['duration_seconds']=n/48
    if name=='Attack':a.pose_markers.new('impact').frame=48
    if name=='Cast':a.pose_markers.new('impact').frame=48
    report[name]={'frames':n+1,'fps':48,'duration_seconds':n/48}
rig.animation_data.action=bpy.data.actions['Standing'];sc.frame_set(0);sc.frame_start=0;sc.frame_end=96
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/animated_v1.blend'))
(P/'work/clips.json').write_text(json.dumps(report,indent=2)+'\n');print('CLIPS',report)
