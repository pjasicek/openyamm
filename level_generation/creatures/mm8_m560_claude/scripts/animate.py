"""Native-inspired wyvern motion, 24 fps; no imported humanoid clips or gameplay timing changes."""
from pathlib import Path
import sys,math,json
import bpy
import numpy as np
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
from common import posing as Q,coordinates,render
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_v1.blend'))
rig=bpy.data.objects['Wyvern_Rig'];mesh=bpy.data.objects['Wyvern'];FPS=24
sc=bpy.context.scene;sc.render.fps=FPS
# Fixed clearance covers Fly/Attack/Hit; moving wing tips must not translate the body.
AIRBORNE_HEIGHT=.405
material=bpy.data.materials.new('Wyvern_A');material.use_nodes=True;material.use_backface_culling=False
material.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.2,.32,.15,1)
material.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.85
mesh.data.materials.clear();mesh.data.materials.append(material)
rest=coordinates(mesh)
vg={g.index:g.name for g in mesh.vertex_groups}
dom=[vg[max(v.groups,key=lambda g:g.weight).group] for v in mesh.data.vertices]
body=np.array([n.startswith(('Spine','Neck','Head','Jaw','Tail')) for n in dom])
wing_masks={s:np.array([n.endswith('_'+s) and 'Wing' in n for n in dom]) for s in 'LR'}
wing_flat={}
for side in 'LR':
    points=rest[wing_masks[side]];c=points-points.mean(0)
    normal=np.linalg.eigh(c.T@c)[1][:,0]
    if normal[2]<0:normal=-normal
    wing_flat[side]=Vector(normal).rotation_difference(Vector((0,0,1)))

def smooth(t):
    t=max(0,min(1,t));return t*t*(3-2*t)

def keys(sequence,t):
    for (a,va),(b,vb) in zip(sequence,sequence[1:]):
        if t<=b:
            u=smooth((t-a)/(b-a));return {k:va.get(k,0)*(1-u)+vb.get(k,0)*u for k in va.keys()|vb.keys()}
    return sequence[-1][1]

def rotate(name,axis,angle):
    Q.rotate_world(rig,name,axis,angle)

def translate(z=0,y=0):
    b=rig.pose.bones['Spine1'];b.matrix=Matrix.Translation((0,y,z))@b.matrix;bpy.context.view_layer.update()

def pose(p):
    Q.reset(rig)
    translate(AIRBORNE_HEIGHT+p.get('bob',0),p.get('reach',0))
    rotate('Spine1','X',p.get('pitch',0));rotate('Spine1','Y',p.get('roll',0))
    for i in range(1,6):
        rotate(f'Neck{i}','X',p.get('neck',0)/5)
        rotate(f'Neck{i}','Z',p.get('neck_yaw',0)/5)
    rotate('Head','X',p.get('head',0));rotate('Jaw','X',p.get('jaw',0))
    for i in range(1,10):
        rotate(f'Tail{i}','X',p.get('tail',0)*(0.6+0.05*i))
        rotate(f'Tail{i}','Z',p.get('tail_yaw',0)*math.sin(i*.4+p.get('phase',0)))
    for side,s in [('L',1),('R',-1)]:
        rotate('Thigh_'+side,'X',p.get('leg',0))
        rotate('Shin_'+side,'X',p.get('shin',0))
        rotate('Foot_'+side,'X',p.get('foot',0))
        rotate('UpperWing_'+side,'Y',-s*p.get('wing',0))
        rotate('ForeWing_'+side,'Y',-s*p.get('elbow',0))
        rotate('ForeWing_'+side,'Z',s*p.get('fold',0))
        for k in range(1,5):rotate(f'Wing{k}b_'+side,'Y',s*p.get('curl',0))

def ground():
    low=float(coordinates(mesh)[:,2].min())
    if low<.003:translate(.003-low)

def fly_parameters(t):
    a=2*math.pi*t
    return {'wing':-15+47*math.cos(a),'elbow':7*math.cos(a-.35),'curl':5*math.sin(a-.7),
            'fold':7*max(0,math.sin(a)),'pitch':3*math.sin(a),'neck':-3*math.sin(a),
            'head':-2*math.sin(a),'tail':1.4*math.sin(a-.7),'tail_yaw':1.1,'phase':a,
            'leg':5*math.sin(a-.3),'bob':.009*math.sin(a+1)}

def fly(t):
    pose(fly_parameters(t))

ATTACK=[(0,fly_parameters(0)),(.22,{'wing':20,'elbow':8,'pitch':-20,'neck':15,'head':-15,'jaw':12,'tail':-5,'leg':-15}),
        (.5,{'wing':-15,'fold':12,'pitch':-35,'neck':20,'head':-10,'jaw':22,'tail':-8,'leg':-30,'shin':20}),
        (.72,{'wing':-35,'fold':8,'pitch':-24,'neck':25,'head':5,'jaw':25,'tail':-10,'leg':-35,'shin':15}),
        (.833333333,{'wing':-45,'pitch':-8,'neck':35,'head':5,'jaw':6,'tail':-8,'leg':-10,'reach':-.04}),
        (1.125,fly_parameters(0))]

def attack(t):
    pose(keys(ATTACK,t))

