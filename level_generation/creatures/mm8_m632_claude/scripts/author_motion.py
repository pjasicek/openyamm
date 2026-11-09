"""Native carry/aim over reviewed local body motions, with a continuous whole-clip arm solve."""
import os,sys,json,math,runpy
from pathlib import Path
import bpy,numpy as np
from mathutils import Matrix,Vector,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
os.environ['M632_BUILD']='1'
import pose_fit as fit
import armik,common
rig,body,prop,sc=fit.rig,fit.body,fit.prop,fit.scene
G=fit.G;NAMES=[b.name for b in rig.pose.bones];sc.render.fps=60;sc.render.fps_base=1
REST={b.name:b.matrix_basis.copy() for b in rig.pose.bones}
for n in REST:REST[n]=Matrix()
def activate(a):
    rig.animation_data.action=a
    if a is not None and len(a.slots):rig.animation_data.action_slot=a.slots[0]
def sample(a,f):
    activate(a);sc.frame_set(int(f),subframe=f-int(f))
    return {b.name:b.matrix_basis.copy() for b in rig.pose.bones}
def put(p):
    activate(None)
    for n in NAMES:rig.pose.bones[n].matrix_basis=p.get(n,Matrix())
    bpy.context.view_layer.update()
def snap():return {b.name:b.matrix_basis.copy() for b in rig.pose.bones}
def smooth(x):
    x=min(1,max(0,x));return x*x*(3-2*x)
def mix(a,b,w):
    return {n:Matrix.LocRotScale(a[n].translation.lerp(b[n].translation,w),a[n].to_quaternion().slerp(b[n].to_quaternion(),w),Vector((1,1,1))) for n in NAMES}
def meshco():
    ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh()
    v=np.empty(len(m.vertices)*3);m.vertices.foreach_get('co',v);ev.to_mesh_clear();return v.reshape(-1,3)
pv=np.array([v.value for v in body.data.attributes['piece'].data]);co=np.array([v.co[:] for v in body.data.vertices])
feet=np.isin(pv,(12,14))
UP=Vector((0,0,1))
FOOT={s:rig.data.bones[f'B_{s}_Foot'].matrix_local.copy() for s in 'LR'}
FWD={s:(rig.data.bones[f'B_{s}_Toe0'].head_local-FOOT[s].translation) for s in 'LR'}
for v in FWD.values():v.z=0;v.normalize()

def leg_ik(s,ank,Rfoot):
    # Same two-segment solve as the Native American foot plant, preserving fitted bone lengths.
    th,ca,ft=(f'B_{s}_{b}' for b in ('Thigh','Calf','Foot'))
    H,K,A=(armik.W(rig,b).translation.copy() for b in (th,ca,ft))
    l1,l2=(K-H).length,(A-K).length;d=ank-H;u=d.normalized()
    assert d.length<(l1+l2)*.9995,(s,'unreachable planted ankle',d.length,l1+l2)
    forward=Rfoot@FOOT[s].to_3x3().inverted()@FWD[s]
    v=(forward-u*forward.dot(u)).normalized()
    c=max(-1,min(1,(l1*l1+d.length*d.length-l2*l2)/(2*l1*d.length)))
    knee=H+l1*(u*c+v*math.sqrt(max(0,1-c*c)))
    for bone,child,target in ((th,ca,knee),(ca,ft,ank)):
        M=armik.W(rig,bone);cur=armik.W(rig,child).translation-M.translation
        q=cur.rotation_difference(target-M.translation)
        armik.set_world(rig,bone,armik.rot_world(M,q.to_matrix()@M.to_3x3()))
    armik.set_world(rig,ft,armik.rot_world(armik.W(rig,ft),Rfoot))
    assert (armik.W(rig,ft).translation-ank).length<1e-5

