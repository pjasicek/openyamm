import bpy,sys,runpy,math,numpy as np
from mathutils import Matrix
from pathlib import Path
P=Path(__file__).resolve().parents[1];W=P/'work';sys.path.insert(0,str(P/'scripts'))
def run(n,*a):
 sys.argv=[n,'--',*map(str,a)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
# Work before reduction so all geometry and UV correspondence remain replayable.
run('author_carry.py',W/'rig_v6t.blend',W/'motion_carry_fixed.blend','Running:0.15')
bpy.ops.wm.open_mainfile(filepath=str(W/'motion_carry_fixed.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene
act=bpy.data.actions['Fidget'];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];rows=[]
for f in np.arange(0,14.001,.25):
 sc.frame_set(int(f),subframe=float(f%1));ch=rig.pose.bones['B_Spine2'];axis=(ch.matrix.to_3x3()@ch.bone.matrix_local.to_3x3().inverted()@__import__('mathutils').Vector((0,-1,0))).normalized()
 amount=math.radians(18)*math.sin(math.pi*f/14)
 snap={}
 for side,sign in [('R',-1),('L',1)]:
  b=rig.pose.bones[f'B_{side}_UpperArm'];m=b.matrix.copy();pos=m.translation.copy();m=Matrix.Rotation(sign*amount,4,axis)@m;m.translation=pos;b.matrix=m;bpy.context.view_layer.update();snap[b.name]=b.rotation_quaternion.copy()
 rows.append((float(f),snap))
for f,snap in rows:
 for n,q in snap.items():b=rig.pose.bones[n];b.rotation_quaternion=q;b.keyframe_insert('rotation_quaternion',frame=f)
rig.animation_data.action=None;bpy.ops.wm.save_as_mainfile(filepath=str(W/'motion_carry_fixed.blend'))
run('head_contacts.py')
# Bake twist after the arm adjustments, but preserve the already established vertex weights.
bpy.ops.wm.open_mainfile(filepath=str(W/'motion_head_fixed.blend'));body=bpy.data.objects['Body'];weights=[[(g.group,g.weight) for g in v.groups] for v in body.data.vertices]
run('twist_bones.py',W/'motion_head_fixed.blend',W/'motion_twist_fixed.blend')
body=bpy.data.objects['Body']
for v,row in zip(body.data.vertices,weights):
 for g in list(v.groups):body.vertex_groups[g.group].remove([v.index])
 for i,w in row:body.vertex_groups[i].add([v.index],w,'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=str(W/'rig_v6t.blend'))
run('finish_motion.py');run('reduce_rigged.py',W/'motion_grounded.blend',W/'master_rig.blend');run('prepare_uploads.py')
run('g6_contacts.py',W/'master_rig.blend','Running','Fidget','Death')
run('g6_head_clearance.py',W/'master_rig.blend','Fidget','Death')
for view in ('front','left'):run('clip_sheet.py',W/'master_rig.blend',P/f'review/corrected_{view}',view,7,'Running','Fidget','Death')
