"""Create an original scimitar and author MM6 goblin poses against the native six-frame attack."""
import bpy
import json
import math
from pathlib import Path
from mathutils import Vector, Matrix, Quaternion

ROOT = Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_sword_attack')
scene = bpy.data.scenes['Meshy Goblin Sword and Native Attack']
bpy.context.window.scene = scene
rig = bpy.data.objects['MM6 Meshy Goblin Rig']
body = bpy.data.objects['Meshy Goblin Body']
rig.animation_data.action = None
for tr in rig.animation_data.nla_tracks:
    tr.mute = True
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
HAND = 'mixamorig:RightHand'
hand_rest = rig.data.bones[HAND].matrix_local.copy()
width = Vector((0.50113, 0, -0.86537)).normalized()
length = Vector((0, 1, 0))
back = width.cross(length)
grip_local = width * -0.012 + length * 0.104 + back * -0.045
# Sword axes: Y goes from pommel through blade, Z is the curve's rise, X is thickness.
sword_in_hand = Matrix((back, -width, -length)).transposed()
sword_rest = hand_rest @ (Matrix.Translation(grip_local) @ sword_in_hand.to_4x4())
scene['sword_grip_local'] = list(grip_local)
scene['sword_in_hand'] = json.dumps(list(map(list, sword_in_hand)))

# Retain the source shape and UVs; a local shape key closes the sword fingers.
if not body.data.shape_keys:
    body.shape_key_add(name='Basis')
keys = body.data.shape_keys.key_blocks
key = keys.get('SwordGrip') or body.shape_key_add(name='SwordGrip')
hand_groups = {g.index for g in body.vertex_groups if g.name in (HAND, 'mixamorig:RightHandMiddle4')}
inv = hand_rest.inverted() @ body.matrix_world
back_to_mesh = body.matrix_world.inverted() @ hand_rest
changed = 0
for v, original, dest in zip(body.data.vertices, keys['Basis'].data, key.data):
    dest.co = original.co
    weight = sum(g.weight for g in v.groups if g.group in hand_groups)
    p = inv @ original.co
    if weight < 0.4 or p.y <= 0.093:
        continue
    w, y, n = p.dot(width), p.y, p.dot(back)
    radius = 0.035
    theta = min(3.15, max(0, (y - 0.093) / radius))
    # Constant-curvature bend preserves cross-section thickness and avoids collapsing the fingers.
    q = width*w + length*(0.093 + (radius+n+0.010)*math.sin(theta))
    q += back*(-0.010-radius + (radius+n+0.010)*math.cos(theta))
    blend = min(1, max(0, (weight-.4)/.35))
    dest.co = original.co.lerp(back_to_mesh @ q, blend)
    changed += 1
key.value = 1.0

for obj in list(scene.objects):
    if obj.get('mm6_sword_part'):
        bpy.data.objects.remove(obj, do_unlink=True)

def material(name, color, metallic, roughness):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1); mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*color, 1)
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Roughness'].default_value = roughness
    return mat

steel = material('MM6 sword warm steel', (.34,.30,.26), .8, .33)
edge = material('MM6 sword sharpened edge', (.64,.61,.53), .88, .25)
gold = material('MM6 sword aged gold', (.55,.30,.065), .85, .29)
leather = material('MM6 sword dark wrapped grip', (.050,.021,.009), 0, .70)
parts=[]
def mesh_part(name, verts, faces, mat):
    mesh=bpy.data.meshes.new(name); mesh.from_pydata(verts,[],faces); mesh.update()
    obj=bpy.data.objects.new(name,mesh);scene.collection.objects.link(obj);mesh.materials.append(mat)
    obj['mm6_sword_part']=True
    for v in mesh.vertices:v.co=sword_rest@v.co
    group=obj.vertex_groups.new(name=HAND);group.add(list(range(len(mesh.vertices))),1,'REPLACE')
    obj.parent=rig;mod=obj.modifiers.new('Rigid right-hand attachment','ARMATURE');mod.object=rig
    parts.append(obj);return obj

