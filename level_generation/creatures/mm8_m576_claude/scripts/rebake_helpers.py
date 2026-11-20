import bpy,sys,runpy,math,numpy as np
from mathutils import Vector,Quaternion,Matrix
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/master_textured_uv.blend'));rig=bpy.data.objects['Rig'];FA=.6;UA=.5
source=(P/'scripts/twist_bones.py').read_text();exec(source[source.index('def twist_about('):source.index("for act in [a for a in bpy.data.actions if a.use_fake_user]:")])
for a in bpy.data.actions:
 if a.name in ('Standing','Walking','Running','Hit','Fidget','Death','Attack'):bake_twist(a)
for a in bpy.data.actions:
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for curve in bag.fcurves:
     for key in curve.keyframe_points:key.interpolation='LINEAR'
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/master_textured_uv.blend'))
sys.argv=['export_runtime.py'];runpy.run_path(str(P/'scripts/export_runtime.py'),run_name='__main__')
