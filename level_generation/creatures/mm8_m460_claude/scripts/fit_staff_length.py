"""Fit native staff endpoints around the fixed grip, then keep its butt clear through the gait and drop."""
from pathlib import Path
import bpy,json,sys,ast,math,numpy as np
from mathutils import Vector,Quaternion
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'))
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_uvprep.blend'))
original=[v.co.copy() for v in bpy.data.objects['Staff'].data.vertices];source=bpy.data.objects['Rig'].data.bones['Socket_Staff_Head'];socket=(source.head_local.copy(),source.tail_local.copy())
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_uv.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];staff=bpy.data.objects['Staff'];scene=bpy.context.scene
import armik
assert len(original)==len(staff.data.vertices)
for v,co in zip(staff.data.vertices,original):v.co=co
rest=rig.data.bones['Staff'].matrix_local.copy();inv=rest.inverted()
def attach(a):
    rig.animation_data.action=None
    for b in rig.pose.bones:b.matrix_basis.identity()
    rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
def coords(ob):
    ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();v=np.array([q.co[:] for q in me.vertices]);ev.to_mesh_clear();return v
attach(bpy.data.actions['Standing']);scene.frame_set(0);B=coords(body);S=coords(staff);origin=rig.pose.bones['Staff'].matrix.translation.z
body_low,body_high=float(B[:,2].min()),float(B[:,2].max());height=body_high-body_low
target_low=body_low+.001;target_high=body_high-height*2/188
lower=(origin-target_low)/(origin-S[:,2].min());upper=(target_high-origin)/(S[:,2].max()-origin)
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
for v in staff.data.vertices:
    local=inv@v.co;local.z*=upper if local.z>0 else lower;v.co=rest@local
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
b=rig.data.edit_bones['Socket_Staff_Head'];point=inv@socket[0];point.z*=upper;offset=rest@point-socket[0];b.head=socket[0]+offset;b.tail=socket[1]+offset
bpy.ops.object.mode_set(mode='OBJECT')
held_report={}
for role in ['Standing','Walking','Attack','Cast','Hit','Fidget']:
    a=bpy.data.actions[role];attach(a);records=[];raises=[]
    for f in range(int(a.frame_range[1])+1):
        scene.frame_set(f);low=coords(staff)[:,2].min();lift=max(0,.006-low);raises.append(float(lift))
        if lift:
            h=armik.W(rig,'B_R_Hand');elbow=armik.W(rig,'B_R_Forearm').translation;target=h.translation+Vector((0,0,lift));armik.solve(rig,'R',target,pole=elbow,hand_rot=h.to_3x3())
        records.append({n:rig.pose.bones[n].rotation_quaternion.copy() for n in ['B_R_UpperArm','B_R_Forearm','B_R_Hand']})
    for f,row in enumerate(records):
        for n,q in row.items():rig.pose.bones[n].rotation_quaternion=q;rig.pose.bones[n].keyframe_insert('rotation_quaternion',frame=f)
    held_report[role]=max(raises)
death=bpy.data.actions['Death'];attach(death)
for f in range(61):
    scene.frame_set(f);low=coords(staff)[:,2].min();m=rig.pose.bones['Staff'].matrix.copy();m.translation.z+=max(0,.007-low)
    rig.pose.bones['Staff'].matrix=m;rig.pose.bones['Staff'].keyframe_insert('location',frame=f);rig.pose.bones['Staff'].keyframe_insert('rotation_quaternion',frame=f)
FA=.6;UA=.5;tree=ast.parse((p/'scripts/twist_bones.py').read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'twist_about','bake_twist'}],type_ignores=[]),'twist_bake','exec'),globals())
for role in held_report:bake_twist(bpy.data.actions[role])
attach(death);scene.frame_set(60);last=rig.pose.bones['Staff'].matrix_basis.copy();dead=bpy.data.actions['Dead'];attach(dead)
for f in range(31):
    rig.pose.bones['Staff'].matrix_basis=last;rig.pose.bones['Staff'].keyframe_insert('location',frame=f);rig.pose.bones['Staff'].keyframe_insert('rotation_quaternion',frame=f)
for role in [*held_report,'Death','Dead']:
    a=bpy.data.actions[role];attach(a);records=[]
    for f in range(int(a.frame_range[1])+1):
        scene.frame_set(f);records.append({n:rig.pose.bones[n].rotation_quaternion.copy() for n in ['B_R_UpperArm','B_R_Forearm','B_R_Hand','B_R_ForearmTwist','B_R_UpperArmTwist','Staff']})
    previous={}
    for f,row in enumerate(records):
        for n,q in row.items():
            if n in previous and q.dot(previous[n])<0:q=-q
            previous[n]=q;rig.pose.bones[n].rotation_quaternion=q;rig.pose.bones[n].keyframe_insert('rotation_quaternion',frame=f)
    for l in a.layers:
        for s in l.strips:
            for bag in s.channelbags:
                for fc in bag.fcurves:
                    for k in fc.keyframe_points:k.interpolation='LINEAR'
attach(bpy.data.actions['Standing']);scene.frame_set(0);S=coords(staff);assert abs(S[:,2].max()-target_high)<.003 and abs(S[:,2].min()-target_low)<.003
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_uv.blend'))
(p/'review/staff_length_fit.json').write_text(json.dumps({'native_body_height_px':188,'native_staff_height_px':186,'staff_low_m':float(S[:,2].min()),'staff_high_m':float(S[:,2].max()),'body_low_m':body_low,'body_high_m':body_high,'lower_shaft_scale':float(lower),'upper_shaft_scale':float(upper),'held_hand_raise_m':held_report,'reason':'Native finial is two pixels below the scalp and the butt reaches the hem; the grip stays fixed on the shaft, and the hand lifts it with the gait.'},indent=2)+'\n')