def attack_legs(t):
    # Native a/b crouch -> c/d upright turned aim -> e recoil -> g/h low carry.
    w=smooth(t/.35)*smooth((1.25-t)/.40)
    recoil=math.sin(math.pi*max(0,min(1,(t-.625)/.25)))**2
    M=rig.data.bones['B_Pelvis'].matrix_local.copy()
    M=armik.rot_world(M,Matrix.Rotation(math.radians(-18)*w,3,'Z')@M.to_3x3())
    M.translation+=Vector((-.025*w,-.012*w+.020*recoil,.035*w-.012*recoil))
    armik.set_world(rig,'B_Pelvis',M)
    for side in 'LR':
        M0=FOOT[side];pivot=M0.translation.copy();pivot.z=0
        yaw=math.radians(-14 if side=='R' else -3)*w
        R=Matrix.Rotation(yaw,3,'Z')
        # A small toe lift during the pivot settles before the aim hold.
        lift=math.sin(math.pi*min(1,t/.35))**2 if t<.35 else 0
        lift+=math.sin(math.pi*min(1,max(0,(t-.9)/.35)))**2 if t>.9 else 0
        pitch=math.radians(-7)*lift if side=='R' else 0
        axis=UP.cross(R@FWD[side]);R=Quaternion(axis,pitch).to_matrix()@R
        sole=co[pv==(12 if side=='R' else 14)]
        ankle=pivot+R@(M0.translation-pivot)
        transformed=np.array([tuple(ankle+R@(Vector(v)-M0.translation)) for v in sole])
        ankle.z-=float(transformed[:,2].min())
        leg_ik(side,ankle,R@M0.to_3x3())
def stabilize_head():
    C=armik.W(rig,'B_Spine2')@rig.data.bones['B_Spine2'].matrix_local.inverted()
    forward=C.to_3x3()@Vector((0,-1,0));yaw=math.atan2(forward.x,-forward.y)*.35
    for n in ('B_Neck','B_Head'):
        desired=Matrix.Rotation(yaw,3,'Z')@rig.data.bones[n].matrix_local.to_3x3()
        armik.set_world(rig,n,armik.rot_world(armik.W(rig,n),desired))
def secondary():
    for s in 'LR':
        fb,hb=rig.data.bones[f'B_{s}_Forearm'],rig.data.bones[f'B_{s}_Hand']
        ax=(fb.matrix_local.inverted()@hb.head_local).normalized()
        dq=(rig.pose.bones[fb.name].matrix.inverted()@rig.pose.bones[hb.name].matrix).to_quaternion()@(fb.matrix_local.inverted()@hb.matrix_local).to_quaternion().inverted()
        _,tw=armik.split_swing_twist(dq,ax)
        rig.pose.bones[f'B_{s}_ForearmTwist'].rotation_quaternion=Quaternion(ax,tw*.6)
        ub=rig.data.bones[f'B_{s}_UpperArm'];ax=(ub.matrix_local.inverted()@fb.head_local).normalized()
        _,tw=armik.split_swing_twist(rig.pose.bones[ub.name].rotation_quaternion,ax)
        rig.pose.bones[f'B_{s}_UpperArmTwist'].rotation_quaternion=Quaternion(ax,-tw*.5)
        cb=rig.data.bones[f'B_{s}_Clavicle'];C=armik.W(rig,cb.name)@cb.matrix_local.inverted()
        ref=C.to_3x3()@(fb.head_local-ub.head_local);cur=armik.W(rig,fb.name).translation-armik.W(rig,ub.name).translation
        q=Quaternion().slerp(ref.rotation_difference(cur),.40)
        armik.set_world(rig,f'B_{s}_Pauldron',armik.rot_world(armik.W(rig,f'B_{s}_Pauldron'),q.to_matrix()@C.to_3x3()@ub.matrix_local.to_3x3()))
    bpy.context.view_layer.update()
