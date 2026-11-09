"""Original reference-driven goblin motion. Bake analytic limb targets into editable FK actions via Blender MCP."""
import bpy
import math
import json
import sys
from pathlib import Path
from mathutils import Vector, Matrix, Quaternion, Euler

ROOT=Path(__file__).resolve().parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from model_common import look_at,active

SCENE='MM6 Goblin animation studio'
FPS=24
CLIPS={'Standing':(2.0,True),'Walk':(.75,True),'Attack':(.75,False),'Hit':(.75,False),
    'Death':(.625,False),'Corpse':(.125,False),'Fidget':(.75,True)}
STRIDE=.64
SPEED=STRIDE/.75

def lerp(a,b,t):
    if isinstance(a,(list,tuple)):return [x+(y-x)*t for x,y in zip(a,b)]
    return a+(b-a)*t

def key_parameters(keys,t):
    for i in range(len(keys)-1):
        ta,a=keys[i];tb,b=keys[i+1]
        if t<=tb:
            f=max(0,min(1,(t-ta)/(tb-ta)));f=f*f*(3-2*f)
            return {k:lerp(a[k],b[k],f) for k in a}
    return keys[-1][1].copy()

def base_parameters():
    return {'pelvis':(0,0,-.035),'lean':4.,'twist':0.,'head':(0,0,0),
        'right':(-.414,-.11,.96),'left':(.42,-.085,.93),'blade':(.309,-.951,0.),
        'feetR':(-.145,.025,.13),'feetL':(.145,.025,.13),'foot_pitchR':0.,'foot_pitchL':0.,
        'free_hand_turn':0.}

def control(**changes):
    p=base_parameters();p.update(changes);return p

ATTACK=[(0,control()),
    (.17,control(lean=7.,twist=-18.,right=(-.20,-.31,1.03),blade=(.82,-.28,.50),left=(.42,-.15,1.03))),
    (.34,control(lean=-3.,twist=-32.,right=(.19,-.36,1.37),blade=(.62,-.12,.78),left=(.29,-.30,1.17))),
    (.45,control(lean=2.,twist=-17.,right=(.14,-.40,1.34),blade=(.54,-.22,.81),left=(.28,-.34,1.10))),
    (.60,control(lean=12.,twist=24.,right=(-.35,-.40,1.13),blade=(-.94,-.28,.15),left=(.13,-.35,1.04))),
    (.76,control(lean=17.,twist=30.,right=(-.50,-.25,.95),blade=(-.92,-.37,-.12),left=(.13,-.23,.89))),
    (1,control())]

HIT=[(0,control()),
    (.20,control(lean=-9.,twist=12.,head=(0,0,24),left=(-.07,-.30,1.59),
        right=(-.45,-.26,1.02),blade=(-.15,-.40,.90),free_hand_turn=-60.)),
    (.40,control(lean=8.,twist=9.,head=(15,0,12),left=(-.06,-.31,1.53),
        right=(-.44,-.29,1.00),blade=(-.10,-.43,.90),free_hand_turn=-48.)),
    (.68,control(lean=11.,head=(10,0,0),left=(.14,-.29,1.20),right=(-.43,-.22,.96),blade=(0,-.65,.76))),
    (1,control())]

DEATH=[(0,control()),
    (.24,control(pelvis=(0,0,-.14),lean=25.,head=(12,0,0),right=(-.27,-.34,1.02),
        left=(.20,-.32,.88),blade=(.98,-.10,.10))),
    (.52,control(pelvis=(0,.02,-.43),lean=52.,head=(10,0,-12),right=(-.34,-.40,.42),
        left=(.42,-.41,.23),blade=(.92,-.36,.04),feetR=(-.17,.17,.14),feetL=(.19,.19,.14))),
    (.78,control(pelvis=(0,.10,-.70),lean=83.,twist=-8.,head=(0,15,-18),right=(-.54,-.52,.15),
        left=(.62,-.57,.09),blade=(.98,-.16,.02),feetR=(-.22,.67,.09),feetL=(.32,.56,.09),
        foot_pitchR=-65.,foot_pitchL=-55.,free_hand_turn=50.)),
    (1,control(pelvis=(0,.12,-.795),lean=89.,twist=-9.,head=(0,24,-14),right=(-.56,-.52,.125),
        left=(.65,-.58,.06),blade=(.98,-.16,.00),feetR=(-.25,.70,.105),feetL=(.35,.59,.105),
        foot_pitchR=-75.,foot_pitchL=-65.,free_hand_turn=65.))]

