"""Native-derived tail waves, open-hand bite, recoil and backward collapse at 24 fps."""
import bpy
import json
import math
import sys
import numpy as np
from pathlib import Path
from mathutils import Matrix, Vector

P = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P / 'work/rig_v1.blend'))
rig, body = bpy.data.objects['Rig'], bpy.data.objects['Body']
scene = bpy.context.scene
scene.render.fps = 24
data = json.loads((P / 'work/rig.json').read_text())
bones = data['bones']
rest = {n: rig.data.bones[n].matrix_local.copy() for n in bones}
relative = {n: rest[b['parent']].inverted() @ rest[n] if b['parent'] else rest[n] for n,b in bones.items()}
tail0 = np.array(data['tail'])
trunk0 = np.array(data['trunk'])
tailLength = np.linalg.norm(np.diff(tail0, axis=0), axis=1)
trunkLength = np.linalg.norm(np.diff(trunk0, axis=0), axis=1)
source = np.load(P / 'work/weights.npz')
co, edges = source['co'], source['edges']
edgeLength = np.linalg.norm(co[edges[:,1]] - co[edges[:,0]], axis=1)

durations = {'Standing':3., 'Walk':1.125, 'Running':.75, 'Fidget':.75,
             'Attack':1., 'Cast':1., 'Hit':.75, 'Death':.625, 'Dead':1.}
if '--pilot' in sys.argv:
    durations={k:v for k,v in durations.items() if k in ['Standing','Walk','Attack','Cast']}

def smooth(x):
    x = np.clip(x, 0, 1)
    return float(x*x*(3-2*x))

def pulse(t, start, peak, end):
    return smooth((t-start)/(peak-start)) * (1-smooth((t-peak)/(end-peak)))

def unit(v):
    return v / max(np.linalg.norm(v), 1e-9)

def matrix(rot, point):
    m = rot.to_4x4()
    m.translation = Vector(point)
    return m

def frame(axis, tail=False):
    y = unit(np.array(axis))
    x = unit(np.cross(y, [0,0,1])) if tail else unit(np.array([1.,0,0])-y*y[0])
    return Matrix(np.column_stack([x,y,np.cross(x,y)]))