HIT=[(0,fly_parameters(0)),(.125,{'pitch':-30,'neck':-30,'head':-15,'jaw':25,'wing':-5,'fold':20,'tail':-6,'leg':-20}),
     (.30,{'pitch':-35,'roll':22,'neck':-10,'jaw':22,'wing':-30,'fold':35,'tail':-8,'leg':-30}),
     (.55,{'pitch':-20,'roll':10,'neck':20,'jaw':10,'wing':-35,'fold':20,'tail':-6}),(.875,fly_parameters(0))]
DEATH=[(0,fly_parameters(0)),(.125,{'pitch':-30,'neck':-30,'jaw':25,'wing':-5,'fold':20,'tail':-6,'roll':10}),
       (.25,{'pitch':-55,'neck':-10,'jaw':20,'wing':-10,'fold':25,'tail':-9,'roll':45,'leg':-25}),
       (.45,{'pitch':-20,'roll':110,'neck':10,'jaw':15,'wing':-10,'fold':10,'tail':-3,'leg':-20,'shin':25}),
       (.65,{'pitch':3,'roll':105,'neck':0,'jaw':5,'tail':0,'leg':-25,'shin':30}),
       (.75,{'pitch':0,'roll':100,'neck':0,'jaw':5,'tail':0,'leg':-25,'shin':30})]

def hit(t):
    pose(keys(HIT,t))

def death(t):
    pose(keys(DEATH,t));u=smooth((t-.25)/.43)
    for side in 'LR':
        b=rig.pose.bones['UpperWing_'+side]
        desired=wing_flat[side]@b.bone.matrix_local.to_quaternion()
        current=b.matrix.to_quaternion()
        b.matrix=Matrix.Translation(b.head)@current.slerp(desired,u).to_matrix().to_4x4()
        bpy.context.view_layer.update()
    # Land the body first; wing tips must never hold the corpse aloft.
    translate((.006-float(coordinates(mesh)[body,2].min()))*u)
    tail_height=rig.pose.bones['Tail1'].head.z
    for i in range(1,10):
        b=rig.pose.bones[f'Tail{i}'];target=b.tail.copy()
        height=.012+(tail_height-.012)*(1-smooth(i/5))
        target.z=target.z*(1-u)+height*u
        Q.aim_bone(rig,b.name,target)

    for side,sign in [('L',1),('R',-1)]:
        mask=wing_masks[side]
        if float(coordinates(mesh)[mask,2].min())>=.002:continue
        for step in range(30):
            rotate('UpperWing_'+side,'Y',-sign*.5*u)
            if float(coordinates(mesh)[mask,2].min())>=.002:break
    ground()

CLIPS={'Fly':(1.,True,fly),'Attack':(1.125,False,attack),'Hit':(.875,False,hit),
       'Death':(.75,False,death),'Dead':(1.,True,lambda t:death(.75))}
report={}
for name,(duration,loop,fn) in CLIPS.items():
    count=round(duration*FPS);assert abs(count/FPS-duration)<1e-8
    action=bpy.data.actions.new(name);action.use_fake_user=True
    if not rig.animation_data:rig.animation_data_create()
    rig.animation_data.action=None
    poses=[];bounds=[]
    for frame in range(count+1):
        fn(0 if loop and frame==count else frame/FPS)
        co=coordinates(mesh);assert np.isfinite(co).all();assert co[:,2].min()>-.0001
        poses.append({b.name:(b.location.copy(),b.rotation_quaternion.copy(),b.scale.copy()) for b in rig.pose.bones})
        bounds.append([co.min(0).tolist(),co.max(0).tolist()])
        if frame in sorted(set([0,count//4,count//2,3*count//4,count])):
            for view in ['front','side','quarter']:render(f'{name}_{frame:02d}_{view}',view,1.8,(0,-.05,.38))
    rig.animation_data.action=action;previous={}
    for frame,values in enumerate(poses):
        for b in rig.pose.bones:
            loc,q,scale=values[b.name]
            if b.name in previous and previous[b.name].dot(q)<0:q=-q
            previous[b.name]=q.copy();b.location=loc;b.rotation_quaternion=q;b.scale=scale
            for channel in ['location','rotation_quaternion','scale']:b.keyframe_insert(channel,frame=frame+1)
    # Linear sampled motion avoids Bezier overshoot between the evaluated safe poses.
    for slot in action.slots:
        for layer in action.layers:
            for strip in layer.strips:
                bag=strip.channelbag(slot)
                if bag:
                    for curve in bag.fcurves:
                        for key in curve.keyframe_points:key.interpolation='LINEAR'
    rig.animation_data.action=None
    report[name]={'duration':duration,'loop':loop,'frames':count,'minimum_z':min(a[0][2] for a in bounds),'maximum_z':max(a[1][2] for a in bounds)}
rig.animation_data.action=bpy.data.actions['Fly'];sc.frame_set(1)
(P/'review/animation_metrics.json').write_text(json.dumps(report,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/anim_v1.blend'))
for o in bpy.data.objects:o.select_set(o in (mesh,rig))
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(P/'export/wyvern_pilots.glb'),use_selection=True,export_format='GLB',export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=False,export_reset_pose_bones=True,export_anim_slide_to_zero=True)
print('ANIMATIONS',report,flush=True)
