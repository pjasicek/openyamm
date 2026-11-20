import bpy, json, math
from pathlib import Path
from mathutils import Vector, Quaternion, Matrix
import numpy as np
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'master_weights.blend'))
rig=bpy.data.objects['Lizardman_Rig'];body=bpy.data.objects['Lizardman_Body'];sc=bpy.context.scene
for t in rig.animation_data.nla_tracks:t.mute=True

def activate(name,frame):
    a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
    sc.frame_set(int(frame),subframe=float(frame%1))

def snapshot():
    return {b.name:(b.location.copy(),b.rotation_quaternion.copy(),b.scale.copy()) for b in rig.pose.bones}

activate('Standing',0);standing=snapshot()
# The retained face-touch gesture forced a reversed wrist. Keep its hand position with a relaxed wrist,
# and spread the reach evenly across the native half-second instead of snapping into it.
activate('Fidget',9)
rig.animation_data.action=None
hand=rig.pose.bones['RightHand'];hand.rotation_quaternion=Quaternion()
upper=rig.pose.bones['RightArm'];lower=rig.pose.bones['RightForeArm']
shoulder=upper.head.copy();target_hand=Vector((-.08,-.25,1.28));pole=Vector((-.35,-.1,1.05))
a=(rig.data.bones['RightForeArm'].head_local-rig.data.bones['RightArm'].head_local).length
b=(rig.data.bones['RightHand'].head_local-rig.data.bones['RightForeArm'].head_local).length
delta=target_hand-shoulder;distance=delta.length;direction=delta.normalized()
assert abs(a-b)<distance<a+b
axis=pole-shoulder;axis=(axis-direction*axis.dot(direction)).normalized()
along=(a*a-b*b+distance*distance)/(2*distance)
elbow=shoulder+direction*along+axis*math.sqrt(a*a-along*along)
for bone,end in [(upper,elbow),(lower,target_hand)]:
    current=bone.matrix.to_3x3()@Vector((0,1,0));q=current.rotation_difference((end-bone.head).normalized())
    m=bone.matrix.copy();m=Matrix.Translation(m.translation)@q.to_matrix().to_4x4()@Matrix.Translation(-m.translation)@m
    bone.matrix=m;bpy.context.view_layer.update()
hand.rotation_quaternion=Quaternion();bpy.context.view_layer.update()
frames=json.loads((P.parent/'pilot_review_v3/rig_changes.json').read_text())['hand_frames']
axis=hand.matrix.to_3x3()@hand.bone.matrix_local.to_3x3().inverted()@Vector(frames['Right']['axis'])
q=axis.rotation_difference(Vector((0,0,1)));m=hand.matrix.copy()
hand.matrix=Matrix.Translation(m.translation)@q.to_matrix().to_4x4()@Matrix.Translation(-m.translation)@m
bpy.context.view_layer.update()
print('FIDGET WRIST',math.degrees(hand.rotation_quaternion.to_swing_twist('Y')[0].angle),flush=True)
target=snapshot()
for frame in range(25):
    activate('Fidget',frame);weight=math.sin(math.pi*frame/24)**2
    for b in rig.pose.bones:
        sl,sr,ss=standing[b.name];tl,tr,ts=target[b.name]
        b.location=sl.lerp(tl,weight);b.rotation_quaternion=sr.slerp(tr,weight);b.scale=ss.lerp(ts,weight)
        for prop in ['location','rotation_quaternion','scale']:b.keyframe_insert(prop,frame=frame)
for name in ['Hit','Fidget','Death']:
    a=bpy.data.actions[name];end=int(a.frame_range[1]);poses=[]
    for frame in range(end+1):activate(name,frame);poses.append(snapshot())
    rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
    for frame in range(end+1):
        sc.frame_set(frame)
        phase=min(1,frame/3)
        if name!='Death':phase=min(phase,(end-frame)/4)
        phase=phase*phase*(3-2*phase)
        for b in rig.pose.bones:
            loc,rot,scale=poses[frame][b.name]
            sl,sr,ss=standing[b.name]
            b.location=sl.lerp(loc,phase);b.rotation_quaternion=sr.slerp(rot,phase);b.scale=ss.lerp(scale,phase)
        bpy.context.view_layer.update()
        ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
        low=min((ev.matrix_world@v.co).z for v in me.vertices);ev.to_mesh_clear()
        hip=rig.pose.bones['Hips'];m=hip.matrix.copy();m.translation.z-=low;hip.matrix=m
        bpy.context.view_layer.update()
        for b in rig.pose.bones:
            for prop in ['location','rotation_quaternion','scale']:b.keyframe_insert(prop,frame=frame)
