"""Slow the two-frame library recovery turn, preserving the exact collision-free pose path."""
import bpy,json,sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'))
selection=json.loads((P/'review/rebake/final_selection.json').read_text())
for level,item in selection.items():
 path=P/f"work/rebake/{item['tag']}_baked.blend";bpy.ops.wm.open_mainfile(filepath=str(path));rig=bpy.data.objects['Rig'];rig.animation_data.action=None
 for name in ['Attack','Cast']:bpy.data.actions.remove(bpy.data.actions[name])
 with bpy.data.libraries.load(str(P/'work/rebake/near70final_baked.blend'),link=False)as(src,dst):dst.actions=['Attack']
 a=dst.actions[0];a.name='Attack';a.use_fake_user=True
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for curve in bag.fcurves:
     for key in curve.keyframe_points:
      f=key.co.x;key.co.x=f if f<=23 else 23+(f-23)*2 if f<25 else f+2;key.interpolation='LINEAR'
     curve.update()
 a.frame_end=35
 c=a.copy();c.name='Cast';c.use_fake_user=True
 bpy.ops.wm.save_as_mainfile(filepath=str(path))
 if level=='0':bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/master_export.blend'))
runpy.run_path(str(P/'scripts/angular_acceleration.py'),run_name='__main__')
sys.argv=['g6','--',str(P/'work/master_export.blend'),'Attack'];runpy.run_path(str(P/'scripts/g6_contacts.py'),run_name='__main__')
