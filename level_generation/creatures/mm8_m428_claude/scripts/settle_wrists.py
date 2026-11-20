"""Reduce excess source hand roll while retaining wrist swing and finger poses."""
import bpy,sys,math
from pathlib import Path
from mathutils import Vector,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import armik
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_timed.blend'))
rig=bpy.data.objects['Rig']
def smooth(x):
    x=max(0,min(1,x));return x*x*(3-2*x)
for a in [a for a in bpy.data.actions if a.use_fake_user and a.name!='GripRef']:
    rig.animation_data.action=a
    if len(a.slots):rig.animation_data.action_slot=a.slots[0]
    N=int(a.frame_range[1]);keys=[]
    for f in range(N+1):
        bpy.context.scene.frame_set(f);pose={}
        for sd in 'LR':
            name=f'B_{sd}_Hand';q=rig.pose.bones[name].rotation_quaternion.copy();sw,tw=armik.split_swing_twist(q,Vector((0,1,0)))
            offset=-25 if sd=='L' else (25*smooth(f/6)*(smooth((N-f)/6) if a.name=='Hit' else 1) if a.name in ('Hit','Death') else 0)
            # (the male's Running kept the source arm with a 100 deg roll; m428 carries the dagger in Running too)
            pose[name]=sw@Quaternion((0,1,0),tw+math.radians(offset))
        keys.append(pose)
    for f,pose in enumerate(keys):
        for name,q in pose.items():
            b=rig.pose.bones[name];b.rotation_quaternion=q;b.keyframe_insert('rotation_quaternion',frame=f)
rig.animation_data.action=None
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_wrists.blend'))