for action in bpy.data.actions:common.action_continuity(action)
SOURCE={name:bpy.data.actions[name] for name in ('Walking','Running','Attack','Hit','Death')}
# Cache source frames before replacing any actions; they were imported at 30 fps.
COUNTS={'Standing':120,'Walking':48,'Running':44,'Attack':75,'Hit':36,'Death':90,'Fidget':75}
FRAMES={n:list(range(0,end,1 if n in ('Walking','Running') else 2))+[end] for n,end in COUNTS.items()}
BASE={n:sample(a,0) for n,a in SOURCE.items()}
ARM_REFERENCE=sample(SOURCE['Attack'],8)
inputs={};source_arms={}
for name,frames in FRAMES.items():
    poses=[];source_arms[name]=[]
    for f in frames:
        t=f/60;end=COUNTS[name]
        if name in ('Standing','Fidget'):p={n:m.copy() for n,m in REST.items()}
        elif name=='Attack':
            sf=float(np.interp(t,[0,.25,.625,.875,1.25],[0,8,12,19,30]));p=sample(SOURCE[name],sf)
            p=mix(REST,p,.20*smooth(t/.18)*smooth((1.25-t)/.25))
            for n in p:
                if any(k in n for k in ('Thigh','Calf','Foot','Toe','Pelvis')):p[n]=REST[n].copy()
        elif name=='Hit':
            source=sample(SOURCE[name],min(t*30,15))
            relative={n:Matrix.LocRotScale(source[n].translation-BASE[name][n].translation,source[n].to_quaternion()@BASE[name][n].to_quaternion().inverted(),Vector((1,1,1))) for n in NAMES}
            p=mix(REST,relative,.35*smooth(f/8)*smooth((end-f)/10))
        elif name=='Death':p=mix(REST,sample(SOURCE[name],min(max(t-.166667,0)*30,40)),smooth(f/24))
        else:p=sample(SOURCE[name],f/2)
        put(p)
        if name=='Attack':attack_legs(t)
        if name in ('Standing','Fidget'):
            pb=rig.pose.bones['B_Spine1'];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=Quaternion((1,0,0),math.radians(.6)*math.sin(2*math.pi*f/end))
        if name=='Running':
            d=armik.W(rig,'B_Neck').translation-armik.W(rig,'B_Spine').translation
            lean=math.atan2(-d.y,d.z);M=armik.W(rig,'B_Spine')
            armik.set_world(rig,'B_Spine',armik.rot_world(M,Quaternion((1,0,0),math.radians(13)-lean).to_matrix()@M.to_3x3()))
        if name!='Death':stabilize_head()
        source_arms[name].append(snap())
        # A bent source elbow gives the solver a stable anatomical bend plane.
        for s in 'LR':
            for b in ('Clavicle','UpperArm','Forearm','Hand'):
                rig.pose.bones[f'B_{s}_{b}'].matrix_basis=Matrix() if b=='Clavicle' else ARM_REFERENCE[f'B_{s}_{b}']
        if name=='Attack':
            w=smooth(t/.35)*smooth((1.25-t)/.40)
            M=armik.W(rig,'B_L_Clavicle');R=Quaternion((0,0,1),math.radians(-12)*w).to_matrix()
            armik.set_world(rig,'B_L_Clavicle',armik.rot_world(M,R@M.to_3x3()))
        bpy.context.view_layer.update();xyz=meshco();low=float(xyz[:,2].min() if name=='Death' else xyz[feet,2].min())
        dz=-low if name!='Running' else max(-low,0)
        M=armik.W(rig,'B_Pelvis');M.translation.z+=dz;armik.set_world(rig,'B_Pelvis',M)
        poses.append(snap())
    inputs[name]=poses
# Level each sole across its width; retain the source heel strike and toe-off pitch.
# The old median pitch included airborne feet and tipped the planted shoes onto their heels.
for name in ('Walking','Running'):
    for i,p in enumerate(inputs[name]):
        put(p);oldlow=float(meshco()[feet,2].min())
        for side in 'LR':
            M=armik.W(rig,f'B_{side}_Foot');D=M.to_3x3()@FOOT[side].to_3x3().inverted()
            source_forward=D@FWD[side];right=D@FWD[side].cross(UP)
            right.z=0;right.normalize();heading=UP.cross(right)
            pitch=math.atan2(source_forward.z,source_forward.dot(heading))
            forward=heading*math.cos(pitch)+UP*math.sin(pitch)
            normal=right.cross(forward).normalized()
            basis=Matrix((right,forward,normal)).transposed()
            rest=Matrix((FWD[side].cross(UP),FWD[side],UP)).transposed()
            R=basis@rest.transposed()@FOOT[side].to_3x3()
            armik.set_world(rig,f'B_{side}_Foot',armik.rot_world(M,R))
        low=float(meshco()[feet,2].min());M=armik.W(rig,'B_Pelvis')
        M.translation.z+=(-low if name=='Walking' else max(0,oldlow)-low)
        armik.set_world(rig,'B_Pelvis',M);inputs[name][i]=snap()
base_carry=Vector((-.36,-.32,.73));base_aim=Vector((-.08,-.47,1.055))
Rcarry=Matrix.Rotation(math.radians(25),3,'X')@Matrix.Rotation(math.pi,3,'Z')
Raim=Matrix.Rotation(math.radians(-4),3,'X')@Matrix.Rotation(math.pi,3,'Z')
Hfree=Rcarry@fit.basis((0,0,1),(1,0,0))@fit.LOCAL['L'].transposed()
def support(name,t):
    return smooth(t/.55)*smooth((1.25-t)/.55) if name=='Attack' else 0
