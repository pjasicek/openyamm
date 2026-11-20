"""Native-informed gallop, hind-supported rear and collapse, with rigid-hoof IK contacts."""
from pathlib import Path
import sys, json, math
import bpy
import numpy as np
from mathutils import Vector, Matrix, Quaternion

P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P.parent/'mm6_rat_claude/scripts'))
import posing as pose
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_v1.blend'))
rig, mesh = bpy.data.objects['Unicorn_Rig'], bpy.data.objects['Unicorn']
sc = bpy.context.scene
FPS = sc.render.fps = 48
for old in list(bpy.data.actions):
    bpy.data.actions.remove(old)
pose.reset(rig)
rest = {b.name:b.matrix.copy() for b in rig.pose.bones}
X, Y, Z = Vector((1,0,0)), Vector((0,1,0)), Vector((0,0,1))
points = np.array([tuple(v.co) for v in mesh.data.vertices])
foot = {}
for kind in ('Front','Hind'):
    for side,sign in [('L',1),('R',-1)]:
        name = f'{kind}Hoof_{side}'
        mask = (points[:,0]*sign>0)&((points[:,1]<0)==(kind=='Front'))&(points[:,2]<.035)
        foot[kind,side] = rest[name].translation.copy()-Vector((0,0,float(points[mask,2].min())))

def rot(name, axis, degrees):
    pose.rotate_world(rig, name, axis, degrees)

def smooth(t):
    t = max(0,min(1,t))
    return t*t*(3-2*t)

def leg(kind, side, offset=Vector(), pitch=0, articulate=False):
    hoof, pastern = f'{kind}Hoof_{side}', f'{kind}Pastern_{side}'
    upper, lower = ((f'UpperArm_{side}',f'ForeArm_{side}') if kind=='Front'
                    else (f'Thigh_{side}',f'Shin_{side}'))
    target = foot[kind,side]+offset
    rotation = Quaternion(X,math.radians(pitch))
    rest_vector = rest[hoof].translation-rest[pastern].translation
    lower_vector = rotation@rest_vector
    pastern_rotation = rotation
    if articulate:
        direction = (target-rig.pose.bones[upper].head).normalized()
        lower_vector = direction*rest_vector.length
        pastern_rotation = rest_vector.normalized().rotation_difference(direction)
    carpus = target-lower_vector
    pole = carpus+Vector((.012 if side=='L' else -.012,.35 if kind=='Front' else -.35,.04))
    pose.two_bone_ik(rig,upper,lower,carpus,pole)
    for name in (pastern,hoof):
        bone = rig.pose.bones[name]
        q = (pastern_rotation if name==pastern else rotation)@rest[name].to_quaternion()
        bone.matrix = Matrix.LocRotScale(bone.head.copy(),q,Vector((1,1,1)))
        bpy.context.view_layer.update()

def body(drop=-.016,pitch=0,roll=0,head=0,yaw=0,travel=0):
    pose.reset(rig)
    root = rig.pose.bones['Spine1']
    root.matrix = Matrix.Translation((0,travel,drop))@root.matrix
    bpy.context.view_layer.update()
    rot('Spine1',X,pitch)
    rot('Spine1',Y,roll)
    for name,weight in [('Neck1',.25),('Neck2',.35),('Head',.4)]:
        rot(name,X,head*weight)
        rot(name,Z,yaw*weight)

def tail(phase, amplitude=3, lift=0):
    for i in range(1,6):
        rot(f'Tail{i}',Z,amplitude*(i/5)*math.sin(2*math.pi*phase-.55*i))
        rot(f'Tail{i}',X,lift if i==1 else 0)

def stand(t):
    s = math.sin(math.pi*t)
    body(drop=-.016+.001*s,head=1.5*s,yaw=2*s)
    for key in foot:
        leg(*key)
    tail(t/2,2)

STRIDE = .64
DUTY = .30
CONTACTS = {('Hind','L'):0,('Hind','R'):.12,('Front','L'):.34,('Front','R'):.46}

def gait(t, running=False):
    period = .75 if running else 1.0
    phase = t/period%1
    airborne = math.sin(math.pi*(phase-.76)/.24)**2 if phase>.76 else 0
    body(drop=-.045+.014*airborne-.006*math.sin(2*math.pi*phase),
         pitch=2.5*math.sin(2*math.pi*(phase-.1)),head=-2*math.sin(2*math.pi*phase))
    for key,start in CONTACTS.items():
        q = (phase-start)%1
        distance = STRIDE*DUTY
        if q<DUTY:
            dy = -distance/2+STRIDE*q
            dz = pitch = 0
        else:
            u = (q-DUTY)/(1-DUTY)
            dy = distance/2-distance*smooth(u)
            dz = (.11 if key[0]=='Front' else .08)*math.sin(math.pi*u)**1.5
            pitch = -32*math.sin(math.pi*u)
        # Centre each stride under the limb, removing the generated model's staggered rest stance.
        target_y = -.19 if key[0]=='Front' else .19
        dy += target_y-foot[key].y
        leg(*key,Vector((0,dy,dz)),pitch,articulate=True)
    tail(phase,4,14)

def keyed(keys,t):
    for (a,va),(b,vb) in zip(keys,keys[1:]):
        if t<=b:
            u = smooth((t-a)/(b-a))
            return {k:va.get(k,0)+(vb.get(k,0)-va.get(k,0))*u for k in va.keys()|vb.keys()}
    return keys[-1][1]

