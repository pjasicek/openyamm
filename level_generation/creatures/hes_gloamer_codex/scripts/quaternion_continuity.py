"""Equivalent quaternion signs must interpolate along the short arc between sampled source poses."""
import bpy,sys,os,json
from pathlib import Path
args=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(args[0]));rig=bpy.data.objects['Rig'];report={}
for act in bpy.data.actions:
    if not act.use_fake_user:continue
    rig.animation_data.action=act
    if len(act.slots):rig.animation_data.action_slot=act.slots[0]
    samples=[];prev={};flips=0
    for f in range(int(act.frame_range[0]),int(act.frame_range[1])+1):
        bpy.context.scene.frame_set(f);row={}
        for b in rig.pose.bones:
            q=b.rotation_quaternion.copy()
            if b.name in prev and q.dot(prev[b.name])<0:q.negate();flips+=1
            row[b.name]=q
        samples.append((f,row));prev=row
    for f,row in samples:
        for n,q in row.items():
            b=rig.pose.bones[n];b.rotation_quaternion=q;b.keyframe_insert('rotation_quaternion',frame=f)
    for layer in act.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for fc in bag.fcurves:
                    for key in fc.keyframe_points:key.interpolation='LINEAR'
    report[act.name]=flips
rig.animation_data.action=None
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args[1]))
print('QUATERNION CONTINUITY',json.dumps(report),flush=True)
sys.stdout.flush();sys.stderr.flush();os._exit(0)
