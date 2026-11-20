"""Retain the source strike and make only the measured jaw/low-recovery clearance corrections."""
import bpy,sys,json,math
from pathlib import Path
from mathutils import Vector,Matrix
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import armik
bpy.ops.wm.open_mainfile(filepath=str(p/'work/pilot_carried.blend'))
rig=bpy.data.objects['Rig'];sc=bpy.context.scene;a=bpy.data.actions['Attack'];frames=[]
def action(a):
 rig.animation_data.action=a
 if a is not None:rig.animation_data.action_slot=a.slots[0]
for f in range(int(a.frame_range[1])+1):
 action(a);sc.frame_set(f);snap={b.name:b.matrix_basis.copy() for b in rig.pose.bones};action(None)
 for n,m in snap.items():rig.pose.bones[n].matrix_basis=m
 bpy.context.view_layer.update();H=armik.W(rig,'B_R_Hand');target=H.translation.copy();w=math.exp(-.5*((f-38)/6)**2);target+=Vector((-.08,-.06,.06))*w
 armik.solve(rig,'R',target,hand_rot=H.to_3x3())
 H=armik.W(rig,'B_Head');angle=-math.radians(9)*math.exp(-.5*((f-7)/6)**2)
 armik.set_world(rig,'B_Head',armik.rot_world(H,Matrix.Rotation(angle,3,'X')@H.to_3x3()))
 frames.append({b.name:b.matrix_basis.copy() for b in rig.pose.bones})
action(a)
for f,snap in enumerate(frames):
 for n,m in snap.items():
  b=rig.pose.bones[n];b.matrix_basis=m;b.keyframe_insert('rotation_quaternion',frame=f)
action(None);bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/pilot_carried.blend'))
