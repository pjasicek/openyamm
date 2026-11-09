import bpy,sys,runpy,math,numpy as np
from mathutils import Vector,Matrix
from pathlib import Path
P=Path(__file__).resolve().parents[1];W=P/'work';sys.path.insert(0,str(P/'scripts'));import armik

def run(n,*a):
 sys.argv=[n,'--',*map(str,a)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
# Regenerate the original fidget blend, preserving all other accepted motion and frozen UV-upload geometry.
run('clip_timing.py')
run('sync_actions.py',W/'rig_v6t.blend',W/'master_uv_upload.blend','Fidget')
run('author_carry.py',W/'master_uv_upload.blend',W/'motion_carry_fixed.blend','Fidget:0.12')
bpy.ops.wm.open_mainfile(filepath=str(W/'motion_carry_fixed.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene
act=bpy.data.actions['Fidget'];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];rows=[]
for f in np.arange(0,18.001,.25):
 sc.frame_set(int(f),subframe=float(f%1));before=armik.W(rig,'B_L_Hand');target=before.translation.copy()
 u=math.sin(math.pi*f/18);target.x+=max(0,.29-target.x)*u;target.y-=max(0,target.y+.20)*u
 armik.solve(rig,'L',target,hand_rot=before.to_3x3().normalized())
 rows.append((float(f),{n:rig.pose.bones[n].rotation_quaternion.copy() for n in ['B_L_UpperArm','B_L_Forearm','B_L_Hand']}))
for f,snap in rows:
 for n,q in snap.items():b=rig.pose.bones[n];b.rotation_quaternion=q;b.keyframe_insert('rotation_quaternion',frame=f)
rig.animation_data.action=None;bpy.ops.wm.save_as_mainfile(filepath=str(W/'motion_carry_fixed.blend'))
run('head_contacts.py')
bpy.ops.wm.open_mainfile(filepath=str(W/'motion_head_fixed.blend'));body=bpy.data.objects['Body'];weights=[[(g.group,g.weight) for g in v.groups] for v in body.data.vertices]
run('twist_bones.py',W/'motion_head_fixed.blend',W/'motion_twist_fixed.blend');body=bpy.data.objects['Body']
for v,row in zip(body.data.vertices,weights):
 for g in list(v.groups):body.vertex_groups[g.group].remove([v.index])
 for i,w in row:body.vertex_groups[i].add([v.index],w,'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=str(W/'rig_v6t.blend'))
run('finish_motion.py')
bpy.ops.wm.open_mainfile(filepath=str(W/'motion_grounded.blend'));bpy.ops.wm.save_as_mainfile(filepath=str(W/'master_motion.blend'))
run('g6_contacts.py',W/'master_motion.blend','Running','Fidget','Death')
run('g6_head_clearance.py',W/'master_motion.blend','Fidget','Death')
for view in ('front','left'):run('clip_sheet.py',W/'master_motion.blend',P/f'review/final_contacts_{view}',view,7,'Running','Fidget','Death')