def tube(name, pts, radius, mat, sides=12):
    pts=[Vector(p) for p in pts]
    if len(pts)>3 and 'winding' not in name:
        smooth=[]
        for i in range(len(pts)-1):
            p0,p1,p2,p3=pts[max(0,i-1)],pts[i],pts[i+1],pts[min(len(pts)-1,i+2)]
            for j in range(7):
                t=j/7
                smooth.append(.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t))
        pts=smooth+[pts[-1]]
    verts=[];faces=[]
    for i,p in enumerate(pts):
        tangent=(pts[min(i+1,len(pts)-1)]-pts[max(0,i-1)]).normalized()
        u=tangent.cross(Vector((1,0,0)))
        if u.length<.01:u=tangent.cross(Vector((0,0,1)))
        u.normalize();v=tangent.cross(u)
        for j in range(sides):
            a=j*2*math.pi/sides;verts.append(p+radius*(math.cos(a)*u+math.sin(a)*v))
    for i in range(len(pts)-1):
        for j in range(sides):a=i*sides+j;b=i*sides+(j+1)%sides;faces.append((a,b,b+sides,a+sides))
    faces.extend([tuple(reversed(range(sides))),tuple((len(pts)-1)*sides+j for j in range(sides))])
    ob=mesh_part(name,verts,faces,mat)
    for f in ob.data.polygons:f.use_smooth=True
    return ob

verts=[];faces=[]
count=33
for i in range(count):
    t=i/(count-1);y=.105+.745*t;z=.018*t*t+.115*t**5
    half=(.024+.025*math.sin(math.pi*t)**1.4)*(1-t**9)
    half=max(.0004,half);thick=.0045*(1-.85*t*t)
    verts.extend([(0,y,z-half),(thick*.8,y,z-half+half*.17),(thick,y,z+half*.80),(0,y,z+half),(-thick,y,z+half*.80),(-thick*.8,y,z-half+half*.17)])
for i in range(count-1):
    for j in range(6):a=i*6+j;b=i*6+(j+1)%6;faces.append((a,b,b+6,a+6))
faces.extend([tuple(reversed(range(6))),tuple((count-1)*6+j for j in range(6))])
faces=[tuple(reversed(f)) for f in faces]
blade=mesh_part('MM6 long curved blade',verts,faces,steel);blade.data.materials.append(edge)
for i,p in enumerate(blade.data.polygons):p.material_index=1 if i%6 in (0,5) else 0
# Swept crossguard and outside bow resemble the native gold hilt.
tube('MM6 swept gold guard',[(0,.078,-.080),(0,.094,-.072),(0,.102,-.04),(0,.099,0),(0,.092,.045),(0,.075,.073),(0,.059,.075)],.0065,gold)
tube('MM6 knuckle bow',[(0,-.087,0),(.016,-.082,-.055),(.02,-.055,-.073),(.02,.035,-.080),(.008,.083,-.067)],.0047,gold)
tube('MM6 leather sword grip',[(0,-.083,0),(0,.084,0)],.018,leather,20)
for i in range(12):
    y=-.076+i*.013
    tube('MM6 grip winding %02d'%i,[(.0185*math.cos(j*2*math.pi/24),y+j*.006/24,.0185*math.sin(j*2*math.pi/24)) for j in range(25)],.0018,leather,6)
tube('MM6 gold pommel',[(0,-.097,0),(0,-.086,0),(0,-.078,0)],.026,gold,20)
tube('MM6 grip ferrule',[(0,.075,0),(0,.092,0)],.021,gold,20)

