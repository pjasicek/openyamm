"""Settle fitted feet without changing bone lengths; remove the death carry solver's sudden elbow-plane change."""
import bpy,sys,math,json
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import armik
src,out=sys.argv[sys.argv.index('--')+1:];bpy.ops.wm.open_mainfile(filepath=src)
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene;names=[b.name for b in rig.data.bones]
rest=np.array([tuple(v.co) for v in body.data.vertices]);groups=[g.name for g in body.vertex_groups]
feet={s:np.array([sum(e.weight for e in v.groups if groups[e.group] in (f'B_{s}_Foot',f'B_{s}_Toe0'))>.5 for v in body.data.vertices]) for s in 'LR'}
def set_act(a):
    rig.animation_data.action=a
    if a is not None and len(a.slots):rig.animation_data.action_slot=a.slots[0]
def pos():
    bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();v=np.array([tuple(body.matrix_world@x.co) for x in me.vertices]);ev.to_mesh_clear();return v
def leg(s,dz):
    th,ca,ft=[f'B_{s}_{n}' for n in ('Thigh','Calf','Foot')]
    H,K,A=[armik.W(rig,n).translation.copy() for n in (th,ca,ft)];Rf=armik.W(rig,ft).to_3x3().normalized()
    a,b=(K-H).length,(A-K).length;T=A+Vector((0,0,dz));D=T-H;dist=min(D.length,(a+b)*.9999);u=D.normalized()
    v=K-H;v-=u*v.dot(u)
    if v.length<1e-5:v=Vector((0,-1,0))-u*u.dot(Vector((0,-1,0)))
    v.normalize();c=np.clip((a*a+dist*dist-b*b)/(2*a*dist),-1,1);Kn=H+a*(u*float(c)+v*math.sqrt(max(0,1-c*c)))
    M=armik.W(rig,th);q=(K-H).rotation_difference(Kn-H);armik.set_world(rig,th,armik.rot_world(M,q.to_matrix()@M.to_3x3().normalized()))
    M=armik.W(rig,ca);cur=armik.W(rig,ft).translation-M.translation;q=cur.rotation_difference(H+u*dist-M.translation)
    armik.set_world(rig,ca,armik.rot_world(M,q.to_matrix()@M.to_3x3().normalized()));armik.set_world(rig,ft,armik.rot_world(armik.W(rig,ft),Rf))
    assert abs((armik.W(rig,ca).translation-armik.W(rig,th).translation).length-a)<1e-5
report={}
for name in ('Standing','Walking','Running','Attack','Hit','Fidget','Death'):
    act=bpy.data.actions[name];frames=np.arange(0,float(act.frame_range[1])+.001,.25);saved=[]
    for f in frames:
        set_act(act);sc.frame_set(int(f),subframe=float(f%1));saved.append({n:rig.pose.bones[n].matrix_basis.copy() for n in names})
    rows=[];lows=[]
    for f,snap in zip(frames,saved):
        set_act(None)
        for n,m in snap.items():rig.pose.bones[n].matrix_basis=m
        V=pos();low={s:float(V[feet[s],2].min()) for s in 'LR'}
        if name=='Death':
            dz=.001-float(V[:,2].min());M=armik.W(rig,'B_Pelvis');M.translation.z+=dz;armik.set_world(rig,'B_Pelvis',M)
        else:
            # Preserve the source leg arc but keep the support foot close to the ground during flight.
            target=.001 if name!='Running' else min(.008,max(.001,min(low.values())*.06))
            dz=target-min(low.values());M=armik.W(rig,'B_Pelvis');M.translation.z+=dz;armik.set_world(rig,'B_Pelvis',M)
            if name in ('Standing','Attack','Fidget'):
                for _ in range(2):
                    V=pos()
                    for s in 'LR':leg(s,.001-float(V[feet[s],2].min()))
        V=pos();lows.append(float(V[:,2].min()) if name=='Death' else min(float(V[m,2].min()) for m in feet.values()))
        rows.append({n:(rig.pose.bones[n].rotation_quaternion.copy(),rig.pose.bones[n].location.copy()) for n in names})
    # Replace off-grid keys left by timing edits; the source and exported curves must share one sample grid.
    bpy.data.actions.remove(act);act=bpy.data.actions.new(name);act.use_fake_user=True
    act.use_frame_range=True;act.frame_start=float(frames[0]);act.frame_end=float(frames[-1])
    set_act(act);prev={}
    for f,snap in zip(frames,rows):
        for n,(q,l) in snap.items():
            if n in prev and q.dot(prev[n])<0:q=-q
            prev[n]=q;pb=rig.pose.bones[n];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=float(f))
            if n=='B_Pelvis':pb.location=l;pb.keyframe_insert('location',frame=float(f))
    report[name]={'min_surface_z_m':min(lows),'max_lowest_surface_z_m':max(lows)}
    print('CONTACT',name,report[name],flush=True)
for a in bpy.data.actions:
    for layer in a.layers:
        for strip in layer.strips:
            for cb in strip.channelbags:
                for fc in cb.fcurves:
                    for k in fc.keyframe_points:k.interpolation='LINEAR'
set_act(None);(P.parent/'work/contact_fit.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=out)
