import bpy,runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/round1_clothed.blend'))
for name in ['Attack','Cast']:
 a=bpy.data.actions[name];end=a.frame_range[1]*1.2
 for lay in a.layers:
  for st in lay.strips:
   for cb in st.channelbags:
    for fc in cb.fcurves:
     for k in fc.keyframe_points:k.co.x*=1.2;k.handle_left.x*=1.2;k.handle_right.x*=1.2
 a.frame_end=end
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round1_clothed.blend'))
sys.argv=['g','--','work/round1_clothed.blend'];runpy.run_path(str(P/'scripts/rig_gates_48.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/round1_precision.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/round1_motion_trace.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/round1_blade_audit.py'),run_name='__main__')
