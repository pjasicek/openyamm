import bpy,sys,json,runpy,os,subprocess
from pathlib import Path
from mathutils import Quaternion,Vector
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;os.environ['PYTHONDONTWRITEBYTECODE']='1';grip=json.loads((P/'work/grip_final.json').read_text());sel=json.loads((P/'review/reduction_soft/selection.json').read_text())
for path in [P/'work/rig_polished.blend']+[P/row['blend']for row in sel.values()]:
 bpy.ops.wm.open_mainfile(filepath=str(path));r=bpy.data.objects['Rig'];a=bpy.data.actions['Attack'];end=float(a.frame_range[1]);r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in list(bag.fcurves):
     if fc.data_path.startswith('pose.bones["B_R_Finger')and any(fc.data_path.endswith(x)for x in ['rotation_quaternion','location']):bag.fcurves.remove(fc)
 for f in [0,end]:
  for name,q in grip['finger_local'].items():
   pb=r.pose.bones[name];pb.rotation_quaternion=Quaternion(q);pb.location=Vector(grip['finger_locations'][name]);pb.keyframe_insert('rotation_quaternion',frame=f);pb.keyframe_insert('location',frame=f)
 a.use_fake_user=True;r.animation_data.action=bpy.data.actions['Standing'];r.animation_data.action_slot=r.animation_data.action.slots[0];bpy.context.scene.frame_set(0);bpy.ops.wm.save_as_mainfile(filepath=str(path))
runpy.run_path(str(P/'scripts/export_levels.py'),run_name='__main__')
for name in ['pack_runtime','prepare_review','audit_runtime']:subprocess.run(['/usr/bin/python3',str(P/'scripts'/f'{name}.py')],check=True)
runpy.run_path(str(P/'scripts/final_checks.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/final_hands.py'),run_name='__main__')
