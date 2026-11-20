"""Retain the upright carry through the short recoil, with the arm fitted to the moving shoulder."""
import bpy,sys,math,json,ast,numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import armik
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_uv.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene
names=['B_R_Clavicle','B_R_UpperArm','B_R_Forearm','B_R_Hand']
def attach(a):
 rig.animation_data.action=None
 for pb in rig.pose.bones:pb.matrix_basis.identity()
 rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
attach(bpy.data.actions['Standing']);sc.frame_set(0);ready={n:rig.pose.bones[n].rotation_quaternion.copy() for n in names};hand=armik.W(rig,'B_R_Hand').copy()
a=bpy.data.actions['Hit'];attach(a);records=[]
for f in range(19):
 sc.frame_set(f)
 for n,q in ready.items():rig.pose.bones[n].rotation_quaternion=q
 bpy.context.view_layer.update();elbow=armik.W(rig,'B_R_Forearm').translation.copy();pulse=math.sin(math.pi*f/18)**2
 target=hand.translation+Vector((-.035*pulse,.045*pulse,.045*pulse))
 armik.solve(rig,'R',target,pole=elbow,hand_rot=hand.to_3x3())
 records.append({n:rig.pose.bones[n].rotation_quaternion.copy() for n in names})
previous={}
for f,row in enumerate(records):
 for n,q in row.items():
  if n in previous and q.dot(previous[n])<0:q=-q
  previous[n]=q;pb=rig.pose.bones[n];pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f)
FA=.6;UA=.5;tree=ast.parse((p/'scripts/twist_bones.py').read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'twist_about','bake_twist'}],type_ignores=[]),'twist_bake','exec'),globals());bake_twist(a)
for l in a.layers:
 for strip in l.strips:
  for bag in strip.channelbags:
   for fc in bag.fcurves:
    for key in fc.keyframe_points:key.interpolation='LINEAR'
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_uv.blend'))
