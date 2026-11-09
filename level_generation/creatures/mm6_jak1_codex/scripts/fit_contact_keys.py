"""Fit the remaining off-hand contacts without changing the arm or library motion."""
import bpy,json,sys,runpy
from pathlib import Path
from mathutils import Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));fit=json.loads((P/'work/finger_contact_fit.json').read_text())
for file in ['textured_master','production_body','animated_master']:
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/{file}.blend'));rig=bpy.data.objects['Rig'];a=bpy.data.actions['Attack'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];sc=bpy.context.scene;sc.frame_set(0);idle={n:rig.pose.bones[n].rotation_quaternion.copy()for n in fit}
 def smooth(u):u=max(0,min(1,u));return u*u*(3-2*u)
 for f in range(int(a.frame_range[1])+1):
  t=f/sc.render.fps;curl=min(smooth((t/.4-.72)/.28),1-smooth(((t-1.2)/.4)/.28))
  for n,row in fit.items():
   pb=rig.pose.bones[n];pb.rotation_quaternion=idle[n].slerp(Quaternion(row['quaternion']),curl);pb.keyframe_insert('rotation_quaternion',frame=f)
 bpy.ops.wm.save_as_mainfile(filepath=str(P/f'work/{file}.blend'))
runpy.run_path(str(P/'scripts/export_runtime.py'),run_name='__main__')
