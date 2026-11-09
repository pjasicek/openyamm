import bpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for name in ['rig','animated']:
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/{name}.blend'))
 rig=bpy.data.objects['Rig'];rig.data.bones['Body'].name='Core'
 for ob in bpy.data.objects:
  if ob.parent==rig and ob.parent_bone=='Body':ob.parent_bone='Core'
 for a in bpy.data.actions:
  for layer in a.layers:
   for strip in layer.strips:
    for bag in strip.channelbags:
     for fc in bag.fcurves:fc.data_path=fc.data_path.replace('pose.bones["Body"]','pose.bones["Core"]')
 bpy.ops.wm.save_as_mainfile(filepath=str(P/f'work/{name}.blend'))
