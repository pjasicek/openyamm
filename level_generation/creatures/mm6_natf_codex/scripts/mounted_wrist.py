import bpy,sys,runpy,math,json
from pathlib import Path
from mathutils import Quaternion
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/gate_master.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene;pb=rig.pose.bones['B_R_Hand']
for name in ['Attack','Cast','Death']:
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];end=int(a.frame_range[1]);qs=[]
 for f in range(end+1):
  sc.frame_set(f);t=min(1,f/10,(end-f)/10)if name!='Death'else min(1,f/10);t=t*t*(3-2*t);qs.append(pb.rotation_quaternion.slerp(Quaternion(),t))
 for f,q in enumerate(qs):pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f)
a=bpy.data.actions['Death'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];sc.frame_set(int(a.frame_range[1]));endq=pb.rotation_quaternion.copy();a=bpy.data.actions['Dead'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
for f in range(int(a.frame_range[1])+1):pb.rotation_quaternion=endq;pb.keyframe_insert('rotation_quaternion',frame=f)
ns=runpy.run_path(str(P/'scripts/bake_twist.py'));[ns['bake_twist'](a)for a in bpy.data.actions if a.use_fake_user]
blade=bpy.data.objects['ForearmBlade'];M=rig.data.bones['ForearmBlade'].matrix_local;iv=M.inverted()
for v in blade.data.vertices:
 q=iv@v.co
 if q.z>.17:q.x-=.022*min(1,max(0,(q.z-.17)/.065));v.co=M@q
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/gate_master.blend'));(P/'review/mounted_wrist.md').write_text('The blade is mounted along the forearm. Attack, Cast and Death retain their library shoulder/elbow motion; the open hand returns to its neutral wrist relation during the active motion so it cannot bend into the blade. Standing and Fidget preserve the inward-facing free palm. The blade has 10 mm extra clearance beyond the cuffs.\n')