def action(t,kind):
    if kind in ('Attack','Cast'):
        keys = [(0,{}),(.25,{'pitch':-18,'head':12,'lift':.16,'back':.035}),
                (.55,{'pitch':-29,'head':20,'lift':.25,'back':.065}),
                (.85,{'pitch':-18,'head':24,'lift':.18,'back':.04}),
                (1.125,{'pitch':4,'head':24,'travel':-.015}),
                (1.25,{'head':14}), (1.50,{})]
    elif kind=='Hit':
        keys = [(0,{}),(.125,{'head':-12,'yaw':-9,'travel':.015,'sag':-.015}),
                (.375,{'head':7,'yaw':4}),(.625,{})]
    else:
        keys = [(0,{}),(.18,{'head':-6,'lift':.055}),(.4,{'head':3,'lift':.04}),(.625,{})]
    a = keyed(keys,t)
    body(drop=-.025+a.get('sag',0),pitch=a.get('pitch',0),head=a.get('head',0),
         yaw=a.get('yaw',0)+(3*math.sin(math.pi*t/1.5) if kind=='Cast' else 0),
         travel=a.get('travel',0))
    for k,s in foot:
        lift = a.get('lift',0) if k=='Front' else 0
        if kind=='Fidget' and s=='R':
            lift = 0
        leg(k,s,Vector((0,a.get('back',0) if k=='Front' else 0,lift)),
            -35*smooth(lift/.15) if k=='Front' else 0,articulate=True)
    tail(t,3,max(0,-a.get('pitch',0))+6)

def evaluated():
    obj = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get())
    data = obj.to_mesh()
    co = np.array([tuple(v.co) for v in data.vertices])
    obj.to_mesh_clear()
    return co

def death(t):
    a = keyed([(0,{'drop':-.016}),(.18,{'pitch':-18,'drop':-.025,'head':-5}),
               (.35,{'pitch':-28,'roll':35,'drop':-.08}),
               (.62,{'pitch':-8,'roll':88,'drop':-.25,'head':10}),
               (.75,{'pitch':-4,'roll':92,'drop':-.28,'head':14})],t)
    body(drop=a['drop'],pitch=a.get('pitch',0),roll=a.get('roll',0),head=a.get('head',0))
    u = smooth(t/.45)
    for side in 'LR':
        rot(f'UpperArm_{side}',X,-32*u)
        rot(f'ForeArm_{side}',X,65*u)
        rot(f'Thigh_{side}',X,-18*u)
        rot(f'Shin_{side}',X,35*u)
        rot(f'HindPastern_{side}',X,-20*u)
    # Fold the underside legs so the flank, rather than a dangling hoof, supports the corpse.
    rot('UpperArm_L',Z,-28*u)
    rot('Thigh_L',Z,-22*u)
    tail(.25,4*u,12*u)
    co = evaluated()
    root = rig.pose.bones['Spine1']
    root.matrix = Matrix.Translation((0,0,-float(co[:,2].min())))@root.matrix
    bpy.context.view_layer.update()

clips = {'Standing':(2,True,stand),'Walking':(1,True,gait),
         'Running':(.75,True,lambda t:gait(t,True)),
         'Attack':(1.5,False,lambda t:action(t,'Attack')),
         'Cast':(1.5,False,lambda t:action(t,'Cast')),
         'Hit':(.625,False,lambda t:action(t,'Hit')),
         'Fidget':(.625,False,lambda t:action(t,'Fidget')),
         'Death':(.75,False,death),'Dead':(1,False,lambda t:death(.75))}
tail_ids = [v.index for v in mesh.data.vertices if
            any(mesh.vertex_groups[g.group].name.startswith('Tail') and g.weight>.5 for g in v.groups)]
report = {}
for name,(seconds,loop,fn) in clips.items():
    rig.animation_data_create()
    rig.animation_data.action = None
    n = round(seconds*FPS)
    frames = []
    lowest = 1
    for f in range(n+1):
        fn((f%n)/FPS if loop else f/FPS)
        if name not in ('Death','Dead'):
            for attempt in range(40):
                if float(evaluated()[tail_ids,2].min())>=.004:
                    break
                rot('Tail1',X,2)
        co = evaluated()
        assert np.isfinite(co).all()
        lowest = min(lowest,float(co[:,2].min()))
        frames.append({b.name:(b.location.copy(),b.rotation_quaternion.copy(),b.scale.copy())
                       for b in rig.pose.bones})
    act = bpy.data.actions.new(name)
    act.use_fake_user = True
    rig.animation_data.action = act
    previous = {}
    for f,frame in enumerate(frames,1):
        for bone in rig.pose.bones:
            loc,q,scale = frame[bone.name]
            if bone.name in previous and q.dot(previous[bone.name])<0:
                q = -q
            previous[bone.name] = q
            bone.location,bone.rotation_quaternion,bone.scale = loc,q,scale
            for channel in ('location','rotation_quaternion','scale'):
                bone.keyframe_insert(channel,frame=f)
    report[name] = {'duration':n/FPS,'loop':loop,'minimum_z':lowest}
    print(name,report[name],flush=True)
rig.animation_data.action = bpy.data.actions['Standing']
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/anim_v1.blend'))
(P/'work/animation_report.json').write_text(json.dumps(report,indent=2)+'\n')
assert min(x['minimum_z'] for x in report.values())>-.015, 'Floor penetration requires repair'