def targets(name,f):
    t=f/60;w=0;recoil=0
    if name=='Attack':
        w=smooth(t/.35)*smooth((1.25-t)/.40)
        recoil=math.sin(math.pi*max(0,min(1,(t-.625)/.25)))**2
    D=armik.W(rig,'B_Spine2')@rig.data.bones['B_Spine2'].matrix_local.inverted()
    C=(D@base_carry).lerp(base_aim+D.translation,w)
    front=D.to_3x3()@Vector((0,-1,0));yaw=math.atan2(front.x,-front.y)
    R=Matrix.Rotation(yaw*(1-w),3,'Z')@Rcarry.to_quaternion().slerp(Raim.to_quaternion(),w).to_matrix()
    if name in ('Walking','Running','Death'):
        R=D.to_3x3()@Rcarry
        if name=='Running':C=D@(base_carry+Vector((0,0,.07)))
    if recoil:
        R=Quaternion((1,0,0),math.radians(-20)*recoil).to_matrix()@R;C.y+=.025*recoil;C.z+=.015*recoil
    C.y-=.055*math.sin(math.pi*w)
    C.x-=.08*math.sin(math.pi*w)
    out={}
    for s in 'RL':
        H=fit.hand_rotation(s,R);grip=C+R@Vector((0,0,0) if s=='R' else (0,.09,.025));wrist=grip-H@Vector(G[s]['handle_centre_hand_local'])
        if s=='L':
            free=D@Vector((.31,-.17,.76));freeH=D.to_3x3()@Hfree
            if name=='Fidget':freeH=Quaternion((1,0,0),math.radians(-65)*math.sin(math.pi*t/1.25)**2).to_matrix()@freeH;free=D@Vector((.31-.11*math.sin(math.pi*t/1.25)**2,-.17+.04*math.sin(math.pi*t/1.25)**2,.76+.17*math.sin(math.pi*t/1.25)**2))
            join=support(name,t)
            approach=min(1,join/.65)
            offset=R@Vector((-.35355339,.35355339,-.86602540))*.12
            if join<.65:
                wrist=free.lerp(wrist+offset,approach)+Vector((.09,-.08,0))*math.sin(math.pi*approach)
                H=freeH.to_quaternion().slerp(H.to_quaternion(),approach).to_matrix()
            else:wrist+=offset*(1-smooth((join-.65)/.35))
        out[s]=(wrist,H)
    return C,R,w,out
