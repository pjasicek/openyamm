from pathlib import Path
import bpy,sys,json,runpy
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/fitted_r2.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene
act=bpy.data.actions['Harrower_Death'];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];sc.frame_set(int(act.frame_range[1]))
end={b.name:(b.location.copy(),b.rotation_quaternion.copy(),b.scale.copy()) for b in rig.pose.bones if b.name.startswith(('Cloth_','Mantle_'))}
act=bpy.data.actions['Harrower_Dead'];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
for f in (0,30):
 for name,(loc,q,scale) in end.items():
  b=rig.pose.bones[name];b.location=loc;b.rotation_quaternion=q;b.scale=scale
  for prop in ('location','rotation_quaternion','scale'):b.keyframe_insert(prop,frame=f)
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
for side in 'LR':
 for name,count in (('forearm',3),('shin',2)):bpy.data.objects[f'Arm_{name}_{side}']['segment_count']=count
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/final_r2.blend'))
clips=[a.name for a in bpy.data.actions if a.name.startswith('Harrower_')]
for script,args in [('grip_gate_r2.py',[str(P/'work/final_r2.blend')]),('audit_geometry.py',[str(P/'work/final_r2.blend'),'r2','.25']),('armour_gate.py',[str(P/'work/final_r2.blend'),'r2',str(P/'scripts/armour_harrower.json'),*clips]),('shell_leak.py',[str(P/'work/final_r2.blend'),str(P/'scripts/armour_harrower.json'),'r2',*clips])]:
 print('AUDIT',script,flush=True);sys.argv=[script,'--',*args];runpy.run_path(str(P/'scripts'/script),run_name='__main__')