def pose(role, t):
    if role == 'Dead':
        role, t = 'Death', durations['Death']
    gait = role in ['Walk','Running']
    phase = 2*math.pi*t/durations[role]
    windup = pulse(t,0,.28,.50) if role=='Attack' else pulse(t,0,.28,.50) if role=='Cast' else 0
    strike = pulse(t,.28,.50,1.) if role in ['Attack','Cast'] else 0
    hit = pulse(t,0,.20,.75) if role=='Hit' else pulse(t,0,.13,.30) if role=='Death' else 0
    fall = smooth((t-.10)/.525) if role=='Death' else 0
    fidget = math.sin(phase)*math.sin(math.pi*t/durations[role])**2 if role=='Fidget' else 0
    matrices = {'Root':rest['Root'].copy()}
    tail = tail0.copy()
    distance = np.r_[0,np.cumsum(tailLength)]
    for i, length in enumerate(tailLength):
        u = (i+.5)/len(tailLength)
        if gait:
            angle = 1.0*u+(.48 if role=='Running' else .34)*math.sin(phase-u*2*math.pi)*smooth(u/.2)
        else:
            angle = 1.0*u + .025*math.sin(phase-u*3)*(1-fall)
        angle += .3*fall*u
        v=(i+1)/len(tailLength)
        z = .14+.09*math.exp(-6*v)+.50*smooth((v-.82)/.18)
        if gait:
            z += .006*math.sin(phase-u*5)*smooth(u/.2)
        dz = np.clip(z-tail[i,2],-length*.95,length*.95)
        horizontal = math.sqrt(max(1e-8,length*length-dz*dz))
        tail[i+1] = tail[i]+[math.sin(angle)*horizontal,math.cos(angle)*horizontal,dz]
        name = data['tail_names'][i]
        rot = frame(tail[i+1]-tail[i],True) @ frame(tail0[i+1]-tail0[i],True).transposed()
        matrices[name] = matrix(rot @ rest[name].to_3x3(),tail[i])
    trunk = trunk0.copy()
    pitch = (.012*math.sin(phase) if role=='Standing' else 0)-.12*windup+(.12 if role=='Cast' else -.20)*strike-.35*hit
    for i,length in enumerate(trunkLength):
        u = (i+1)/len(trunkLength)
        direction = unit(trunk0[i+1]-trunk0[i])
        yaw = (.045*math.sin(phase-u*2) if gait else .025*fidget)*u
        direction = np.array(Matrix.Rotation(yaw,3,'Y') @ Matrix.Rotation(pitch*u,3,'X') @ Vector(direction))
        if fall:
            arcU=(i+.5)/len(trunkLength)
            arcDirection=np.array([.12*math.sin(u*math.pi),math.sin(math.pi*.82*arcU),math.cos(math.pi*.82*arcU)])
            direction=unit(direction*(1-fall)+arcDirection*fall)
        trunk[i+1] = trunk[i]+length*direction
        name = data['spine_names'][i]
        old = Vector(trunk0[i+1]-trunk0[i])
        rot = old.rotation_difference(Vector(direction)).to_matrix()
        orientation = rot @ rest[name].to_3x3()
        matrices[name] = matrix(orientation,trunk[i])
    for name,b in bones.items():
        if name in matrices:
            continue
        m = matrices[b['parent']] @ relative[name]
        if name=='Neck':
            m = m @ Matrix.Rotation(-.10*windup+.10*strike-.16*hit+.30*fall,4,'X')
        elif name=='Head':
            m = m @ Matrix.Rotation(.11*windup-.17*strike+.12*hit+.12*fall,4,'X')
            m = m @ Matrix.Rotation(.16*fidget,4,'Z')
        elif name=='Jaw':
            # Local X follows the skull's left/right hinge axis.
            m = m @ Matrix.Rotation(.08*windup+.20*strike+.10*hit,4,'X')
        if name.startswith('Dorsal_'):
            m=m @ Matrix.Rotation(.045*math.sin(phase-int(name.split('_')[-1])*.5)*(1-fall)+1.25*fall,4,'Z')
        elif name=='Caudal':
            m=m @ Matrix.Rotation(.07*math.sin(phase-1.5)*(1-fall),4,'Y')
        matrices[name] = m
    chest = data['spine_names'][-1]
    carried = matrices[chest] @ rest[chest].inverted()
    rotation = carried.to_3x3()
    for side,sign in [('L',1),('R',-1)]:
        names = data['arms'][side]['names']
        p = np.array(data['arms'][side]['points'])
        shoulder = np.array(matrices[names[0]].translation)
        swing = .04*math.sin(phase+(0 if sign>0 else math.pi)) if gait else 0
        if role=='Cast':
            offset=Vector((sign*(-.18+.03*windup-.08*strike),.08-.12*windup-.31*strike+swing,
                           .10+.15*windup+.20*strike))
        else:
            offset=Vector((sign*(-.18+.23*windup+.12*strike),.10+.02*windup+swing,
                           .10+.30*windup+.20*strike+.24*hit+.025*fidget))
        target = np.array(carried @ Vector(p[2]) + rotation @ offset)
        if fall:
            planted = shoulder+np.array([sign*.30,-.10,.12])
            target = target*(1-fall)+planted*fall
            target[2] = max(target[2],.30)
        upper = np.linalg.norm(p[1]-p[0])
        lower = np.linalg.norm(p[2]-p[1])
        axis = unit(target-shoulder)
        length = np.clip(np.linalg.norm(target-shoulder),abs(upper-lower)+.003,upper+lower-.003)
        target = shoulder+axis*length
        pole = np.array(carried@Vector(p[1]) + rotation@Vector((sign*.08,.08,.05)))-shoulder
        if fall:
            pole = pole*(1-fall)+np.array([0.,0.,1.])*fall
        pole = unit(pole-axis*np.dot(pole,axis))
        along = (upper*upper-lower*lower+length*length)/(2*length)
        elbow = shoulder+axis*along+pole*math.sqrt(max(0,upper*upper-along*along))
        for i,(start,end) in enumerate([(shoulder,elbow),(elbow,target)]):
            old = rotation @ Vector(p[i+1]-p[i])
            delta = old.rotation_difference(Vector(end-start)).to_matrix()
            matrices[names[i]] = matrix(delta@rotation@rest[names[i]].to_3x3(),start)
        delta = matrices[names[1]].to_3x3() @ rest[names[1]].to_3x3().transposed()
        matrices[names[2]] = matrix(delta@rest[names[2]].to_3x3(),target)
        for digit in data['fingers'][side]:
            for i,name in enumerate(digit['names']):
                m = matrices[bones[name]['parent']] @ relative[name]
                # Keep each claw rigid; bend only the fleshy finger joints.
                if i<2:
                    m = m @ Matrix.Rotation(.05*strike+.035*hit+.025*fidget,4,'X')
                matrices[name] = m
    for name,b in bones.items():
        parent = b['parent']
        rig.pose.bones[name].matrix_basis = relative[name].inverted() @ (
            matrices[parent].inverted()@matrices[name] if parent else matrices[name])
    bpy.context.view_layer.update()
    evaluated = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    minimum = min(v.co.z for v in mesh.vertices)
    evaluated.to_mesh_clear()
    lift = max(0,-minimum)
    if lift:
        rig.pose.bones['Root'].location += rest['Root'].to_3x3().transposed() @ Vector((0,0,lift))
        bpy.context.view_layer.update()
    return lift

