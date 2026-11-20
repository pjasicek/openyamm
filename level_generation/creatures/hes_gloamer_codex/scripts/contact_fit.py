"""Adapt source arm paths to the longer forearms using minimal shoulder swing and measured skin contact."""
import bpy,sys,os,json,math
from pathlib import Path
import numpy as np
from mathutils import Vector,Quaternion
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).parent));import armik
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_timed.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene;me=body.data
names=[g.name for g in body.vertex_groups];co=np.array([v.co[:] for v in me.vertices]);piece=np.array([x.value for x in me.attributes['piece'].data])
W=np.zeros((len(co),len(names)))
for v in me.vertices:
    for g in v.groups:W[v.index,g.group]=g.weight
arm={s:W[:,[i for i,n in enumerate(names) if n.startswith('B_'+s+'_') and any(x in n for x in ['UpperArm','Forearm','Hand','Finger'])]].sum(1) for s in 'LR'}
hand={s:W[:,[i for i,n in enumerate(names) if n.startswith('B_'+s+'_') and any(x in n for x in ['Hand','Finger'])]].sum(1)>.5 for s in 'LR'}
other=W[:,[i for i,n in enumerate(names) if any(x in n for x in ['Thigh','Calf','Foot','Toe']) or n in ['B_Pelvis','B_Spine','B_Spine1','B_Spine2','B_Neck','B_Head']]].sum(1)
faces=[tuple(f.vertices) for f in me.polygons if piece[f.vertices[0]]==0]
AF={s:[f for f in faces if all(arm[s][i]>.93 for i in f)] for s in 'LR'}
OF=[f for f in faces if all(other[i]>.93 for i in f)]
restx=rig.data.bones['B_Spine2'].matrix_local.to_3x3().inverted()@Vector((1,0,0))
def setact(a):
    rig.animation_data.action=a
    if a is not None and len(a.slots):rig.animation_data.action_slot=a.slots[0]
def mesh():
    ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();a=np.empty(len(m.vertices)*3);m.vertices.foreach_get('co',a);ev.to_mesh_clear();return a.reshape(-1,3)
def restore(row):
    for n,m in row.items():rig.pose.bones[n].matrix_basis=m
    bpy.context.view_layer.update()
def rotate(s,angle,base):
    n='B_'+s+'_UpperArm';M=base[n];shoulder=M.translation
    elbow=base['B_'+s+'_Forearm'].translation;out=base['B_Spine2'].to_3x3()@restx*(1 if s=='L' else -1)
    axis=(elbow-shoulder).cross(out).normalized()
    armik.set_world(rig,n,armik.rot_world(M,Quaternion(axis,math.radians(angle)).to_matrix()@M.to_3x3()))
def floor(s):
    # Keep the enlarged fingers above the floor by bending the arm, never lifting the feet.
    for k in range(3):
        z=float(mesh()[hand[s],2].min())
        if z>=.004:break
        wrist=armik.W(rig,'B_'+s+'_Hand').translation.copy();wrist.z+=.006-z
        armik.solve(rig,s,wrist)
def overlaps(s):
    arr=mesh().tolist();return len(BVHTree.FromPolygons(arr,AF[s],all_triangles=True).overlap(BVHTree.FromPolygons(arr,OF,all_triangles=True)))
report={}
for name in ['Standing','Walking','Running','Attack','Hit','Death','Fidget','Cast']:
    act=bpy.data.actions[name];N=int(act.frame_range[1]);samples=[];required={s:[] for s in 'LR'}
    for f in range(N+1):
        setact(act);sc.frame_set(f);row={b.name:b.matrix_basis.copy() for b in rig.pose.bones};setact(None);restore(row)
        base={b.name:armik.W(rig,b.name).copy() for b in rig.pose.bones};samples.append((row,base))
        for s in 'LR':
            found=None
            for ang in range(0,76,3):
                restore(row);rotate(s,ang,base);floor(s)
                if overlaps(s)==0:found=ang;break
            assert found is not None,(name,f,s,'no clear shoulder swing within 75 degrees')
            required[s].append(found)
    curves={}
    for s in 'LR':
        raw=np.array(required[s],float)
        # A smooth upper envelope starts clearing the body before contact and avoids correction pops.
        raised=np.array([max(raw[j]*max(0,1-abs(i-j)/8) for j in range(max(0,i-7),min(len(raw),i+8))) for i in range(len(raw))])
        curves[s]=raised+np.where(raised>0,3,0)
    keys=[];maxhits=0
    for f,(row,base) in enumerate(samples):
        restore(row)
        for s in 'LR':rotate(s,float(curves[s][f]),base);floor(s)
        maxhits=max(maxhits,max(overlaps(s) for s in 'LR'))
        keys.append({b.name:(b.rotation_quaternion.copy(),b.location.copy()) for b in rig.pose.bones})
    setact(act);prev={}
    for f,row in enumerate(keys):
        for n,(q,l) in row.items():
            if n in prev and q.dot(prev[n])<0:q.negate()
            prev[n]=q.copy();b=rig.pose.bones[n];b.rotation_quaternion=q;b.location=l;b.keyframe_insert('rotation_quaternion',frame=f)
    for layer in act.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for fc in bag.fcurves:
                    for k in fc.keyframe_points:k.interpolation='LINEAR'
    report[name]={'max_shoulder_swing_deg':{s:float(curves[s].max()) for s in 'LR'},'max_remaining_intersections':maxhits}
    print('CONTACT',name,report[name],flush=True)
    (P/'review/contact_fit.json').write_text(json.dumps(report,indent=2)+'\n')
    setact(None)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_contact.blend'))
sys.stdout.flush();sys.stderr.flush();os._exit(0)
