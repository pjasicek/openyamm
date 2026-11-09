"""Bird flight: proximal downstroke, folding return stroke, feather lag and talon-first strike."""
import json,math,sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parent/'mm6_bat_claude/scripts'))
import posing
bpy.ops.wm.open_mainfile(filepath=str(P/('work/uv_master.blend' if '--uv' in sys.argv else 'work/rig_v1.blend')))
for action in list(bpy.data.actions):bpy.data.actions.remove(action)
rig=bpy.data.objects['Thunderbird_Rig'];mesh=bpy.data.objects['Thunderbird']
D=json.loads((P/'work/rig.json').read_text());scene=bpy.context.scene;scene.render.fps=FPS=24
FULL='--full' in sys.argv
rig.animation_data_create()
def smooth(t):
    t=max(0,min(1,t));return t*t*(3-2*t)
def envelope(t,a,b,c,d):return smooth((t-a)/(b-a))*(1-smooth((t-c)/(d-c)))
def rot(name,axis,angle):posing.rotate_world(rig,name,axis,angle)
def coords():return np.array([tuple(v.co) for v in mesh.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.vertices])
def pose(role,t):
    posing.reset(rig)
    phase=math.tau*t
    up=-34+28*math.cos(phase);elbow=-4+9*math.cos(phase-.4)
    fold=12*max(0,-math.sin(phase));tip=7*math.sin(phase-.7)
    pitch=2*math.sin(phase);roll=1.3*math.sin(phase);head=-pitch*.8
    thigh=shin=foot=0.;tail=-pitch*.4;shift=Vector((0,0,.004*math.cos(phase+math.pi)))
    if role in ('Attack','Cast'):
        rear=envelope(t,0,.4,.55,.875);strike=envelope(t,.55,.875,.92,29/24)
        up=18+6*rear-12*strike;elbow=8+2*rear-12*strike;fold=6*rear
        pitch=-20*rear-48*strike;head=12*rear+28*strike;roll=0
        thigh=-65*rear-115*strike;shin=20*rear+20*strike;foot=-12*rear-15*strike
        tail=18*rear;shift=Vector((0,.015*rear-.04*strike,.005*rear));tip=4*rear
        if role=='Cast':
            pitch=-12*rear+4*strike;head=-8*rear+12*strike;thigh=-12*rear;shin=foot=0
            up=4+12*rear-20*strike;elbow=8*rear;tail=8*rear
            shift=Vector((0,.005*rear-.018*strike,0))
    elif role=='Hit':
        hit=envelope(t,0,.125,.25,.75);pitch=-20*hit;head=-15*hit;roll=10*hit
        up=18+12*hit;elbow=18*hit;fold=25*hit;shift=Vector((0,.03*hit,.01*hit))
    elif role in ('Death','Dead'):
        t=.625 if role=='Dead' else t
        u=smooth(t/.625);shock=envelope(t,0,.125,.2,.4)
        up=-55*u+25*shock;elbow=-5*u;fold=8*u+100*max(0,math.sin(math.pi*u))**.5;tip=0
        pitch=-20*shock+5*u;roll=170*u;head=12*u;thigh=-12*u;shin=10*u;foot=0;tail=5*u
        shift=Vector((0,0,0))
    elif role=='Stress':
        up=-20+65*math.cos(phase);elbow=25*math.sin(phase);fold=22*math.sin(phase)
        pitch=20*math.sin(phase);head=-pitch;thigh=-95*smooth(t/.5);shin=25;roll=12*math.sin(phase)
    root=rig.pose.bones['Root'];root.matrix=Matrix.Translation(shift)@root.matrix;bpy.context.view_layer.update()
    rot('Root','X',pitch);rot('Root','Y',0 if role in ('Death','Dead') else roll);rot('Neck','X',head*.45);rot('Head','X',head*.55);rot('Tail','X',tail)
    for side,sign in [('L',1),('R',-1)]:
        rot('UpperWing_'+side,'Y',-sign*up)
        rot('ForeWing_'+side,'Y',-sign*elbow)
        if role in ('Death','Dead'):
            rot('UpperWing_'+side,'Z',sign*fold*.65)
            rot('ForeWing_'+side,'Z',sign*fold*.2)
            rot('HandWing_'+side,'Z',sign*fold*.15)
        else:
            rot('ForeWing_'+side,'Z',sign*fold*.4)
            rot('HandWing_'+side,'Z',sign*fold)
        rot('HandWing_'+side,'Y',sign*tip)
        rot('Thigh_'+side,'X',thigh);rot('Shin_'+side,'X',shin);rot('Foot_'+side,'X',foot)
    for part,feather in D['feathers'].items():
        sign=1 if feather['side']=='L' else -1
        amount=tip*.28*(.5+abs(feather['tip'][0]))
        rot(feather['bone'],'Y',sign*amount)
    for part,toe in D['toes'].items():
        if role=='Attack':rot(toe['bone'],'X',-22*strike)
    if role in ('Death','Dead'):
        # Fold in body space before rolling, so a spread wing cannot vault the body upward.
        rot('Root','Y',roll)
        # Body and wing tips settle together; no added flight hover offset.
        low=float(coords()[:,2].min());root=rig.pose.bones['Root']
        root.matrix=Matrix.Translation((0,0,-low+.001))@root.matrix;bpy.context.view_layer.update()
    return float(coords()[:,2].min())