PHIS=list(range(-180,180,10));stats={};result={}
for name,frames in FRAMES.items():
    bodyposes=inputs[name];tg=[];tables={s:[] for s in 'RL'}
    for f,p in zip(frames,bodyposes):
        put(p);C,R,w,targets_=targets(name,f);tg.append((C.copy(),R.copy(),w,targets_))
        for s in 'RL':
            wrist,H=targets_[s];S=armik.W(rig,f'B_{s}_UpperArm').translation.copy();axis=(wrist-S).normalized()
            base=Vector((.5 if s=='L' else -.5,.03,.75))-S;base=(base-axis*base.dot(axis)).normalized()
            candidates=[]
            for phi in PHIS:
                put(p);reach=armik.solve(rig,s,wrist,S+Quaternion(axis,math.radians(phi))@base,H)
                sw,tw=armik.wrist_cost(rig,s,H)
                ub=rig.data.bones[f'B_{s}_UpperArm'];fb=rig.data.bones[f'B_{s}_Forearm']
                uax=(ub.matrix_local.inverted()@fb.head_local).normalized()
                _,ut=armik.split_swing_twist(rig.pose.bones[ub.name].rotation_quaternion,uax);ut=abs(math.degrees(ut))
                elbow=armik.W(rig,f'B_{s}_Forearm').translation
                chest=armik.W(rig,'B_Spine2')@rig.data.bones['B_Spine2'].matrix_local.inverted()
                clearance=0
                for v in (elbow,elbow.lerp(wrist,.35),elbow.lerp(wrist,.65)):
                    v=chest.inverted()@v
                    if .65<v.z<1.08:clearance+=max(0,1-math.hypot(v.x/.29,v.y/.28))**2*20000
                # Keep the trigger elbow outside the beard as the torso turns.
                if name=='Attack' and s=='R':
                    clearance+=max(0,elbow.x+.30)**2*300000*w
                cost=clearance+max(0,abs(tw)-145)**2*5+sw+.02*sw*sw+.5*abs(tw)+.45*ut+.006*ut*ut+max(0,reach-.98)*10000
                arm={f'B_{s}_{b}':rig.pose.bones[f'B_{s}_{b}'].matrix_basis.copy() for b in ('UpperArm','Forearm','Hand')}
                qs=np.array([tuple(arm[f'B_{s}_{b}'].to_quaternion()) for b in ('UpperArm','Forearm','Hand')])
                candidates.append((cost,arm,qs,sw,tw,reach))
            tables[s].append(candidates)
    chosen={}
    for s in 'RL':
        tabs=tables[s]
        if name in ('Attack','Hit','Fidget','Death'):
            anchor=np.array([tuple(result['Standing'][1][0][f'B_{s}_{b}'].to_quaternion()) for b in ('UpperArm','Forearm','Hand')])
        else:anchor=tabs[0][int(np.argmin([c[0] for c in tabs[0]]))][2]
        penalty=lambda tab:np.array([sum((np.degrees(2*np.arccos(np.clip(np.abs(np.sum(c[2]*anchor,axis=1)),0,1))))**2)*100 for c in tab])
        acc=np.array([c[0] for c in tabs[0]])+penalty(tabs[0]);backs=[]
        for step,(prev,cur) in enumerate(zip(tabs[:-1],tabs[1:]),1):
            qa=np.array([c[2] for c in prev]);qb=np.array([c[2] for c in cur])
            dots=np.abs(np.einsum('ibk,jbk->ijb',qa,qb));angle=np.degrees(2*np.arccos(np.clip(dots,0,1)))
            transition=np.sum(angle**2,axis=2)*.35
            transition[np.max(angle,axis=2)>32*(frames[step]-frames[step-1])/2]=1e10
            costs=acc[:,None]+transition;back=np.argmin(costs,axis=0);backs.append(back)
            previous=acc.copy()
            acc=costs[back,np.arange(len(PHIS))]+np.array([c[0] for c in cur])
            assert float(acc.min())<1e10,(name,s,'step',frames[step],'minimum joint step',float(np.min(np.max(angle[previous<1e10],axis=2))))
        acc+=penalty(tabs[-1]) if name!='Death' else 0
        assert float(acc.min())<1e10,(name,s,'No continuous arm path')
        k=int(acc.argmin());path=[k]
        for back in reversed(backs):k=int(back[k]);path.append(k)
        path.reverse();chosen[s]=[tab[k] for tab,k in zip(tabs,path)]
        angles=[np.degrees(2*np.arccos(np.clip(np.abs(np.sum(a[2]*b[2],axis=1)),0,1))) for a,b in zip(chosen[s][:-1],chosen[s][1:])]
        print('ARM STEP',name,s,round(float(np.max(angles)),2),flush=True)
    poses=[];st=[]
    for i,(f,p) in enumerate(zip(frames,bodyposes)):
        put(p);C,R,w,_=tg[i]
        for s in 'RL':
            for n,m in chosen[s][i][1].items():rig.pose.bones[n].matrix_basis=m
            weight=1 if s=='R' else .7+.3*smooth(support(name,f/60)/.65)
            for n,q in G[s]['finger_local'].items():rig.pose.bones[n].rotation_quaternion=Quaternion().slerp(Quaternion(q),weight)
        if name=='Death':
            for s in 'LR':
                release=.8*smooth((f-(34 if s=='R' else 24))/18)
                for b in ('Clavicle','UpperArm','Forearm','Hand'):
                    n=f'B_{s}_{b}';pb=rig.pose.bones[n]
                    pb.rotation_quaternion=pb.rotation_quaternion.slerp(source_arms[name][i][n].to_quaternion(),release)
                for n in G[s]['finger_local']:
                    rig.pose.bones[n].rotation_quaternion=rig.pose.bones[n].rotation_quaternion.slerp(Quaternion(),release*.8)
                # Released hands relax instead of retaining the source rig's excessive wrist bend.
                if f>34:
                    hb=rig.data.bones[f'B_{s}_Hand'];fb=rig.data.bones[f'B_{s}_Forearm'];pb=rig.pose.bones[hb.name]
                    axis=hb.matrix_local.to_3x3().inverted()@(hb.head_local-fb.head_local).normalized()
                    swing,twist=armik.split_swing_twist(pb.rotation_quaternion,axis)
                    angle=swing.angle if swing.angle<=math.pi else 2*math.pi-swing.angle
                    if angle>math.radians(55):swing=Quaternion().slerp(swing,math.radians(55)/angle)
                    pb.rotation_quaternion=swing@Quaternion(axis,twist)
        secondary()
        # The crossbow is a separate rigid bone; its pose remains explicit through death.
        M=R.to_4x4();M.translation=C;armik.set_world(rig,'Crossbow',M)
        if name=='Death':
            xyz=meshco();low=float(xyz[:,2].min())
            root=armik.W(rig,'B_Pelvis');root.translation.z-=low;armik.set_world(rig,'B_Pelvis',root)
            M.translation.z-=low
            if f<=34:
                # The grip releases along its measured clear axis before the prop tumbles.
                M.translation+=R@Vector((0,0,.18*smooth((f-24)/10)))
                drop_start=M.copy()
                drop_direction=drop_start.translation-armik.W(rig,'B_Spine2').translation
                drop_direction.z=0;drop_direction.normalize()
            else:
                u=smooth((f-34)/14);fall=max(0,min(1,(f-34)/30));turn=smooth((f-42)/22)
                landing=drop_start.translation+drop_direction*.9;landing.z=.075
                M=drop_start.to_quaternion().slerp(Matrix.Rotation(math.pi,3,'Z').to_quaternion(),turn).to_matrix().to_4x4()
                M.translation=drop_start.translation.lerp(landing,u)
                M.translation.z=drop_start.translation.z*(1-fall*fall)+landing.z*fall*fall
                floor=min((M@v.co).z for v in prop.data.vertices)
                M.translation.z-=min(0,floor)
            armik.set_world(rig,'Crossbow',M)
        poses.append(snap());st.append({s:{'swing':chosen[s][i][3],'twist':chosen[s][i][4],'reach':chosen[s][i][5]} for s in 'RL'})
    if name in ('Standing','Walking','Running'):poses[-1]=poses[0]
    assert max(x[s]['reach'] for x in st for s in 'LR')<1,(name,'unreachable hand target')
    result[name]=(frames,poses);stats[name]=st
    print('AUTHORED',name,{s:{'swing':round(max(x[s]['swing'] for x in st),1),'twist':round(max(abs(x[s]['twist']) for x in st),1),'reach':round(max(x[s]['reach'] for x in st),3)} for s in 'LR'},flush=True)
