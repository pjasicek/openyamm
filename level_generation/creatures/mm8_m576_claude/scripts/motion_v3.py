import bpy,sys,math,runpy
from pathlib import Path
from mathutils import Matrix,Vector
P=Path(__file__).resolve().parents[1];W=P/'work';sys.path.insert(0,str(P/'scripts'));import armik
bpy.ops.wm.open_mainfile(filepath=str(W/'gate_repair_carry.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene
for name in ('Standing','Walking','Running','Hit','Fidget','Death'):
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];frames=[i/4 for i in range(round(a.frame_range[1]*4)+1)];rows=[]
 for f in frames:
  sc.frame_set(int(f),subframe=f%1)
  chest=armik.W(rig,'B_Spine2').to_3x3()@rig.data.bones['B_Spine2'].matrix_local.to_3x3().inverted();axis=chest@Vector((0,-1,0));M=armik.W(rig,'B_L_UpperArm');pivot=M.translation.copy();M=Matrix.Rotation(math.radians(15 if name=='Hit' else 6),4,axis)@M;M.translation=pivot;armik.set_world(rig,'B_L_UpperArm',M);rows.append(rig.pose.bones['B_L_UpperArm'].rotation_quaternion.copy())
 for f,q in zip(frames,rows):rig.pose.bones['B_L_UpperArm'].rotation_quaternion=q;rig.pose.bones['B_L_UpperArm'].keyframe_insert('rotation_quaternion',frame=f)
bpy.ops.wm.save_as_mainfile(filepath=str(W/'gate_repair_carry_v3.blend'))
sys.argv=['author_attack.py','--',str(W/'gate_repair_carry_v3.blend'),str(W/'gate_repair_attack.blend')];runpy.run_path(str(P/'scripts/author_attack.py'),run_name='__main__')