clips={'Fly':(1.,True),'Attack':(29/24,False),'Stress':(1.,True)}
if FULL:clips={'Fly':(1.,True),'Attack':(29/24,False),'Cast':(29/24,False),'Hit':(.75,False),'Death':(.625,False),'Dead':(1.,False)}
report={}
for name,(duration,loop) in clips.items():
    rig.animation_data.action=None
    action=bpy.data.actions.new(name);action.use_fake_user=True;previous={};samples=[]
    count=round(duration*FPS)
    for f in range(count+1):
        rig.animation_data.action=None;scene.frame_set(f)
        low=pose(name,(f/FPS)%duration if loop else f/FPS);samples.append(low)
        values={b.name:(b.location.copy(),b.rotation_quaternion.copy()) for b in rig.pose.bones}
        rig.animation_data.action=action
        for bone in rig.pose.bones:
            loc,q=values[bone.name]
            if bone.name in previous and q.dot(previous[bone.name])<0:q.negate()
            previous[bone.name]=q.copy();bone.location=loc;bone.rotation_quaternion=q
            bone.keyframe_insert('location',frame=f);bone.keyframe_insert('rotation_quaternion',frame=f)
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    for k in curve.keyframe_points:k.interpolation='LINEAR'
    if name == 'Death':
        # Rotation interpolation can sweep a feather below the floor between grounded keys.
        rig.animation_data.action=action
        lift=np.zeros(count+1)
        for frame in np.arange(0,count+.01,.125):
            scene.frame_set(int(frame),subframe=float(frame%1))
            correction=max(0,.001-float(coords()[:,2].min()))
            lift[int(frame)]=max(lift[int(frame)],correction)
            lift[min(count,int(frame)+1)]=max(lift[min(count,int(frame)+1)],correction)
        for frame,amount in enumerate(lift):
            scene.frame_set(frame)
            root=rig.pose.bones['Root']
            root.matrix=Matrix.Translation((0,0,float(amount)))@root.matrix
            root.keyframe_insert('location',frame=frame)
    report[name]={'seconds':duration,'frames':count,'loop':loop,'minimum_z':min(samples)}
    print('CLIP',name,report[name],flush=True)
(P/'work/clip_manifest.json').write_text(json.dumps(report,indent=2)+'\n')
rig.animation_data.action=bpy.data.actions['Fly'];scene.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(P/('work/uv_master.blend' if '--uv' in sys.argv else ('work/anim_v1.blend' if FULL else 'work/pilot_v1.blend'))))
(P/'review/viewer').mkdir(parents=True,exist_ok=True)
for o in scene.objects:o.select_set(o in (rig,mesh))
bpy.ops.export_scene.gltf(filepath=str(P/'review/viewer/pilot.glb'),use_selection=True,export_format='GLB',export_yup=True,export_skins=True,export_animations=True,export_animation_mode='ACTIONS',export_frame_range=False,export_materials='NONE')
scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.light='STUDIO';scene.display.shading.show_cavity=True
scene.display.shading.color_type='SINGLE';scene.display.shading.single_color=(.55,.65,.72)
scene.world=bpy.data.worlds.new('ReviewWorld');scene.world.color=(.07,.07,.07)
scene.render.resolution_x=1100;scene.render.resolution_y=800;scene.render.resolution_percentage=100
cam=bpy.data.objects.new('Camera',bpy.data.cameras.new('Camera'));scene.collection.objects.link(cam);scene.camera=cam
cam.data.type='ORTHO';cam.data.ortho_scale=1.50
shots=[('Fly',0),('Fly',.25),('Fly',.5),('Fly',.75),('Attack',.4),('Attack',.875),('Stress',.5)] if not FULL else [(n,min(.2,d[0])) for n,d in clips.items()]+[('Death',.625),('Dead',.8),('Cast',.875)]
for name,t in shots:
    rig.animation_data.action=bpy.data.actions[name];frame=t*FPS;scene.frame_set(int(frame),subframe=frame%1)
    for view,direction in [('quarter',(1,-1.5,.65)),('side',(1,0,.05)),('front',(0,-1,.05))]:
        center=Vector((0,0,.13));cam.location=center+Vector(direction).normalized()*3
        cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
        scene.render.filepath=str(P/f'review/{name}_{t:.3f}_{view}.png');bpy.ops.render.render(write_still=True)
