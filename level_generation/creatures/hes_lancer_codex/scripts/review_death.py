"""Give the released hands clearance from the longer thigh plates without changing the fall or head motion."""
import bpy,sys
from mathutils import Vector
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import armik
bpy.ops.wm.open_mainfile(filepath=str(P/'work/review_before_20261023/lancer_complete.blend'))
r=bpy.data.objects['Rig'];r.animation_data_create();a=bpy.data.actions['Carbine_Death'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
names=[f'B_{s}_{part}' for s in 'LR' for part in ('UpperArm','Forearm','Hand')]
original=[]
for f in range(int(a.frame_range[1])+1):
    bpy.context.scene.frame_set(f);original.append({n:r.pose.bones[n].matrix_basis.copy() for n in names})
bpy.ops.wm.open_mainfile(filepath=str(P/'work/lancer_review2.blend'))
r=bpy.data.objects['Rig'];r.animation_data_create();a=bpy.data.actions['Carbine_Death'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
keys=[]
for f,pose in enumerate(original):
    bpy.context.scene.frame_set(f)
    for n,m in pose.items():r.pose.bones[n].matrix_basis=m
    bpy.context.view_layer.update()
    amount=min(1,max(0,(40-f)/15));amount=amount*amount*(3-2*amount)
    across=(armik.W(r,'B_L_UpperArm').translation-armik.W(r,'B_R_UpperArm').translation).normalized()
    for side,sign in [('L',1),('R',-1)]:
        hand=armik.W(r,f'B_{side}_Hand');armik.solve(r,side,hand.translation+(across*(sign*.03)+Vector((0,-.07,0)))*amount,hand_rot=hand.to_3x3().normalized())
    keys.append({n:r.pose.bones[n].rotation_quaternion.copy() for n in names})
previous={}
for f,pose in enumerate(keys):
    for n,q in pose.items():
        if n in previous and q.dot(previous[n])<0:q=-q
        previous[n]=q.copy();b=r.pose.bones[n];b.rotation_quaternion=q;b.keyframe_insert('rotation_quaternion',frame=f)
r.animation_data.action=None;bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/lancer_review2.blend'))
