"""Wyrm motions adapted from the native sequence; shared analytic limb IK, no paid biped clips."""
import bpy, math, json, sys
import numpy as np
from pathlib import Path
from mathutils import Vector, Matrix, Quaternion
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parent/'mm6_rat_claude/scripts'))
import posing
bpy.ops.wm.open_mainfile(filepath=str(P/'work/revision02_rest.blend'))
rig=bpy.data.objects['Wyrm_Rig'];mesh=bpy.data.objects['Wyrm'];sc=bpy.context.scene
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.object.mode_set(mode='EDIT')
b=rig.data.edit_bones.get('Remains') or rig.data.edit_bones.new('Remains');b.head=(0,0,0);b.tail=(0,.01,0)
bpy.ops.object.mode_set(mode='OBJECT')
for b in rig.pose.bones:b.rotation_mode='QUATERNION'
socket=bpy.data.objects.get('Socket_Remains')
if socket is None:
    socket=bpy.data.objects.new('Socket_Remains',None);sc.collection.objects.link(socket)
socket.parent=rig;socket.parent_type='BONE';socket.parent_bone='Remains'
bpy.context.view_layer.update();socket.matrix_world=Matrix.Identity(4)
FPS=24;sc.render.fps=FPS
posing.reset(rig)
REST={b.name:b.matrix.copy() for b in rig.pose.bones}
X,Y,Z=Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1))

# Correct the separately modelled mouth floor's ownership without touching submitted texture geometry/UVs.
parts=mesh.data.attributes['part']
ids=[i for i,v in enumerate(parts.data) if v.value==2]
for g in mesh.vertex_groups:g.remove(ids)
mesh.vertex_groups['Jaw'].add(ids,1.0,'REPLACE')

def rot(name,axis,deg):
    if abs(deg)>1e-7:posing.rotate_world(rig,name,axis,deg)

def smooth(t):
    t=max(0,min(1,t));return t*t*(3-2*t)

def keys(t,rows):
    for (t0,a),(t1,b) in zip(rows,rows[1:]):
        if t<=t1:
            u=smooth((t-t0)/(t1-t0));return {k:a.get(k,0)+(b.get(k,0)-a.get(k,0))*u for k in a.keys()|b.keys()}
    return rows[-1][1]

def leg(kind,side,offset=Vector(),pitch=0):
    upper,lower,paw=(f'UpperArm_{side}',f'ForeArm_{side}',f'FrontPaw_{side}') if kind=='front' else (f'Thigh_{side}',f'Shin_{side}',f'HindPaw_{side}')
    target=REST[paw].translation+offset;sign=1 if side=='L' else -1
    pole=target+Vector((.010*sign,.18 if kind=='front' else -.18,.08))
    posing.two_bone_ik(rig,upper,lower,target,pole)
    bone=rig.pose.bones[paw]
    bone.matrix=Matrix.LocRotScale(bone.head.copy(),Quaternion(X,math.radians(pitch))@REST[paw].to_quaternion(),Vector((1,1,1)))
    bpy.context.view_layer.update()

def planted():
    for kind in ['front','hind']:
        for side in 'LR':leg(kind,side)

def tail(phase,amp=2,lift=0):
    for i in range(1,11):
        rot(f'Tail{i}',Z,amp*(.4+i/10)*math.sin(2*math.pi*(phase-.045*i)))
        rot(f'Tail{i}',X,lift if i==1 else 0)

def core(p):
    root=rig.pose.bones['Spine1'];root.matrix=Matrix.Translation(Vector((0,p.get('travel',0),p.get('height',0))))@root.matrix;bpy.context.view_layer.update()
    rot('Spine1',X,p.get('pitch',0));rot('Spine1',Y,p.get('roll',0));rot('Spine2',X,p.get('chest',0))
    for n in ['Neck1','Neck2','Neck3']:
        rot(n,X,p.get('neck',0)/3);rot(n,Z,p.get('yaw',0)/3)
    rot('Head',X,p.get('head',0));rot('Jaw',X,p.get('jaw',0))

def standing(t):
    posing.reset(rig);phase=t/3
    core({'neck':1.3*math.sin(phase*2*math.pi),'yaw':2*math.sin(phase*2*math.pi)})
    tail(phase,1.2);planted()

def gait(t,period,stride,duty,running=False):
    posing.reset(rig);phase=t/period
    core({'height':-.005-.002*math.cos(phase*4*math.pi),'neck':-3 if running else 0})
    tail(phase,2.5)
    phases=[('front','L',0),('front','R',.5),('hind','L',.5 if running else .75),('hind','R',0 if running else .25)]
    for kind,side,shift in phases:
        q=(phase+shift)%1
        if q<duty:dy=stride*(q-duty/2);dz=0;pitch=0
        else:
            u=(q-duty)/(1-duty);dy=stride*duty*(.5-smooth(u));dz=(.022 if kind=='front' else .017)*math.sin(math.pi*u);pitch=10*math.sin(math.pi*u)
        leg(kind,side,Vector((0,dy,dz)),pitch)

