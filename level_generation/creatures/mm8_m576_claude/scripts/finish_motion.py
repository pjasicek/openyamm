"""Blend native action transitions, restrain corpse travel and settle evaluated surfaces."""
import bpy,sys,math,json
from pathlib import Path
import numpy as np
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parent.parent
src,out=sys.argv[sys.argv.index('--')+1:];bpy.ops.wm.open_mainfile(filepath=src)
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
names=[b.name for b in rig.data.bones]
def set_act(a):
    rig.animation_data_create();rig.animation_data.action=a
    if a is not None and len(a.slots):rig.animation_data.action_slot=a.slots[0]
def sample(a,f):
    set_act(a);sc.frame_set(int(f),subframe=f-int(f));return {n:(rig.pose.bones[n].rotation_quaternion.copy(),rig.pose.bones[n].location.copy()) for n in names}
def smooth(t):t=np.clip(t,0,1);return float(t*t*(3-2*t))
ST=sample(bpy.data.actions['Standing'],0)
report={}
for name in ('Hit','Fidget','Death'):
    a=bpy.data.actions[name];end=int(a.frame_range[1]);poses=[sample(a,f) for f in range(end+1)];set_act(None)
    origin=None
    for f,pose in enumerate(poses):
        w=smooth(f/(3 if name=='Hit' else 7))
        if name!='Death':w*=smooth((end-f)/(4 if name=='Hit' else 8))
        for n,(q,l) in pose.items():
            q0,l0=ST[n]
            if q0.dot(q)<0:q=-q
            pb=rig.pose.bones[n];pb.rotation_quaternion=q0.slerp(q,w);pb.location=l0.lerp(l,w)
        bpy.context.view_layer.update()
        if name=='Death':
            M=rig.matrix_world@rig.pose.bones['B_Pelvis'].matrix
            if origin is None:origin=M.translation.copy()
            t=M.translation.copy();t.x=origin.x+(t.x-origin.x)*.45;t.y=origin.y+(t.y-origin.y)*.45
            M.translation=t;rig.pose.bones['B_Pelvis'].matrix=rig.matrix_world.inverted()@M
        bpy.context.view_layer.update()
        poses[f]={n:(rig.pose.bones[n].rotation_quaternion.copy(),rig.pose.bones[n].location.copy()) for n in names}
    bpy.data.actions.remove(a);a=bpy.data.actions.new(name);a.use_fake_user=True;set_act(a);prev={}
    for f,pose in enumerate(poses):
        for n,(q,l) in pose.items():
            if n in prev and q.dot(prev[n])<0:q=-q
            prev[n]=q;pb=rig.pose.bones[n];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q;pb.location=l;pb.keyframe_insert('rotation_quaternion',frame=f)
            if n=='B_Pelvis':pb.keyframe_insert('location',frame=f)
    a.use_frame_range=True;a.frame_start=0;a.frame_end=end
# Settle feet; corpse uses the whole surface. Running preserves the fitted flight and source timing.
co=np.array([tuple(v.co) for v in body.data.vertices]);piece=np.array([v.value for v in body.data.attributes['piece'].data]);foot=(piece==0)&(co[:,2]<.045)
inv=rig.data.bones['B_Pelvis'].matrix_local.to_3x3().inverted()
for name in ('Standing','Walking','Attack','Hit','Fidget','Death'):
    a=bpy.data.actions[name];set_act(a);rows=[]
    for f in np.arange(0,float(a.frame_range[1])+.001,.5):
        sc.frame_set(int(f),subframe=float(f%1));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
        z=np.array([(body.matrix_world@v.co).z for v in me.vertices]);ev.to_mesh_clear()
        low=float(z.min() if name=='Death' else z[foot].min());rows.append((float(f),rig.pose.bones['B_Pelvis'].location.copy()+inv@Vector((0,0,.001-low))))
    for f,l in rows:pb=rig.pose.bones['B_Pelvis'];pb.location=l;pb.keyframe_insert('location',frame=f)
    report[name]={'duration_seconds':float(a.frame_range[1])/30}
for a in bpy.data.actions:
    for lay in a.layers:
        for st in lay.strips:
            for cb in st.channelbags:
                for fc in cb.fcurves:
                    for k in fc.keyframe_points:k.interpolation='LINEAR'
set_act(None)
(P/'work/clip_timing.json').write_text(json.dumps({'attack_impact_s':1.0,'hit_seconds':.5,'clips':report},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=out)
