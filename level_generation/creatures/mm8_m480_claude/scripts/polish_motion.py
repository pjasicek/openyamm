"""Bake dense floor corrections and retain the source rate in the 60 Hz export master."""
from pathlib import Path
import bpy,json,numpy as np
from mathutils import Vector
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/authored.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];scene=bpy.context.scene
assert scene.render.fps==30,'Rebuild author_motion.py before polishing again'
acts=[a for a in bpy.data.actions if a.use_fake_user]
for act in acts:
    start,end=act.frame_range[:]
    shift=lambda x: (x*21/22 if x<=22 else x-1) if act.name=='Attack' else x
    for layer in act.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for fc in bag.fcurves:
                    for key in fc.keyframe_points:
                        key.co.x=shift(key.co.x)*2;key.handle_left.x=shift(key.handle_left.x)*2;key.handle_right.x=shift(key.handle_right.x)*2;key.interpolation='LINEAR'
                    fc.update()
    act.frame_start=shift(start)*2;act.frame_end=shift(end)*2
scene.render.fps=60;scene.render.fps_base=1
sole=[v.index for v in body.data.vertices if v.co.z<.055 and body.data.attributes['piece'].data[v.index].value==0]
report={}
for act in acts:
    rig.animation_data.action=act
    if len(act.slots):rig.animation_data.action_slot=act.slots[0]
    keys=[];corrections=[]
    for f in range(int(act.frame_range[1])+1):
        scene.frame_set(f)
        ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
        low=min(me.vertices[i].co.z for i in sole)
        if act.name in ('Death','Dead'):low=min(v.co.z for v in me.vertices)
        ev.to_mesh_clear()
        dz=.001-low if act.name not in ('Running','Death','Dead') else max(0,.001-low)
        pb=rig.pose.bones['B_Pelvis'];m=pb.matrix.copy();m.translation.z+=dz;pb.matrix=m
        keys.append(pb.location.copy());corrections.append(dz)
    for f,value in enumerate(keys):
        pb=rig.pose.bones['B_Pelvis'];pb.location=value;pb.keyframe_insert('location',frame=f)
    for layer in act.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for fc in bag.fcurves:
                    for key in fc.keyframe_points:key.interpolation='LINEAR'
    report[act.name]={'fps':60,'duration':act.frame_range[1]/60,'floor_adjustment_m':[min(corrections),max(corrections)]}
# Measure the actual club end rather than using the source hand's speed as impact time.
g=json.loads((p/'work/grip_pose.json').read_text());a=bpy.data.actions['Attack'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
points=[]
for f in range(int(a.frame_range[1])+1):
    scene.frame_set(f);h=rig.pose.bones['B_R_Hand'].matrix;c=h@Vector(g['handle_centre_hand_local']);axis=h.to_3x3()@Vector(g['handle_axis_hand_local']);points.append(tuple(c+axis*.475))
y=np.array(points)[:,1];peak=int(np.argmin(y));start=42
threshold=y[start]+.95*(y[peak]-y[start]);hit=next((i for i in range(start,peak+1) if y[i]<=threshold),peak)
report['Attack']['forward_reach_95_seconds']=hit/60;report['Attack']['maximum_reach_seconds']=peak/60;report['Attack']['tip_at_impact']=points[hit]
(p/'review/timing_and_floor.json').write_text(json.dumps(report,indent=2))
rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=rig.animation_data.action.slots[0];scene.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/authored.blend'))
print('POLISH',json.dumps(report),flush=True)
