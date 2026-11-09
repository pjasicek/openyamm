import bpy,json,math,numpy as np,sys,runpy
from pathlib import Path
from mathutils import Vector,Quaternion
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round2/master.blend'));r=bpy.data.objects['Rig'];s=bpy.context.scene;a=bpy.data.actions['Death'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];pr=r.data.bones['B_Pelvis'].matrix_local;B=r.data.bones['Club'];axis=(B.tail_local-B.head_local).normalized();design=axis.to_track_quat('Z','Y').to_matrix().to_4x4();design.translation=B.head_local;bd=B.matrix_local.inverted()@design;park=Vector((-.248,.105,.91));qs={}
for f in np.arange(0,float(a.frame_range[1])+.001,.25):
 s.frame_set(int(f),subframe=f%1);t=f/30;w=math.exp(-.5*((t-.32)/.18)**2);direction=Vector((-.16-.60*w,.10,-1)).normalized();M=direction.to_track_quat('Z','Y').to_matrix().to_4x4();M.translation=park;M=r.pose.bones['B_Pelvis'].matrix@pr.inverted()@M;b=r.pose.bones['Club'];b.matrix=M@bd.inverted();b.keyframe_insert('rotation_quaternion',frame=float(f));b.keyframe_insert('location',frame=float(f))
# Final held corpse matches the final club socket.
s.frame_set(int(a.frame_range[1]));q=r.pose.bones['Club'].rotation_quaternion.copy();v=r.pose.bones['Club'].location.copy();a=bpy.data.actions['Dead'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
for f in [0,30]:b=r.pose.bones['Club'];b.rotation_quaternion=q;b.location=v;b.keyframe_insert('rotation_quaternion',frame=f);b.keyframe_insert('location',frame=f)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round2/master.blend'))
runpy.run_path(str(P/'scripts/round2_reduce.py'),run_name='__main__')