ATTACK=[(0,{}),(.17,{'pitch':-2,'height':-.004,'travel':.008,'neck':-8,'head':-5,'yaw':6,'jaw':7}),
        (.375,{'pitch':-6,'chest':-2,'height':-.020,'travel':.024,'neck':-24,'head':-15,'yaw':17,'jaw':21}),
        (.46,{'pitch':-5,'chest':-1,'height':-.018,'travel':.020,'neck':-20,'head':-12,'yaw':13,'jaw':28}),
        (.625,{'pitch':5,'chest':2,'height':-.008,'travel':-.021,'neck':14,'head':5,'yaw':-11,'jaw':32}),
        (.75,{'pitch':3,'height':-.006,'travel':-.012,'neck':8,'head':2,'yaw':-7,'jaw':18}),
        (.875,{'pitch':-1,'height':-.003,'travel':.002,'neck':-3,'yaw':-3,'jaw':5}),(1.0,{})]
HIT=[(0,{}),(.125,{'neck':28,'yaw':-22,'head':5}),(.25,{'neck':10,'yaw':-30,'head':-9,'jaw':12}),
     (.375,{'neck':-12,'yaw':-28,'head':-6,'jaw':16}),(.5,{'neck':-2,'yaw':-10,'jaw':6}),(.625,{})]
DEATH=[(0,{}),(.125,{'pitch':-5,'height':-.014,'neck':-18,'head':-8,'yaw':-12,'jaw':25}),
       (.29,{'pitch':-12,'height':-.043,'neck':-23,'head':-9,'yaw':10,'roll':10,'jaw':28}),
       (.48,{'pitch':-5,'neck':12,'yaw':20,'roll':48,'height':-.100,'jaw':20}),
       (.68,{'pitch':0,'neck':0,'yaw':4,'roll':82,'height':-.139,'jaw':24}),
       (.875,{'pitch':0,'neck':-8,'yaw':0,'roll':90,'height':-.14,'jaw':24})]

def action(t,rows,death=False):
    posing.reset(rig);p=keys(t,rows);core(p);tail(t,3 if death else 2)
    if death:
        # Keep the planted support through the initial recoil; fold limbs only as the torso falls.
        u=smooth((t-.20)/.34)
        for kind in ['front','hind']:
            for side in 'LR':
                paw=('FrontPaw_' if kind=='front' else 'HindPaw_')+side
                offset=Vector((0,.015*u if kind=='front' else -.012*u,.055*u))
                leg(kind,side,offset,25*u)
    else:planted()

def fidget(t):
    posing.reset(rig);u=t/1.5
    core({'yaw':12*math.sin(u*2*math.pi),'neck':-5*math.sin(u*math.pi),'jaw':3*math.sin(u*math.pi)**2})
    tail(u,3);planted()

deps=bpy.context.evaluated_depsgraph_get()
def coords():
    bpy.context.view_layer.update();ev=mesh.evaluated_get(deps);me=ev.to_mesh();a=np.empty(len(me.vertices)*3);me.vertices.foreach_get('co',a);ev.to_mesh_clear();return a.reshape(-1,3)