def walk_foot(phase,side):
    # Half-cycle stance translates backward relative to an actor advancing at SPEED; the world contact is fixed.
    phase%=1
    if phase<.5:
        y=-STRIDE/4+STRIDE*phase;lift=0.;pitch=0.
    else:
        s=(phase-.5)*2
        smooth=s*s*(3-2*s)
        y=STRIDE/4-STRIDE*.5*smooth
        lift=.115*math.sin(math.pi*s)**1.4
        pitch=18*math.sin(2*math.pi*s)
    return (side*.145,y+.025,.13+lift),pitch

def parameters(clip,t):
    if clip=='Attack':return key_parameters(ATTACK,t)
    if clip=='Hit':return key_parameters(HIT,t)
    if clip=='Death':return key_parameters(DEATH,t)
    if clip=='Corpse':return DEATH[-1][1].copy()
    p=base_parameters();wave=math.sin(2*math.pi*t)
    if clip=='Walk':
        p['feetL'],p['foot_pitchL']=walk_foot(t,1)
        p['feetR'],p['foot_pitchR']=walk_foot(t+.5,-1)
        p['pelvis']=(.014*wave,0,-.052-.014*math.cos(4*math.pi*t))
        p['lean']=9+3*math.sin(4*math.pi*t);p['twist']=6*wave
        p['right']=(-.42,-.07-.13*math.cos(2*math.pi*t),1.00+.04*wave)
        p['left']=(.42,-.07+.15*math.cos(2*math.pi*t),.99-.04*wave)
        p['blade']=(.32,-.88,.25*wave-.12)
        p['head']=(3*math.sin(4*math.pi*t),0,-4*wave)
    else:
        p['pelvis']=(.006*wave,0,-.035+.003*math.sin(2*math.pi*t))
        p['lean']=4+.5*wave;p['right']=(-.414,-.11,.96+.003*wave)
        if clip=='Fidget':
            p['head']=(1.5*wave,0,9*math.sin(2*math.pi*t)**3)
            p['left']=(.42,-.085-.018*wave,.93+.012*wave)
    return p

def chain_joint(a,b,l1,l2,pole):
    axis=b-a;distance=axis.length
    distance=max(abs(l1-l2)+.0001,min(l1+l2-.0001,distance));axis.normalize()
    b=a+axis*distance
    along=(l1*l1-l2*l2+distance*distance)/(2*distance)
    height=math.sqrt(max(0,l1*l1-along*along))
    direction=Vector(pole)-a;direction-=axis*direction.dot(axis);direction.normalize()
    return a+along*axis+height*direction,b

class PoseBuilder:
    def __init__(self,rig):
        self.rig=rig;self.bones=rig.data.bones
        self.rest={b.name:b.matrix_local.copy() for b in self.bones}
        self.targets={}

    def inherited(self,name):
        b=self.bones[name]
        if b.parent:return self.targets[b.parent.name] @ self.rest[b.parent.name].inverted() @ self.rest[name]
        return self.rest[name].copy()

    def fk(self,name,degrees=(0,0,0)):
        rest=self.rest[name].to_quaternion()
        q=Euler(tuple(math.radians(x) for x in degrees),'XYZ').to_quaternion()
        local=rest.inverted() @ q @ rest
        self.targets[name]=self.inherited(name) @ local.to_matrix().to_4x4()

    def aim(self,name,a,b):
        rest=self.bones[name];original=rest.tail_local-rest.head_local
        q=original.rotation_difference(b-a) @ self.rest[name].to_quaternion()
        self.targets[name]=Matrix.Translation(a) @ q.to_matrix().to_4x4()

    def oriented(self,name,point,rotation):
        self.targets[name]=Matrix.Translation(point) @ rotation.to_matrix().to_4x4() @ self.rest[name].to_quaternion().to_matrix().to_4x4()

    def apply(self):
        for b in self.bones:
            name=b.name
            if name not in self.targets:self.targets[name]=self.inherited(name)
            kw={}
            if b.parent:kw={'parent_matrix':self.targets[b.parent.name],'parent_matrix_local':self.rest[b.parent.name]}
            self.rig.pose.bones[name].matrix_basis=b.convert_local_to_pose(
                self.targets[name],self.rest[name],invert=True,**kw)
        bpy.context.view_layer.update()