rig.animation_data_clear()
for action in list(bpy.data.actions):
    bpy.data.actions.remove(action)
reports = {}
for role,duration in durations.items():
    count = round(duration*24)
    keys = {name:[] for name in bones}
    positions = []
    minimum = []
    lifts = []
    stretches = []
    for sample in range(count+1):
        rig.animation_data_clear()
        lifts.append(pose(role,sample/24))
        evaluated = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh = evaluated.to_mesh()
        c = np.array([v.co[:] for v in mesh.vertices])
        evaluated.to_mesh_clear()
        positions.append(c)
        minimum.append(float(c[:,2].min()))
        stretch = np.linalg.norm(c[edges[:,1]]-c[edges[:,0]],axis=1)/np.maximum(edgeLength,1e-6)
        stretches.append([float(np.percentile(stretch,99)),float(stretch.max())])
        for name in bones:
            pb = rig.pose.bones[name]
            keys[name].append((pb.location.copy(),pb.rotation_quaternion.copy()))
    action = bpy.data.actions.new(role)
    action.use_fake_user = True
    rig.animation_data_create()
    rig.animation_data.action = action
    for sample in range(count+1):
        for name in bones:
            pb = rig.pose.bones[name]
            pb.location,pb.rotation_quaternion = keys[name][sample]
            pb.keyframe_insert('location',frame=sample+1,group=name)
            pb.keyframe_insert('rotation_quaternion',frame=sample+1,group=name)
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    for key in curve.keyframe_points:
                        key.interpolation = 'LINEAR'
    reports[role] = dict(duration=count/24,min_z=min(minimum),max_ground_correction=max(lifts),
                         loop_delta=float(np.linalg.norm(positions[-1]-positions[0],axis=1).max()),
                         edge_stretch=np.max(stretches,axis=0).tolist())
    print(role,json.dumps(reports[role]),flush=True)
    assert min(minimum)>-.002,(role,min(minimum))
    if role in ['Standing','Walk','Running','Dead']:
        assert reports[role]['loop_delta']<.002,(role,reports[role])
rig.animation_data.action = bpy.data.actions['Standing']
scene.frame_set(1)
(P/'work/animation_audit.json').write_text(json.dumps(reports,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/anim_v1.blend'))
