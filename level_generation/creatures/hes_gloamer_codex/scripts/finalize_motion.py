"""Preserve source speed, trim the roar's lead/tail, fit the dead hold and animate the elder throat socket."""
import bpy,sys,os,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_contact_uv.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene
names=[b.name for b in rig.pose.bones]
def setact(a):
    rig.animation_data.action=a
    if a is not None and len(a.slots):rig.animation_data.action_slot=a.slots[0]
def sample(a,f):
    setact(a);sc.frame_set(f)
    return {b.name:(b.rotation_quaternion.copy(),b.location.copy()) for b in rig.pose.bones}
def smooth(t):
    t=max(0,min(1,t));return t*t*(3-2*t)
def blend(a,b,w):return {n:(a[n][0].slerp(b[n][0],w),a[n][1].lerp(b[n][1],w)) for n in a}
def write(name,rows):
    old=bpy.data.actions.get(name)
    if old:bpy.data.actions.remove(old)
    a=bpy.data.actions.new(name);a.use_fake_user=True;setact(a);prev={}
    for f,row in enumerate(rows):
        for n,(q,l) in row.items():
            if n in prev and q.dot(prev[n])<0:q.negate()
            prev[n]=q.copy();b=rig.pose.bones[n];b.rotation_quaternion=q;b.location=l;b.keyframe_insert('rotation_quaternion',frame=f)
            if n=='B_Pelvis':b.keyframe_insert('location',frame=f)
    a.use_frame_range=True;a.frame_start=0;a.frame_end=len(rows)-1
    return a
st=sample(bpy.data.actions['Standing'],0);cast=bpy.data.actions['Cast'];oldN=int(cast.frame_range[1]);rows=[];pitch=[]
face=rig.data.bones['B_Head'].matrix_local.to_3x3().inverted()@Vector((0,-1,0))
for f in range(oldN+1):
    rows.append(sample(cast,f));direction=rig.pose.bones['B_Head'].matrix.to_3x3()@face;pitch.append(math.atan2(direction.z,math.hypot(direction.x,direction.y)))
peak=15+int(np.argmax(pitch[15:90]));start=max(0,peak-18);end=min(oldN,peak+70)
selected=[blend(st,rows[start],smooth(i/4)) for i in range(4)]+rows[start:end+1]
for i in range(8):selected[-1-i]=blend(st,selected[-1-i],smooth(i/8))
cast=write('Cast',selected);impact=(peak-start+4)/30
last=sample(bpy.data.actions['Death'],int(bpy.data.actions['Death'].frame_range[1]));write('Dead',[last,last])
# The instantaneous planted-foot backwards speed supplies run stride for the in-place source.
run=bpy.data.actions['Running'];ankles=[];N=int(run.frame_range[1])
for f in range(N+1):
    sample(run,f);ankles.append([list(rig.pose.bones['B_'+s+'_Foot'].head) for s in 'LR'])
ankles=np.array(ankles);vel=np.diff(ankles[:,:,1],axis=0)*30;heights=(ankles[:-1,:,2]+ankles[1:,:,2])/2
plant=heights<np.percentile(heights,40);speeds=vel[plant&(vel>0)]
assert len(speeds)>4
stride=float(np.median(speeds)*N/30);assert .5<stride<4
setact(None)
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
b=rig.data.edit_bones.new('ThroatSac');b.head=(0,-.24,1.13);b.tail=(0,-.24,1.23);b.parent=rig.data.edit_bones['B_Head'];b.use_deform=True
bpy.ops.object.mode_set(mode='OBJECT')
for a in bpy.data.actions:
    if not a.use_fake_user:continue
    setact(a);N=int(a.frame_range[1]);b=rig.pose.bones['ThroatSac']
    for f in range(N+1):
        w=0
        if a.name=='Cast':
            t=f/30;w=smooth(t/max(.1,impact))*(1-smooth((t-impact)/.75))
        b.scale=(1+.30*w,1+.20*w,1+.45*w);b.keyframe_insert('scale',frame=f)
    for layer in a.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for fc in bag.fcurves:
                    for k in fc.keyframe_points:k.interpolation='LINEAR'
report={'cast_source_peak_frame':peak,'cast_source_crop':[start,end],'cast_lead_frames':4,'cast_impact_s':impact,'cast_duration_s':(len(selected)-1)/30,'walking_stride_m':sc['gloamer_walk_stride'],'running_stride_m':stride,'run_stride_samples':len(speeds),'throat_socket_rest':[0,-.24,1.13]}
(P/'review/motion_finalization.json').write_text(json.dumps(report,indent=2)+'\n');print('FINAL MOTION',report,flush=True)
setact(None)
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_final.blend'))
sys.stdout.flush();sys.stderr.flush();os._exit(0)