def pose(rig,clip,t):
    p=parameters(clip,t);builder=PoseBuilder(rig);bones=builder.bones
    # Root's rest matrix aligns Blender bone Y with world Z. Identity would rotate the entire actor onto its back.
    builder.targets['root']=builder.rest['root'].copy()
    settle=0.
    if clip in {'Death','Corpse'}:settle=1 if clip=='Corpse' else max(0,min(1,(t-.52)/.48))
    settle=settle*settle*(3-2*settle)
    # During the final fall the spine unfolds into a flat prone body; retaining the standing bend arches it above ground.
    builder.fk('pelvis',(p['lean']*(.65+.35*settle),0,p['twist']*.55))
    builder.targets['pelvis'].translation+=Vector(p['pelvis'])
    builder.fk('spine',(p['lean']*.20*(1-settle),0,p['twist']*.25))
    builder.fk('chest',(p['lean']*.15*(1-settle),0,p['twist']*.20))
    builder.fk('neck');builder.fk('head',p['head'])
    for side,label in [(-1,'R'),(1,'L')]:
        upper='thigh.'+label;lower='shin.'+label;foot='foot.'+label
        a=builder.inherited(upper).translation;target=Vector(p['feet'+label])
        pole=(side*.17,-1.0,.5)
        if clip in {'Death','Corpse'}:
            weight=1 if clip=='Corpse' else max(0,min(1,(t-.40)/.22))
            weight=weight*weight*(3-2*weight)
            pole=lerp(pole,(side*.9,.15,.45),weight)
        joint,target=chain_joint(a,target,bones[upper].length,bones[lower].length,pole)
        builder.aim(upper,a,joint);builder.aim(lower,joint,target)
        q=Euler((math.radians(p['foot_pitch'+label]),0,math.radians(side*5)),'XYZ').to_quaternion()
        builder.oriented(foot,target,q)
        builder.fk('clavicle.'+label)
        upper='upper_arm.'+label;lower='forearm.'+label;hand='hand.'+label
        a=builder.inherited(upper).translation;target=Vector(p['right' if side<0 else 'left'])
        pole=(side*.80,.20,1.12)
        joint,target=chain_joint(a,target,bones[upper].length,bones[lower].length,pole)
        builder.aim(upper,a,joint);builder.aim(lower,joint,target)
        if side<0:
            q=Vector((.309,-.951,0)).normalized().rotation_difference(Vector(p['blade']).normalized())
        else:
            q=(bones[lower].tail_local-bones[lower].head_local).rotation_difference(target-joint)
            q=q @ Quaternion((0,1,0),math.radians(p['free_hand_turn']))
            if clip in {'Death','Corpse'}:
                weight=1 if clip=='Corpse' else max(0,min(1,(t-.52)/.26))
                rest_hand=bones[hand].tail_local-bones[hand].head_local
                flat=rest_hand.rotation_difference(Vector((.95,-.3,0)))
                q=q.slerp(flat,weight)
        builder.oriented(hand,target,q)
    # Select each strip's modest hinge rotation against both posed thigh capsules and the floor.
    # This is deterministic authored secondary motion baked to ordinary bones, not a runtime cloth solver.
    for i in range(22):
        name='skirt.%02d'%i;a=i*2*math.pi/22
        length=.205+.026*math.sin(i*2.7)+.018*math.cos(i*1.3)
        rest=builder.rest[name];base=builder.inherited(name)
        axis=rest.to_quaternion().inverted() @ Vector((-math.cos(a),-math.sin(a),0))
        points=[]
        for u in [.45,.72,1.]:
            for edge in [-.10,0,.10]:
                angle=a+edge
                v=Vector(((.176+.023*u)*math.sin(angle),-(.125+.025*u)*math.cos(angle),.998-length*u))
                points.append(rest.inverted() @ v)
        best=None
        desired=3*math.sin(2*math.pi*t+i*.4) if clip=='Walk' else 0.
        for degrees in range(-80,81,4):
            transform=base @ Quaternion(axis,math.radians(degrees)).to_matrix().to_4x4()
            penalty=.000015*(degrees-desired)**2
            for local in points:
                v=transform @ local
                if clip in {'Death','Corpse'}:penalty+=max(0,.012-v.z)**2*5000
                for label in ['R','L']:
                    hip=builder.targets['thigh.'+label].translation
                    knee=builder.targets['shin.'+label].translation
                    d=knee-hip;u=max(0,min(1,(v-hip).dot(d)/d.length_squared))
                    radius=.107-.022*u
                    overlap=max(0,radius-(v-(hip+u*d)).length)
                    penalty+=overlap*overlap*2000
            if best is None or penalty<best[0]:best=(penalty,transform)
        builder.targets[name]=best[1]
    builder.apply()
    return p

