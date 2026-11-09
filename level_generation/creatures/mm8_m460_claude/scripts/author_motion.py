"""Fit the native staff carry and cross-body cast over the selected source motion."""
from pathlib import Path
import bpy,json,math,sys,ast
import numpy as np
from mathutils import Vector,Matrix,Quaternion
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common,armik
bpy.ops.wm.open_mainfile(filepath=str(p/'work/robe_rig.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];scene=bpy.context.scene;scene.render.fps=30
def attach(a):
    rig.animation_data_create();rig.animation_data.action=a
    if a and a.slots:rig.animation_data.action_slot=a.slots[0]
attach(None)
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update()
g=json.loads((p/'work/grip_pose.json').read_text());axis=Vector(g['handle_axis_hand_local']);grip=Vector(g['handle_centre_hand_local'])
with bpy.data.libraries.load(str(p/'work/staff.blend'),link=False) as (src,dst):dst.objects=['Staff']
staff=dst.objects[0];bpy.context.collection.objects.link(staff)
H=rig.data.bones['B_R_Hand'].matrix_local;local=Vector((0,0,1)).rotation_difference(axis).to_matrix().to_4x4();local.translation=grip;M=H@local
for v in staff.data.vertices:v.co=M@v.co
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
for n,location,parent in [('Staff',M.translation,'B_R_Hand'),('Socket_Staff_Head',M@Vector((0,0,.57)),'Staff'),('Socket_LeftPalm',rig.data.edit_bones['B_L_Hand'].head.lerp(rig.data.edit_bones['B_L_Finger2'].head,.7),'B_L_Hand')]:
    b=rig.data.edit_bones.new(n);b.head=location;b.tail=location+M.to_3x3().col[1]*.035;b.align_roll(M.to_3x3().col[2]);b.parent=rig.data.edit_bones[parent]
bpy.ops.object.mode_set(mode='OBJECT')
staff.parent=rig;vg=staff.vertex_groups.new(name='Staff');vg.add(list(range(len(staff.data.vertices))),1,'REPLACE');mod=staff.modifiers.new('Armature','ARMATURE');mod.object=rig
names=[b.name for b in rig.data.bones]
def pose():return {n:rig.pose.bones[n].matrix_basis.copy() for n in names}
def apply(d):
    attach(None)
    for n,m in d.items():rig.pose.bones[n].matrix_basis=m
    bpy.context.view_layer.update()
def sample(a,t):
    attach(a);scene.frame_set(int(t),subframe=t-int(t));return pose()
def blend(a,b,w):
    r={}
    for n in names:
        q=a[n].to_quaternion().slerp(b[n].to_quaternion(),w);m=q.to_matrix().to_4x4();m.translation=a[n].translation.lerp(b[n].translation,w);r[n]=m
    return r
def ease(x):x=max(0,min(1,x));return x*x*(3-2*x)
def path(t,keys):
    if t<=keys[0][0]:return Vector(keys[0][1])
    for (a,x),(b,y) in zip(keys,keys[1:]):
        if a<=t<=b:return Vector(x).lerp(Vector(y),ease((t-a)/(b-a)))
    return Vector(keys[-1][1])
source={n:[sample(bpy.data.actions[n],f) for f in range(int(bpy.data.actions[n].frame_range[1])+1)] for n in ['Standing','Walking','Attack','Cast','Hit','Death']}
for a in bpy.data.actions:a.use_fake_user=False
import arm_solver as sol
right=sol.Side('B_R_');left=sol.Side('B_L_')
ready=source['Standing'][0];apply(ready)
# A relaxed free arm clears the outside of the native robe.
L=rig.pose.bones['B_L_Hand'].matrix.to_3x3().copy();armik.solve(rig,'L',Vector((.30,-.075,.90)),pole=Vector((.40,-.25,1.15)),hand_rot=L)
GREADY=Vector((-.34,-.20,1.24));UP=Vector((-.055,.015,1)).normalized()
r=right.solve(GREADY,UP,Vector((-.35,0,-1)),steps=144);right.apply(r)
for n,q in g['finger_local'].items():rig.pose.bones[n].rotation_quaternion=q
for sd in 'LR':rig.pose.bones[f'B_{sd}_Toe0'].matrix_basis.identity()
bpy.context.view_layer.update();ready=pose()
report={'native_action_seconds':1.,'native_hit_seconds':.625,'runtime_roles':{},'running':'Native speeds 160/180/200 are below the anticipated 2.4*scale threshold; verify after final upright scale.'}
out={}
for role in ['Standing','Walking','Attack','Cast','Hit','Death','Fidget']:
    count={'Standing':60,'Walking':len(source['Walking'])-1,'Attack':57,'Cast':57,'Hit':18,'Death':len(source['Death'])-1,'Fidget':72}[role]
    frames=[];arm_records=[];prev=None
    for f in range(count+1):
        t=f/30;phase=2*math.pi*f/count
        if role in ['Standing','Walking']:
            raw=source[role][min(f,len(source[role])-1)];d=blend(ready,raw,1 if role=='Walking' else .4)
            for side in ['R']:
                for part in ['UpperArm','Forearm','Hand']:d[f'B_{side}_{part}']=ready[f'B_{side}_{part}'].copy()
            if role=='Standing':
                for part in ['UpperArm','Forearm','Hand']:d[f'B_L_{part}']=ready[f'B_L_{part}'].copy()
            apply(d);delta=rig.pose.bones['B_Pelvis'].head.z-rig.data.bones['B_Pelvis'].head_local.z
            G=GREADY+Vector((.004*math.sin(phase),.012*math.sin(phase),.004*math.cos(phase)+(delta if role=='Walking' else 0)))
            direction=UP
        elif role in ['Attack','Cast']:
            sf=float(np.clip((t-.5)*30,0,30));i=min(29,int(sf));raw=blend(source[role][i],source[role][i+1],sf-i)
            strength=ease(t/.45)*ease((1.9-t)/.40);d={n:m.copy() for n,m in ready.items()}
            for n in ['B_Spine','B_Spine1','B_Spine2','B_Neck','B_Head','B_L_Clavicle','B_R_Clavicle']:
                d[n]=blend(ready,raw,.55*strength)[n]
            for part in ['UpperArm','Forearm','Hand']:
                n=f'B_L_{part}';d[n]=blend(ready,raw,strength)[n]
            apply(d)
            G=path(t,[(0,GREADY),(.30,(-.35,-.18,1.25)),(.65,(-.25,-.28,1.35)),(.95,(-.02,-.40,1.25)),(1.08,(.01,-.42,1.22)),(1.35,(-.05,-.36,1.23)),(1.9,GREADY)])
            direction=path(t,[(0,UP),(.30,(-.12,0,1)),(.65,(.22,-.02,.98)),(.95,(.72,-.12,.68)),(1.08,(.75,-.10,.65)),(1.35,(.60,-.03,.80)),(1.9,UP)]).normalized()
        elif role=='Hit':
            sf=min(len(source['Hit'])-1,t*30);i=min(len(source['Hit'])-2,int(sf));raw=blend(source['Hit'][i],source['Hit'][i+1],sf-i)
            d={n:m.copy() for n,m in ready.items()};strength=ease(t/.1)*ease((.6-t)/.2)
            for n in ['B_Spine','B_Spine1','B_Spine2','B_Neck','B_Head','B_L_Clavicle','B_R_Clavicle']:
                d[n]=blend(ready,raw,.65*strength)[n]
            apply(d);G=GREADY+Vector((-.035*strength,.04*strength,.025*strength));direction=UP
        elif role=='Death':
            d=blend(ready,source['Death'][f],ease(t/.3));apply(d)
            G=rig.pose.bones['B_R_Hand'].matrix@grip;direction=rig.pose.bones['B_R_Hand'].matrix.to_3x3()@axis
        else:
            apply(ready);turn=Quaternion(Vector((0,0,1)),math.radians(10)*math.sin(phase))
            rig.pose.bones['B_Head'].rotation_quaternion=turn@ready['B_Head'].to_quaternion()
            G=GREADY+Vector((0,-.025*math.sin(phase)**2,.015*math.sin(phase)));direction=UP
        if role!='Death':
            result=right.solve(G,direction,Vector((-.35,0,-1)),phi_prev=prev,steps=144);right.apply(result);prev=result['phi']
            if role=='Walking':
                m=rig.pose.bones['B_L_UpperArm'].matrix.copy();q=Quaternion(Vector((0,-1,0)),math.radians(9));m3=q.to_matrix()@m.to_3x3();m3=m3.to_4x4();m3.translation=m.translation;rig.pose.bones['B_L_UpperArm'].matrix=m3
        for n,q in g['finger_local'].items():
            rig.pose.bones[n].rotation_quaternion=Quaternion(q).slerp(Quaternion(),ease((t-.3)/.3)) if role=='Death' else Quaternion(q)
        for sd in 'LR':rig.pose.bones[f'B_{sd}_Toe0'].matrix_basis.identity()
        bpy.context.view_layer.update();frames.append(pose())
    if role in ['Standing','Walking','Fidget']:frames[-1]={n:m.copy() for n,m in frames[0].items()}
    if role in ['Attack','Cast','Hit']:frames[0]={n:m.copy() for n,m in ready.items()};frames[-1]={n:m.copy() for n,m in ready.items()}
    # Global elbow/hand roll path avoids independent-frame branch changes with the long staff.
    if role in ['Attack','Cast','Hit']:
        records=[]
        for f,d in enumerate(frames):
            apply(d);hand=rig.pose.bones['B_R_Hand'].matrix.copy();row={'wrist':hand.translation.copy(),'dir':hand.to_3x3()@axis,'hand_reference':hand.to_3x3()}
            for part in ['UpperArm','Forearm','Hand']:rig.pose.bones[f'B_R_{part}'].matrix_basis=ready[f'B_R_{part}']
            bpy.context.view_layer.update();row['snap']=pose();records.append(row)
        options=armik.arm_dp(rig,'R',records,axis,phis=range(-90,91,10),psis=range(0,360,5),k_twist=.55,twist_neutral=0,k_dphi=.8,k_dpsi=1.1)
        phi=np.array([r['phi'] for r in options],float);psi=np.degrees(np.unwrap(np.radians([r['psi'] for r in options])))
        for values in [phi,psi]:
            for _ in range(4):values[1:-1]=.25*values[:-2]+.5*values[1:-1]+.25*values[2:]
        for f,row in enumerate(records):
            armik.apply_arm(rig,'R',row['snap'],row['wrist'],axis,row['dir'],float(phi[f]),float(psi[f]));frames[f]=pose()
        frames[0]=ready;frames[-1]=ready
    out[role]=frames;report['runtime_roles'][role]={'duration_seconds':count/30,'impact_seconds':.95 if role in ['Attack','Cast'] else None}
    print('AUTHORED',role,count+1,flush=True)
# Drop the staff during the native forward collapse; retain its rigid attachment node after release.
death=out['Death'];start=10;apply(death[start]);startM=rig.pose.bones['Staff'].matrix.copy();target=Matrix.Identity(4)
q=Vector((0,0,1)).rotation_difference(Vector((.96,.28,.015)).normalized());target=q.to_matrix().to_4x4();target.translation=Vector((.10,-.44,.048))
for f in range(start,len(death)):
    apply(death[f]);t=ease((f-start)/17);q=startM.to_quaternion().slerp(target.to_quaternion(),t);m=q.to_matrix().to_4x4();m.translation=startM.translation.lerp(target.translation,t);m.translation.z+=.10*math.sin(math.pi*t)
    rig.pose.bones['Staff'].matrix=m;bpy.context.view_layer.update();death[f]=pose()
out['Dead']=[death[-1]]*31;report['runtime_roles']['Dead']={'duration_seconds':1.}
for role,frames in out.items():
    old=bpy.data.actions.get(role)
    if old:bpy.data.actions.remove(old)
    a=bpy.data.actions.new(role);a.use_fake_user=True;attach(a);previous={}
    for f,d in enumerate(frames):
        for n,m in d.items():
            pb=rig.pose.bones[n];q=m.to_quaternion()
            if n in previous and q.dot(previous[n])<0:q=-q
            previous[n]=q;pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f)
            if n in ['B_Pelvis','Staff'] or n.startswith('Robe_'):pb.location=m.translation;pb.keyframe_insert('location',frame=f)
    a.use_frame_range=True;a.frame_start=0;a.frame_end=len(frames)-1
    for layer in a.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for fc in bag.fcurves:
                    for k in fc.keyframe_points:k.interpolation='LINEAR'
    attach(None)
FA=.6;UA=.5;tree=ast.parse((p/'scripts/twist_bones.py').read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'twist_about','bake_twist'}],type_ignores=[]),'twist_bake','exec'),globals())
for role in out:bake_twist(bpy.data.actions[role])
attach(None)
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/motion_authored.blend'))
(p/'review/authored_motion.json').write_text(json.dumps(report,indent=2)+'\n')
common.workbench_clay(scene);(p/'review/pilots').mkdir(exist_ok=True)
for role in ['Standing','Walking','Attack','Hit','Death']:
    a=bpy.data.actions[role];attach(a);last=int(a.frame_range[1])
    for f in sorted(set([0,round(last*.25),round(last*.5),round(last*.75),last])):
        scene.frame_set(f);common.render_views(str(p/f'review/pilots/{role}_{f:03d}'),.9,2.8,views=('front','left','three_quarter'),resolution=(400,520))