# Per-frame pose targets from the native front attack, with depth inferred from anatomy.
# Timings are source-frame starts in seconds; the final 0.75 s key returns to standing.
KEYS=[
 (0.000, dict(twist=0,lean=2,r=(-.30,-.22,1.00),l=(.31,-.05,.91),d=(.83,-.32,.46),lift=0,roll=0)),
 (0.125, dict(twist=40,lean=-5,r=(.21,-.28,1.34),l=(.29,-.20,1.12),d=(.61,-.12,.78),lift=.060,roll=0)),
 (0.250, dict(twist=19,lean=0,r=(.20,-.30,1.35),l=(.25,-.28,1.22),d=(.49,-.21,.85),lift=.060,roll=0)),
 (0.375, dict(twist=-9,lean=6,r=(-.32,-.34,1.11),l=(.05,-.34,1.09),d=(.19,-.94,-.28),lift=.015,roll=0)),
 (0.500, dict(twist=-28,lean=17,r=(-.44,-.26,1.00),l=(.01,-.29,.94),d=(-.96,-.23,-.16),lift=0,roll=72)),
 (0.625, dict(twist=-8,lean=7,r=(-.30,-.21,.98),l=(.25,-.22,.92),d=(.12,-.97,-.20),lift=0,roll=0)),
 (0.750, dict(twist=0,lean=2,r=(-.31,-.14,.98),l=(.32,-.06,.92),d=(.31,-.95,.02),lift=0,roll=0)),
]
rest={b.name:b.matrix_local.copy() for b in rig.data.bones}
def interpolate(t):
    for (ta,a),(tb,b) in zip(KEYS,KEYS[1:]):
        if t<=tb:
            f=max(0,(t-ta)/(tb-ta));f=f*f*(3-2*f)
            return {k:(tuple(x+(y-x)*f for x,y in zip(a[k],b[k])) if isinstance(a[k],tuple) else a[k]+(b[k]-a[k])*f) for k in a}
    return KEYS[-1][1].copy()

def solve_two(a,target,l1,l2,pole):
    delta=target-a;dist=max(.001,min(delta.length,l1+l2-.0003));axis=delta.normalized();target=a+axis*dist
    along=(l1*l1-l2*l2+dist*dist)/(2*dist);height=math.sqrt(max(0,l1*l1-along*along))
    direction=Vector(pole)-a;direction-=axis*direction.dot(axis);direction.normalize()
    return a+axis*along+direction*height,target

def pose(params):
    targets={}
    def inherited(name):
        b=rig.data.bones[name]
        return targets[b.parent.name]@rest[b.parent.name].inverted()@rest[name] if b.parent else rest[name].copy()
    def rotate(name,tilt,twist):
        m=inherited(name);q=Quaternion((0,0,1),math.radians(twist))@Quaternion((1,0,0),math.radians(tilt));orientation=q@rest[name].to_quaternion()
        m=(Matrix.Translation(m.translation)@orientation.to_matrix().to_4x4());targets[name]=m
    def aim(name,a,b):
        bone=rig.data.bones[name];q=(bone.tail_local-bone.head_local).rotation_difference(b-a)@rest[name].to_quaternion();targets[name]=Matrix.Translation(a)@q.to_matrix().to_4x4()
    def target_for(name):
        if name not in targets:targets[name]=inherited(name)
        return targets[name]
    # Absolute torso rotations increase smoothly from pelvis to shoulders.
    for name,frac in [('Hips',.25),('Spine',.5),('Spine1',.8),('Spine2',1),('Neck',1),('Head',1)]:
        n='mixamorig:'+name;tilt=params['lean']*(1.8 if name=='Head' else 1)*frac
        rotate(n,tilt,params['twist']*(1.10 if name=='Head' else frac))
        if name=='Hips':targets[n].translation+=Vector((0,0,-.020-.002*max(0,params['lean'])))
    for b in rig.data.bones:
        if b.name in targets:continue
        if 'Shoulder' in b.name:targets[b.name]=inherited(b.name)
    for side,sign in [('Right',-1),('Left',1)]:
        prefix='mixamorig:'+side
        # Planted feet; left heel lifts through anticipation and returns during the slash.
        upper,lower,foot=prefix+'UpLeg',prefix+'Leg',prefix+'Foot'
        a=inherited(upper).translation;target=rest[foot].translation.copy()
        if side=='Left':target+=Vector((0,.045*params['lift']/.06,params['lift']))
        joint,target=solve_two(a,target,rig.data.bones[upper].length,rig.data.bones[lower].length,(sign*.3,-1,.5));aim(upper,a,joint);aim(lower,joint,target)
        targets[foot]=rest[foot].copy();targets[foot].translation=target
        if side=='Left':targets[foot]=targets[foot]@Quaternion((1,0,0),math.radians(-12*params['lift']/.06)).to_matrix().to_4x4()
        upper,lower,hand=prefix+'Arm',prefix+'ForeArm',prefix+'Hand'
        a=inherited(upper).translation
        if side=='Right':
            direction=Vector(params['d']).normalized();normal=Vector((0,-1,0));normal-=direction*normal.dot(direction);normal.normalize();up=normal.cross(direction)
            sword_rotation=Quaternion(direction,math.radians(params['roll'])).to_matrix()@Matrix((normal,direction,up)).transposed()
            hand_rotation=sword_rotation@sword_in_hand.inverted()
            wrist=Vector(params['r'])-hand_rotation@grip_local
        else:
            wrist=Vector(params['l']);hand_rotation=None
        pole=(sign*.60,.04,1.05)
        joint,wrist=solve_two(a,wrist,rig.data.bones[upper].length,rig.data.bones[lower].length,pole)
        aim(upper,a,joint);aim(lower,joint,wrist)
        if hand_rotation is None:
            hand_rotation=targets[lower].to_3x3()@rest[lower].to_3x3().inverted()@rest[hand].to_3x3()
        targets[hand]=Matrix.Translation(wrist)@hand_rotation.to_4x4()
    for b in rig.data.bones:
        if b.name not in targets:targets[b.name]=inherited(b.name)
        kw={}
        if b.parent:kw={'parent_matrix':targets[b.parent.name],'parent_matrix_local':rest[b.parent.name]}
        rig.pose.bones[b.name].matrix_basis=b.convert_local_to_pose(targets[b.name],rest[b.name],invert=True,**kw)
    bpy.context.view_layer.update()

