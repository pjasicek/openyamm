"""Bake the authored role clips and check grounded deformation at every key."""
import bpy,sys,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_uv.blend'))
sys.path.insert(0,str(P/'scripts'));import motion as M
rig=M.rig;sc=bpy.context.scene;sc.render.fps=M.FPS
rig.animation_data_create();report={}
for name,(seconds,loop) in M.CLIPS.items():
    count=round(seconds*M.FPS);poses=[];minz=1;maxz=-1
    rig.animation_data.action=None
    for f in range(count+1):
        M.pose(name,(f%count)/M.FPS if loop else f/M.FPS)
        coords=M.co();low=float(coords[:,2].min());minz=min(minz,low);maxz=max(maxz,float(coords[:,2].max()))
        assert low>=-.004,(name,f,low)
        poses.append({b.name:(b.location.copy(),b.rotation_quaternion.copy(),b.scale.copy()) for b in rig.pose.bones})
    act=bpy.data.actions.new(name);act.use_fake_user=True;act['loop']=loop;rig.animation_data.action=act
    prev={}
    for f,pose in enumerate(poses):
        for bone in rig.pose.bones:
            loc,q,scale=pose[bone.name]
            if bone.name in prev and prev[bone.name].dot(q)<0:q=-q
            prev[bone.name]=q.copy();bone.location=loc;bone.rotation_quaternion=q;bone.scale=scale
            for channel in ['location','rotation_quaternion','scale']:bone.keyframe_insert(channel,frame=f+1)
    for layer in act.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    for key in curve.keyframe_points:key.interpolation='LINEAR'
    report[name]={'duration':count/M.FPS,'keys':count+1,'loop':loop,'min_z':minz,'max_z':maxz}
    print('BAKED',name,report[name],flush=True)
rig.animation_data.action=bpy.data.actions['Standing'];sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/animated.blend'))
(P/'work/animation_info.json').write_text(json.dumps({'fps':M.FPS,'clips':report,'walk_stride_m':.32,'run_stride_m':.43,'impact_seconds':.375},indent=2))