def curves(action):
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                yield from bag.fcurves

def build(review_poses=None):
    assert bpy.data.scenes.get(SCENE) is None,'Archive the current animation studio before replacing it'
    bpy.context.window.scene=bpy.data.scenes['MM6 Goblin rig studio'];bpy.ops.scene.new(type='FULL_COPY')
    scene=bpy.context.window.scene;scene.name=SCENE
    rig=next(o for o in scene.objects if o.type=='ARMATURE');active(rig)
    scene.render.fps=FPS
    for b in rig.pose.bones:b.rotation_mode='QUATERNION'
    rig.animation_data_clear()
    manifest={'fps':FPS,'walk_stride_m':STRIDE,'walk_speed_m_s':SPEED,
        'walk_contact':'Left foot starts stance; stance duration 0.375 s. In-place + forward -Y translation at documented speed.',
        'status':'First motion authoring pass; requires contact, intersection and playback review','clips':{}}
    for clip,(duration,loop) in CLIPS.items():
        rig.animation_data_clear();action=None;previous={}
        # The rapid knee-plane change in Death needs subframe FK keys to preserve its solved foot contacts.
        intervals=round(duration*FPS)*(4 if clip=='Death' else 1)
        for sample in range(intervals+1):
            frame=1+duration*FPS*sample/intervals
            pose(rig,clip,sample/intervals)
            for b in rig.pose.bones:
                q=b.rotation_quaternion.copy()
                if b.name in previous and previous[b.name].dot(q)<0:q.negate();b.rotation_quaternion=q
                previous[b.name]=q.copy()
                for prop in ['location','rotation_quaternion','scale']:b.keyframe_insert(data_path=prop,frame=frame,group=b.name)
            action=rig.animation_data.action
        action.name=clip;action.use_fake_user=True
        for curve in curves(action):
            for key in curve.keyframe_points:key.interpolation='LINEAR'
        manifest['clips'][clip]={'action':action.name,'duration_seconds':duration,'frame_start':1,
            'frame_end':1+duration*FPS,'loop':loop,'samples':intervals+1}
    rig.animation_data.action=bpy.data.actions[manifest['clips']['Standing']['action']]
    scene.frame_start=1;scene.frame_end=49;scene.frame_set(1)
    rig['animation_state']='Seven first-pass clips; use animation_data.action to choose; clear action and reset pose for editing.'
    (ROOT/'animations').mkdir(exist_ok=True)
    (ROOT/'animations/manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    bpy.data.libraries.write(str(ROOT/'animations/animation_library.blend'),{scene,*[
        bpy.data.actions[v['action']] for v in manifest['clips'].values()]},fake_user=True)
    camera=scene.camera;camera.data.ortho_scale=2.65;camera.location=(-3.0,-5,1.12);look_at(camera,(0,0,.94))
    scene.render.resolution_x=700;scene.render.resolution_y=760;scene.cycles.samples=16
    if review_poses is None:
        review_poses=[('Standing',0),('Walk',0),('Walk',.5),('Attack',.34),('Attack',.60),('Hit',.20),('Death',.52),('Corpse',1)]
    for clip,t in review_poses:
        rig.animation_data.action=bpy.data.actions[manifest['clips'][clip]['action']]
        frame=1+t*CLIPS[clip][0]*FPS;scene.frame_set(int(frame),subframe=frame-int(frame))
        scene.render.filepath=str(ROOT/'review'/f'motion_v6_{clip.lower()}_{t:.2f}.png')
        bpy.ops.render.render(write_still=True)
    rig.animation_data.action=bpy.data.actions[manifest['clips']['Standing']['action']];scene.frame_set(1)
    print(json.dumps(manifest))

if __name__=='__main__':build()