names={g.index:g.name for g in mesh.vertex_groups}
tail_ids={v.index for v in mesh.data.vertices if sum(g.weight for g in v.groups if names[g.group].startswith('Tail'))>.5}
body_ids=[v.index for v in mesh.data.vertices if v.index not in tail_ids]
tail_sections={n:[v.index for v in mesh.data.vertices if any(names[g.group]==n and g.weight>.45 for g in v.groups)] for n in [f'Tail{i}' for i in range(1,11)]}
tail_clearance={n:max(.008,-min((REST[n].inverted()@mesh.data.vertices[i].co).z for i in ids))+.003 for n,ids in tail_sections.items() if ids}
def floor(name):
    # Body contact may shift the root; a low tail must never hoist the body off its supporting feet.
    if name in ['Death','Dead']:
        low=coords()[body_ids,2].min()
        root=rig.pose.bones['Spine1'];root.matrix=Matrix.Translation(Vector((0,0,max(0,.001-low))))@root.matrix
        bpy.context.view_layer.update()
    for i in range(1,11):
        b=rig.pose.bones[f'Tail{i}'];h=b.head.copy();d=b.tail-h
        clearance=tail_clearance[b.name]
        if name in ['Death','Dead']:
            # Solve a relaxed world-space tail from the moving hip, keeping its length and dorsal side upright.
            rest=rig.data.bones[b.name];r=rest.tail_local-rest.head_local
            root_ratio=max(0,min(1,rig.pose.bones['Tail1'].head.z/rig.data.bones['Tail1'].head_local.z))
            target_z=max(clearance,rest.tail_local.z*root_ratio)
            dz=max(-r.length*.98,min(target_z-h.z,r.length*.98))
            flat=Vector((d.x,d.y,0)).normalized()
            direction=(flat*math.sqrt(max(r.length*r.length-dz*dz,1e-8))+Vector((0,0,dz))).normalized()
            q=r.normalized().rotation_difference(direction) @ REST[b.name].to_quaternion()
            b.matrix=Matrix.LocRotScale(h,q,Vector((1,1,1)))
            bpy.context.view_layer.update()
        elif b.tail.z<clearance:
            flat=Vector((d.x,d.y,0)).normalized();dz=min(clearance-h.z,d.length*.99)
            posing.aim_bone(rig,b.name,h+flat*math.sqrt(max(d.length*d.length-dz*dz,1e-8))+Vector((0,0,dz)))

CLIPS={'Standing':(3,True,standing),'Walking':(.75,True,lambda t:gait(t,.75,.12,.70)),
       'Running':(.625,True,lambda t:gait(t,.625,.19,.58,True)),
       'Attack':(1,False,lambda t:action(t,ATTACK)),'Hit':(.625,False,lambda t:action(t,HIT)),
       'Fidget':(1.5,False,fidget),'Death':(.875,False,lambda t:action(t,DEATH,True)),
       'Dead':(1/24,False,lambda t:action(.875,DEATH,True))}
report={}
for name,(duration,loop,fn) in CLIPS.items():
    if rig.animation_data is None:rig.animation_data_create()
    rig.animation_data.action=None
    old=bpy.data.actions.get(name)
    if old:bpy.data.actions.remove(old)
    act=bpy.data.actions.new(name);act.use_fake_user=True;n=round(duration*FPS);poses=[];low=1e9
    for f in range(n+1):
        fn((f%n if loop else f)/FPS);floor(name);rig.pose.bones['Remains'].scale=(1,1,1) if name=='Dead' else (smooth((f/FPS-.68)/.195),)*3 if name=='Death' else (0,0,0);low=min(low,float(coords()[:,2].min()))
        poses.append({b.name:(b.location.copy(),b.rotation_quaternion.copy(),b.scale.copy()) for b in rig.pose.bones})
    rig.animation_data.action=act;previous={}
    for f,pose in enumerate(poses):
        for b in rig.pose.bones:
            loc,q,scale=pose[b.name]
            if b.name in previous and previous[b.name].dot(q)<0:q=-q
            previous[b.name]=q;b.location=loc;b.rotation_quaternion=q;b.scale=scale
            for prop in ['location','rotation_quaternion','scale']:b.keyframe_insert(prop,frame=f+1)
    rig.animation_data.action=None;report[name]={'duration':duration,'loop':loop,'min_z':low,'samples':len(poses)}
    print('CLIP',name,report[name],flush=True)
    assert low>-.003,(name,low)
rig.animation_data.action=bpy.data.actions['Standing'];sc.frame_set(1)
for a in bpy.data.actions:
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/anim_v3.blend'))
(P/'work/anim_info.json').write_text(json.dumps({'fps':FPS,'walk_stride_m':.12,'run_stride_m':.19,'clips':report},indent=2)+'\n')

# Clay extrema supplement subsequent normal/slow GLB playback.
sc.render.engine='BLENDER_WORKBENCH';sc.render.resolution_x=1000;sc.render.resolution_y=680
sc.display.shading.light='STUDIO';sc.display.shading.color_type='SINGLE';sc.display.shading.single_color=(.66,.7,.65)
sc.display.shading.show_cavity=True;sc.display.shading.background_type='VIEWPORT';sc.display.shading.background_color=(.15,.15,.15)
cam=bpy.data.objects.new('ReviewCamera',bpy.data.cameras.new('ReviewCamera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=1.18
target=Vector((0,0,.20));cam.location=(1,-1,.65);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
for name in ['Attack','Death']:
    rig.animation_data.action=bpy.data.actions[name]
    for j,fraction in enumerate([0,.25,.5,.75,1]):
        sc.frame_set(round(CLIPS[name][0]*FPS*fraction)+1);sc.render.filepath=str(P/'review/revision02'/f'clay_{name}_{j}.png');bpy.ops.render.render(write_still=True)
