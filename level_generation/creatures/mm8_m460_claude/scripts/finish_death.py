"""Fit the closed skirt around both legs through the collapse, and settle the released staff."""
import bpy,sys,json,ast,math,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/motion_robed.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];staff=bpy.data.objects['Staff'];scene=bpy.context.scene
pv=np.array([a.value for a in body.data.attributes['piece'].data]);rest=np.array([v.co[:] for v in body.data.vertices])
ci=np.where(np.isin(pv,[2,5,12,13,14,15,16]))[0]
bones=[b.name for b in rig.data.bones if b.name.startswith('Robe_')];index={n:i for i,n in enumerate(bones)}
W=np.zeros((len(ci),len(bones)))
for j,i in enumerate(ci):
    for g in body.data.vertices[int(i)].groups:
        n=body.vertex_groups[g.group].name
        if n in index:W[j,index[n]]=g.weight
pinv=np.linalg.solve(W.T@W+.002*np.eye(len(bones)),W.T)
z=rest[ci,2];u=np.clip((1.13-z)/1.105,0,1);x=rest[ci,0];y=rest[ci,1]
def hermite(points,t):
    knots=np.array([0,.55,1]);out=np.zeros((len(t),3));der=np.zeros_like(out)
    slopes=np.array([(points[1]-points[0])/.55,points[2]-points[0],(points[2]-points[1])/.45])
    for j in range(2):
        use=(t>=knots[j])&(t<=knots[j+1]);h=knots[j+1]-knots[j];q=((t[use]-knots[j])/h)[:,None]
        out[use]=(2*q**3-3*q*q+1)*points[j]+(q**3-2*q*q+q)*h*slopes[j]+(-2*q**3+3*q*q)*points[j+1]+(q**3-q*q)*h*slopes[j+1]
        der[use]=(6*q*q-6*q)/h*points[j]+(3*q*q-4*q+1)*slopes[j]+(-6*q*q+6*q)/h*points[j+1]+(3*q*q-2*q)*slopes[j+1]
    return out,der
def coords(ob):
    ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();v=np.array([q.co[:] for q in me.vertices]);ev.to_mesh_clear();return v
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
for b in rig.data.edit_bones:
    if b.name.startswith('Robe_'):b.use_connect=False
bpy.ops.object.mode_set(mode='OBJECT')
for name in ['Standing','Walking','Attack','Cast','Hit','Fidget']:
    a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
    for f in [0,int(a.frame_range[1])]:
        for n in bones:
            rig.pose.bones[n].location=(0,0,0);rig.pose.bones[n].keyframe_insert('location',frame=f)
act=bpy.data.actions['Death'];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
sys.path.insert(0,str(p/'scripts'));import arm_solver as sol
right=sol.Side('B_R_');prev=None;early=[];release=None
for f in range(21):
    scene.frame_set(f);original={n:rig.pose.bones[n].rotation_quaternion.copy() for n in ['B_R_UpperArm','B_R_Forearm','B_R_Hand']}
    t=min(f/10,1);result=right.solve(Vector((-.34,-.20-.08*t,1.27-.09*t)),Vector((-.055,.015,1)).normalized(),Vector((-.35,0,-1)),phi_prev=prev,steps=144);right.apply(result);prev=result['phi']
    blend=float(np.clip((f-10)/10,0,1));blend=blend*blend*(3-2*blend)
    for n,q in original.items():
        pb=rig.pose.bones[n];pb.rotation_quaternion=pb.rotation_quaternion.slerp(q,blend);pb.keyframe_insert('rotation_quaternion',frame=f)
    if f==10:
        rig.pose.bones['Staff'].matrix_basis.identity();bpy.context.view_layer.update();release=rig.pose.bones['Staff'].matrix.copy()
for f in range(int(act.frame_range[1])+1):
    scene.frame_set(f)
    if f<=10:rig.pose.bones['Staff'].matrix_basis.identity()
    else:
        t=float(np.clip((f-10)/17,0,1));t=t*t*(3-2*t);q=Vector((0,0,1)).rotation_difference(Vector((.96,.28,.015)).normalized());m=release.to_quaternion().slerp(q,t).to_matrix().to_4x4();m.translation=release.translation.lerp(Vector((.10,-.44,.048)),t);m.translation.z+=.10*math.sin(math.pi*t);rig.pose.bones['Staff'].matrix=m
    rig.pose.bones['Staff'].keyframe_insert('location',frame=f);rig.pose.bones['Staff'].keyframe_insert('rotation_quaternion',frame=f)
