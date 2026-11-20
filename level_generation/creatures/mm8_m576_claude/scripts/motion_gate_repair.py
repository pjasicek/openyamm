import bpy,sys,runpy,math,json
from pathlib import Path
from mathutils import Matrix
P=Path(__file__).resolve().parents[1];W=P/'work';sys.path.insert(0,str(P/'scripts'));import armik
bpy.ops.wm.open_mainfile(filepath=str(W/'master_textured_uv.blend'));bpy.ops.wm.save_as_mainfile(filepath=str(W/'master_before_gate_repair.blend'))
rig=bpy.data.objects['Rig'];sc=bpy.context.scene
a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];sc.frame_set(0)
held=('B_L_Clavicle','B_L_UpperArm','B_L_Forearm','B_L_Hand','B_L_UpperArmTwist','B_L_ForearmTwist','Pauldron_L')
carry={n:rig.pose.bones[n].rotation_quaternion.copy() for n in held}
for name in ('Walking','Running','Hit','Fidget','Death'):
 a=bpy.data.actions[name]
 for layer in a.layers:
  for strip in layer.strips:
   for cb in strip.channelbags:
    for fc in cb.fcurves:
     if fc.data_path.endswith('rotation_quaternion'):
      for n,q in carry.items():
       if fc.data_path==f'pose.bones["{n}"].rotation_quaternion':
        for k in fc.keyframe_points:k.co.y=q[fc.array_index]
        fc.update()
# Native hit duration is 0.625s: retain the full flinch while easing its transition rates.
a=bpy.data.actions['Hit']
for layer in a.layers:
 for strip in layer.strips:
  for cb in strip.channelbags:
   for fc in cb.fcurves:
    for k in fc.keyframe_points:k.co.x*=1.25;k.handle_left.x*=1.25;k.handle_right.x*=1.25
    fc.update()
a.frame_end*=1.25
# Keep the open hand clear of the outer thigh without changing the source gesture.
for a in bpy.data.actions:
 rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];rows=[]
 end=float(a.frame_range[1]);frames=[i/4 for i in range(round(end*4)+1)]
 for f in frames:
  sc.frame_set(int(f),subframe=f%1);M=armik.W(rig,'B_R_UpperArm');origin=M.translation.copy();M=Matrix.Rotation(math.radians(5),4,'Y')@M;M.translation=origin;armik.set_world(rig,'B_R_UpperArm',M);rows.append(rig.pose.bones['B_R_UpperArm'].rotation_quaternion.copy())
 for f,q in zip(frames,rows):rig.pose.bones['B_R_UpperArm'].rotation_quaternion=q;rig.pose.bones['B_R_UpperArm'].keyframe_insert('rotation_quaternion',frame=f)
with bpy.data.libraries.load(str(W/'sources_level.blend')) as (src,dst):dst.actions=['Stab2']
assert dst.actions[0] is not None
dst.actions[0].use_fake_user=True
bpy.ops.wm.save_as_mainfile(filepath=str(W/'gate_repair_carry.blend'))
sys.argv=['author_attack.py','--',str(W/'gate_repair_carry.blend'),str(W/'gate_repair_attack.blend')];runpy.run_path(str(P/'scripts/author_attack.py'),run_name='__main__')