result['Dead']=([0,60],[result['Death'][1][-1]]*2)
# One-shots enter and recover to the exact Standing pose.
standing=result['Standing'][1][0]
for name in ('Attack','Hit','Fidget'):
    f,p=result[name];p[0]=standing;p[-1]=standing
result['Death'][1][0]=standing
for a in list(bpy.data.actions):bpy.data.actions.remove(a)
for name,(frames,poses) in result.items():
    a=bpy.data.actions.new(name);a.use_fake_user=True;activate(a);prev={}
    for f,p in zip(frames,poses):
        for n,m in p.items():
            pb=rig.pose.bones[n];q=m.to_quaternion()
            if n in prev and q.dot(prev[n])<0:q=-q
            prev[n]=q;pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q;pb.location=m.translation;pb.scale=(1,1,1)
            pb.keyframe_insert('rotation_quaternion',frame=f)
            if n in ('B_Pelvis','Crossbow'):pb.keyframe_insert('location',frame=f)
    for layer in a.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for fc in bag.fcurves:
                    for k in fc.keyframe_points:k.interpolation='LINEAR'
    a.use_frame_range=True;a.frame_start=frames[0];a.frame_end=frames[-1]
activate(None)
# Skin the prop rigidly so the exporter carries its authored transform with every role.
prop.matrix_world=Matrix();prop.parent=rig
g=prop.vertex_groups.new(name='Crossbow');g.add(list(range(len(prop.data.vertices))),1,'REPLACE')
mod=prop.modifiers.new('Armature','ARMATURE');mod.object=rig
(P/'work/arm_fit.json').write_text(json.dumps(stats,indent=1))
(P/'work/clip_timing.json').write_text(json.dumps({'fps':60,'durations':{n:f[-1]/60 for n,(f,p) in result.items()},'attack_impact_s':.625,'native_attack_s':1.25,'native_hit_max_s':.625},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/motion_native.blend'))
for view in (() if os.environ.get('M632_FAST_CHECK') else ('front','left','back')):
    sys.argv=['pilot_sheet.py','--',str(P/'work/motion_native.blend'),str(P/f'review/native_{view}'),view,'7',*result]
    runpy.run_path(str(P/'scripts/pilot_sheet.py'),run_name='__main__')