# Bake FK quaternions; the rig remains ordinary GLB skinning without runtime IK dependencies.
def bake(name,params_at,seconds):
    old=bpy.data.actions.get(name)
    if old:old.name=name+' previous'
    action=bpy.data.actions.new(name);rig.animation_data.action=action;action.use_fake_user=True
    for pb in rig.pose.bones:pb.rotation_mode='QUATERNION'
    previous={}
    for i in range(round(seconds*48)+1):
        t=i/48;frame=1+t*24;rig.animation_data.action=None;pose(params_at(t))
        for pb in rig.pose.bones:
            if pb.name in previous and pb.rotation_quaternion.dot(previous[pb.name])<0:pb.rotation_quaternion.negate()
            previous[pb.name]=pb.rotation_quaternion.copy()
        rig.animation_data.action=action
        for pb in rig.pose.bones:
            pb.keyframe_insert('location',frame=frame,group=pb.name);pb.keyframe_insert('rotation_quaternion',frame=frame,group=pb.name);pb.keyframe_insert('scale',frame=frame,group=pb.name)
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for fc in bag.fcurves:
                    for keyframe in fc.keyframe_points:keyframe.interpolation='LINEAR'
    return action
standing=bake('MM6_Standing_Sword',lambda t:KEYS[-1][1],1)
attack=bake('MM6_Attack_Native',interpolate,.75)
scene['authored_actions']=json.dumps({'Standing':standing.name,'Attack':attack.name})
scene.render.fps=24;scene.frame_start=1;scene.frame_end=19
rig.animation_data.action=attack;rig.animation_data.action_slot=attack.slots[0];scene.frame_set(4)
(ROOT/'construction.json').write_text(json.dumps({'source':'output/meshy_goblin_v2_review/goblin_2_head_corrected.glb','grip_vertices':changed,'sword_parts':len(parts),'blade_length':.745,'attack_seconds':.75,'keys':KEYS,'native_source':'../source_audit/attack_native.png'},indent=2))
print(json.dumps({'sword_parts':len(parts),'grip_vertices':changed,'actions':[standing.name,attack.name]}))
