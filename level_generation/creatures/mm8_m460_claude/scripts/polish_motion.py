"""Smooth the measured shoulder-weight transitions and finish released staff and ground contact."""
import bpy,sys,json,math,ast,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'))
# Preserve the original collapse arm arc after release.
bpy.ops.wm.open_mainfile(filepath=str(p/'work/motion_robed.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene
a=bpy.data.actions['Death'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];original=[]
for f in range(61):
    sc.frame_set(f);original.append({n:rig.pose.bones[n].rotation_quaternion.copy() for n in ['B_R_UpperArm','B_R_Forearm']})
bpy.ops.wm.open_mainfile(filepath=str(p/'work/motion_draped.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];staff=bpy.data.objects['Staff'];sc=bpy.context.scene
import armik
me=body.data;P0=np.array([v.co[:] for v in me.vertices]);pv=np.array([a.value for a in me.attributes['piece'].data]);names=[g.name for g in body.vertex_groups]
W=np.zeros((len(P0),len(names)))
for v in me.vertices:
    for g in v.groups:W[v.index,g.group]=g.weight
adj=[[] for _ in P0]
for e in me.edges:
    i,j=e.vertices
    if pv[i]==0 and pv[j]==0:adj[i].append(j);adj[j].append(i)
blend=np.clip((abs(P0[:,0])-.09)/.05,0,1)*np.clip((P0[:,2]-1.14)/.08,0,1)*np.clip((1.49-P0[:,2])/.07,0,1)*(pv==0)
for _ in range(6):
    nxt=W.copy()
    for i in np.where(blend>0)[0]:
        if adj[i]:nxt[i]=W[i]*(1-.55*blend[i])+W[adj[i]].mean(0)*(.55*blend[i])
    W=nxt
for i in np.where(blend>0)[0]:
    weights=W[i];order=np.argsort(weights)[-8:];total=weights[order].sum()
    for g in body.vertex_groups:g.remove([int(i)])
    for j in order:
        if weights[j]>.0001:body.vertex_groups[int(j)].add([int(i)],float(weights[j]/total),'REPLACE')
def coord(ob):
    ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();v=np.array([q.co[:] for q in mesh.vertices]);ev.to_mesh_clear();return v
def attach(a):
    rig.animation_data.action=None
    for b in rig.pose.bones:b.matrix_basis.identity()
    rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
for role in ['Walking','Hit']:
    a=bpy.data.actions[role];attach(a);records=[]
    for f in range(int(a.frame_range[1])+1):
        sc.frame_set(f);h=armik.W(rig,'B_R_Hand');e=armik.W(rig,'B_R_Forearm').translation
        # Move the elbow's pole outside the torso, keeping the fitted wrist and staff fixed.
        amount=1 if role=='Walking' else math.sin(math.pi*f/int(a.frame_range[1]))**2
        armik.solve(rig,'R',h.translation,pole=e+Vector((-.09,-.025,0) if role=='Walking' else (-.35,-.09,0))*amount,hand_rot=h.to_3x3())
        records.append({n:rig.pose.bones[n].rotation_quaternion.copy() for n in ['B_R_UpperArm','B_R_Forearm','B_R_Hand']})
    for f,row in enumerate(records):
        for n,q in row.items():rig.pose.bones[n].rotation_quaternion=q;rig.pose.bones[n].keyframe_insert('rotation_quaternion',frame=f)
death=bpy.data.actions['Death'];attach(death)
for f,row in enumerate(original):
    for n,q in row.items():rig.pose.bones[n].rotation_quaternion=q;rig.pose.bones[n].keyframe_insert('rotation_quaternion',frame=f)
# The native collapse releases the staff before the hands brace the fall.
sc.frame_set(0);start=rig.pose.bones['Staff'].matrix.copy();target=Vector((0,0,1)).rotation_difference(Vector((1,0,.01)).normalized())
staff_report=[]
g=json.loads((p/'work/grip_pose.json').read_text())
for f in range(61):
    for n,q in g['finger_local'].items():
        b=rig.pose.bones[n];b.rotation_quaternion=Quaternion(q).slerp(Quaternion(),min(f/6,1));b.keyframe_insert('rotation_quaternion',frame=f)
for f in range(61):
    sc.frame_set(f)
    if f<3:
        h=armik.W(rig,'B_R_Hand');ready=rig.data.bones['B_R_Hand'].matrix_local
        # The release starts from the held pose; early fall rotates the body only slightly.
        m=start.copy();t=f/3;m.translation+=Vector((-.04*t,-.06*t,0))
    else:
        t=float(np.clip((f-3)/22,0,1));t=t*t*(3-2*t);m=start.to_quaternion().slerp(target,t).to_matrix().to_4x4();m.translation=(start.translation+Vector((-.04,-.06,0))).lerp(Vector((.05,-1.0,.05)),t)
        m.translation.z+=.12*math.sin(math.pi*t)
    rig.pose.bones['Staff'].matrix=m;bpy.context.view_layer.update();low=coord(staff)[:,2].min();m.translation.z+=max(0,.007-low)
    if f>=25:m.translation.z+=.007-(low+max(0,.007-low))
    rig.pose.bones['Staff'].matrix=m;bpy.context.view_layer.update();rig.pose.bones['Staff'].keyframe_insert('location',frame=f);rig.pose.bones['Staff'].keyframe_insert('rotation_quaternion',frame=f)
    cloth=np.isin(pv,[2,5,12,13,14,15,16]);low=coord(body)[cloth,2].min()
    if low<.006:
        offset=.006-low;raw={b.name:b.matrix.copy() for b in rig.pose.bones if b.name.startswith('Robe_')}
        for n,matrix in raw.items():
            matrix.translation.z+=offset;rig.pose.bones[n].matrix=matrix;bpy.context.view_layer.update();rig.pose.bones[n].keyframe_insert('location',frame=f)
    # After support changes to the hands and torso, ground the actual deformed surface.
    if f>=10:
        staffM=m.copy();low=coord(body)[:,2].min();pb=rig.pose.bones['B_Pelvis'];pm=pb.matrix.copy();pm.translation.z+=.003-low;pb.matrix=pm;bpy.context.view_layer.update();pb.keyframe_insert('location',frame=f)
        rig.pose.bones['Staff'].matrix=staffM;rig.pose.bones['Staff'].keyframe_insert('location',frame=f);rig.pose.bones['Staff'].keyframe_insert('rotation_quaternion',frame=f)
    staff_report.append(float(coord(staff)[:,2].min()))
FA=.6;UA=.5;tree=ast.parse((p/'scripts/twist_bones.py').read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'twist_about','bake_twist'}],type_ignores=[]),'twist_bake','exec'),globals())
for name in ['Walking','Hit','Death']:bake_twist(bpy.data.actions[name])
attach(death);sc.frame_set(60);last={b.name:b.matrix_basis.copy() for b in rig.pose.bones};dead=bpy.data.actions['Dead'];attach(dead)
for f in range(31):
    for n,m in last.items():
        b=rig.pose.bones[n];b.matrix_basis=m;b.keyframe_insert('rotation_quaternion',frame=f)
        if n in ['B_Pelvis','Staff'] or n.startswith('Robe_'):b.keyframe_insert('location',frame=f)
# Quaternion sign continuity is required by component interpolation at exported half frames.
for role in ['Standing','Walking','Attack','Cast','Hit','Death','Dead','Fidget']:
    a=bpy.data.actions[role];attach(a);records=[]
    for f in range(int(a.frame_range[1])+1):
        sc.frame_set(f);records.append({b.name:b.rotation_quaternion.copy() for b in rig.pose.bones})
    previous={}
    for f,row in enumerate(records):
        for n,q in row.items():
            if n in previous and q.dot(previous[n])<0:q=-q
            previous[n]=q;pb=rig.pose.bones[n];pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f)
    for l in a.layers:
        for s in l.strips:
            for bag in s.channelbags:
                for fc in bag.fcurves:
                    for k in fc.keyframe_points:k.interpolation='LINEAR'
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/motion_final.blend'))
(p/'review/final_motion_fit.json').write_text(json.dumps({'shoulder_weights_smoothed_vertices':int((blend>0).sum()),'death_staff_floor_m':staff_report},indent=2)+'\n')