# Preserve the imported source's 31/30-second sampled walking cycle, instead of the old native retime.
a=bpy.data.actions['Walk'];factor=(31/30)/.875
for layer in a.layers:
    for strip in layer.strips:
        for bag in strip.channelbags:
            for fc in bag.fcurves:
                for key in fc.keyframe_points:
                    key.co.x*=factor;key.handle_left.x*=factor;key.handle_right.x*=factor
                fc.update()
# Rebuild only the six delivered tracks and make quaternion signs continuous.
for t in list(rig.animation_data.nla_tracks):rig.animation_data.nla_tracks.remove(t)
for name in ['Standing','Walk','Hit','Fidget','Death','Corpse']:
    action=bpy.data.actions[name]
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for b in rig.pose.bones:
                    curves=[bag.fcurves.find('pose.bones['+json.dumps(b.name)+'].rotation_quaternion',index=i) for i in range(4)]
                    if any(c is None for c in curves):continue
                    prev=None
                    for k in range(len(curves[0].keyframe_points)):
                        q=[c.keyframe_points[k].co.y for c in curves]
                        if prev is not None and sum(x*y for x,y in zip(prev,q))<0:
                            for c in curves:c.keyframe_points[k].co.y*=-1
                            q=[-x for x in q]
                        prev=q
    track=rig.animation_data.nla_tracks.new();track.name=name
    strip=track.strips.new(name,0,action);strip.action_slot=action.slots[0];track.mute=True
# Re-evaluate each authored pose before correcting its root; defer writes so sampling cannot feed back.
for name in ['Standing','Walk','Hit','Fidget','Death']:
    action=bpy.data.actions[name];end=float(action.frame_range[1]);roots=[]
    for frame in np.linspace(0,end,int(math.ceil(end*4))+1):
        activate(name,float(frame))
        ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
        low=min((ev.matrix_world@v.co).z for v in me.vertices);ev.to_mesh_clear()
        hip=rig.pose.bones['Hips'];m=hip.matrix.copy()
        m.translation.z-=min(low,0) if name=='Walk' else low
        hip.matrix=m;roots.append((float(frame),hip.location.copy()))
    for frame,location in roots:
        hip.location=location;hip.keyframe_insert('location',frame=frame)
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for fc in bag.fcurves:
                    if fc.data_path=='pose.bones["Hips"].location':
                        for key in fc.keyframe_points:key.interpolation='LINEAR'
activate('Death',36);dead=snapshot()
corpse=bpy.data.actions['Corpse'];rig.animation_data.action=corpse;rig.animation_data.action_slot=corpse.slots[0]
for frame in [0,6]:
    for b in rig.pose.bones:
        b.location,b.rotation_quaternion,b.scale=dead[b.name]
        for prop in ['location','rotation_quaternion','scale']:b.keyframe_insert(prop,frame=frame)
activate('Standing',0)
ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
height=max((ev.matrix_world@v.co).z for v in me.vertices);ev.to_mesh_clear()
feet=[]
for frame in np.linspace(0,49.6,101):
    activate('Walk',float(frame));feet.append([rig.pose.bones[n].head[:] for n in ['LeftFoot','RightFoot']])
feet=np.array(feet);dt=(31/30)/100;speed=[]
for side in range(2):
    z=feet[:,side,2];dy=np.diff(feet[:,side,1]);mask=z[:-1]<np.quantile(z,.45)
    speed.extend(abs(dy[mask]/dt))
stride=float(np.median(speed)*(31/30))
assert .3<stride<2.5,(height,stride)
report={'standing_height_m':height,'native_standing_height_px':196,'scale':196/height,
        'walking_source_duration_seconds':31/30,'stride_length':stride,
        'clips':{n:float(bpy.data.actions[n].frame_range[1]/48) for n in ['Standing','Walk','Hit','Fidget','Death','Corpse']}}
(P/'calibration.json').write_text(json.dumps(report,indent=2)+'\n')
activate('Standing',0)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'master_motion.blend'))
print('CALIBRATION',json.dumps(report),flush=True)