samples=[];residual=[]
for f in range(int(act.frame_range[1])+1):
    scene.frame_set(f);sim=coords(body)[ci];delta=rig.pose.bones['B_Pelvis'].matrix@rig.data.bones['B_Pelvis'].matrix_local.inverted()
    top=np.array(delta@Vector((0,0,1.13)));knees=np.array([rig.pose.bones['B_'+s+'_Calf'].head[:] for s in 'LR']);feet=np.array([rig.pose.bones['B_'+s+'_Foot'].head[:] for s in 'LR'])
    direction=feet-knees;feet+=direction/np.linalg.norm(direction,axis=1)[:,None]*.12
    centre,tangent=hermite(np.array([top,knees.mean(0),feet.mean(0)]),u)
    up=-tangent/np.linalg.norm(tangent,axis=1)[:,None];right=np.array(delta.to_3x3()@Vector((1,0,0)))
    across=right-(up@right)[:,None]*up;across/=np.linalg.norm(across,axis=1)[:,None];back=np.cross(up,across)
    left,_=hermite(np.array([top,knees[0],feet[0]]),u);rightpath,_=hermite(np.array([top,knees[1],feet[1]]),u);sep=left-rightpath
    rx=np.interp(z,[.025,.3,.6,.95,1.13],[.26,.245,.22,.18,.16]);ry=np.interp(z,[.025,.3,.6,.95,1.13],[.205,.19,.16,.13,.115])
    wx=np.maximum(rx,abs(np.sum(sep*across,axis=1))*.5+.15);wy=np.maximum(ry,abs(np.sum(sep*back,axis=1))*.5+.145)
    target=centre+across*(x*wx/rx)[:,None]+back*(y*wy/ry)[:,None]
    target[:,2]=np.maximum(target[:,2],.012)
    t=float(np.clip(f/10,0,1));t=t*t*(3-2*t);target=sim*(1-t)+target*t
    for n in bones:
        rb=rig.data.bones[n];v=rb.head_local;bu=np.array([np.clip((1.13-v.z)/1.105,0,1)])
        c,d=hermite(np.array([top,knees.mean(0),feet.mean(0)]),bu);az=-d[0]/np.linalg.norm(d[0]);ax=np.array(delta.to_3x3()@Vector((1,0,0)));ax-=az*(ax@az);ax/=np.linalg.norm(ax);ay=np.cross(az,ax)
        rotation=Matrix(np.column_stack([ax,ay,az]).tolist());m=(rotation@rb.matrix_local.to_3x3()).to_4x4();m.translation=Vector(c[0]+ax*v.x+ay*v.y)
        rig.pose.bones[n].matrix=m;bpy.context.view_layer.update()
    raw=[rig.pose.bones[n].matrix.copy() for n in bones];base=coords(body)[ci]
    correction=pinv@(target-base);residual.append(float(np.max(np.linalg.norm(base+W@correction-target,axis=1))))
    samples.append((f,raw,correction))
for f,raw,correction in samples:
    scene.frame_set(f)
    for j,n in enumerate(bones):
        m=raw[j].copy();m.translation+=Vector(correction[j]);rig.pose.bones[n].matrix=m;bpy.context.view_layer.update()
        rig.pose.bones[n].keyframe_insert('location',frame=f);rig.pose.bones[n].keyframe_insert('rotation_quaternion',frame=f)
    if f>=10:
        low=coords(staff)[:,2].min();t=float(np.clip((f-10)/17,0,1));t=t*t*(3-2*t)
        m=rig.pose.bones['Staff'].matrix.copy();m.translation.z+=(.005-low)*t;rig.pose.bones['Staff'].matrix=m;bpy.context.view_layer.update()
        rig.pose.bones['Staff'].keyframe_insert('location',frame=f);rig.pose.bones['Staff'].keyframe_insert('rotation_quaternion',frame=f)
# Preserve the free-hand gesture while fitting its swing and roll to this wrist.
for a in [bpy.data.actions[n] for n in ['Standing','Walking','Attack','Cast','Hit','Death','Fidget']]:
    rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];pb=rig.pose.bones['B_L_Hand'];hb=pb.bone;fb=rig.data.bones['B_L_Forearm'];axis=(hb.matrix_local.to_3x3().inverted()@(hb.head_local-fb.head_local)).normalized();records=[]
    for f in range(int(a.frame_range[1])+1):
        scene.frame_set(f);q=pb.rotation_quaternion.copy();tw=2*math.atan2(Vector((q.x,q.y,q.z)).dot(axis),q.w);tw=(tw+math.pi)%(2*math.pi)-math.pi;sw=q@Quaternion(axis,tw).inverted()
        if sw.w<0:sw=-sw
        records.append((f,Quaternion().slerp(sw,.49)@Quaternion(axis,.50*tw)))
    for f,q in records:pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f)
rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
pb=rig.pose.bones['B_R_Hand'];hb=pb.bone;fb=rig.data.bones['B_R_Forearm'];axis=(hb.matrix_local.to_3x3().inverted()@(hb.head_local-fb.head_local)).normalized()
for f in range(11,int(act.frame_range[1])+1):
    scene.frame_set(f);staffM=rig.pose.bones['Staff'].matrix.copy();q=pb.rotation_quaternion.copy();tw=2*math.atan2(Vector((q.x,q.y,q.z)).dot(axis),q.w);tw=(tw+math.pi)%(2*math.pi)-math.pi;sw=q@Quaternion(axis,tw).inverted()
    if sw.w<0:sw=-sw
    weight=min((f-10)/8,1);pb.rotation_quaternion=Quaternion().slerp(sw,1-.16*weight)@Quaternion(axis,tw);pb.keyframe_insert('rotation_quaternion',frame=f);bpy.context.view_layer.update();rig.pose.bones['Staff'].matrix=staffM;rig.pose.bones['Staff'].keyframe_insert('location',frame=f);rig.pose.bones['Staff'].keyframe_insert('rotation_quaternion',frame=f)
# A least-squares cloth contact pass uses the actual skin surface after the fitted drape.
skinfaces=[tuple(face.vertices) for face in body.data.polygons if all(pv[i] in [0,3,4] for i in face.vertices)]
contact_report={}
for name in ['Standing','Walking','Attack','Cast','Hit','Death','Fidget']:
    a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];worst=0
    for f in range(int(a.frame_range[1])+1):
        scene.frame_set(f)
        for iteration in range(5):
            P=coords(body);tree=BVHTree.FromPolygons(P.tolist(),skinfaces);shift=np.zeros((len(ci),3))
            for j,i in enumerate(ci):
                if W[j].sum()<.25:continue
                pt=Vector(P[i]);loc,n,face,d=tree.find_nearest(pt,.075)
                if loc is not None and d>.001 and (pt-loc).dot(n)<-.6*d:shift[j]=np.array(n)*(d+.006)
                shift[j,2]=max(shift[j,2],.006-P[i,2])
            correction=pinv@shift
            if np.linalg.norm(correction,axis=1).max()<.0002:break
            correction*=np.minimum(1,.025/np.maximum(np.linalg.norm(correction,axis=1),1e-8))[:,None]
            raw=[rig.pose.bones[n].matrix.copy() for n in bones]
            for j,n in enumerate(bones):
                m=raw[j].copy();m.translation+=Vector(correction[j]);rig.pose.bones[n].matrix=m;bpy.context.view_layer.update()
        for n in bones:
            rig.pose.bones[n].keyframe_insert('location',frame=f);rig.pose.bones[n].keyframe_insert('rotation_quaternion',frame=f)
        worst=max(worst,float(np.linalg.norm(shift,axis=1).max()))
    contact_report[name]=worst;print('CLOTH_CONTACT_FIT',name,worst,flush=True)
FA=.6;UA=.5;tree=ast.parse((p/'scripts/twist_bones.py').read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'twist_about','bake_twist'}],type_ignores=[]),'twist_bake','exec'),globals())
for n in ['Standing','Walking','Attack','Cast','Hit','Death','Fidget']:bake_twist(bpy.data.actions[n])
rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
scene.frame_set(int(act.frame_range[1]));last={b.name:b.matrix_basis.copy() for b in rig.pose.bones}
dead=bpy.data.actions['Dead'];rig.animation_data.action=dead;rig.animation_data.action_slot=dead.slots[0]
for f in range(31):
    for n,m in last.items():
        b=rig.pose.bones[n];b.matrix_basis=m;b.keyframe_insert('rotation_quaternion',frame=f)
        if n in ['B_Pelvis','Staff'] or n.startswith('Robe_'):b.keyframe_insert('location',frame=f)
for a in [act,dead]:
    for l in a.layers:
        for s in l.strips:
            for bag in s.channelbags:
                for fc in bag.fcurves:
                    for k in fc.keyframe_points:k.interpolation='LINEAR'
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/motion_draped.blend'))
(p/'review/death_drape.json').write_text(json.dumps({'target_fit_max_residual_m':max(residual),'by_frame':residual,'contact_residual':contact_report},indent=2)+'\n')
