"""Keep contact unchanged and fit the return within the native 100-tick recovery."""
from pathlib import Path
import bpy,sys,json
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'))
import action_curves
bpy.ops.wm.open_mainfile(filepath=str(p/'work/full_reduced.blend'))
a=bpy.data.actions['Attack'];assert abs(a.frame_range[1]-64)<.001
curves=action_curves.curves(a);frames=[i*.5 for i in range(99)]
def source(f):
 if f<=29:return f
 u=(f-29)/20;return 29+20*u+15*u*u
values=[[fc.evaluate(source(f)) for f in frames] for fc in curves]
for fc,vs in zip(curves,values):
 fc.keyframe_points.clear()
 for f,v in zip(frames,vs):fc.keyframe_points.insert(f,v,options={'FAST'}).interpolation='LINEAR'
 fc.update()
a.frame_end=49;action_curves.continuous(a)
assert abs(a.frame_range[1]-49)<.001
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/full_reduced.blend'))
(p/'review/attack_timing.json').write_text(json.dumps({'contact_seconds':29/30,'clip_seconds':49/30,'native_action_seconds':1,'native_recovery_seconds':100/60,'runtime_action_seconds':1+(49-29)/30,'retime':'quadratic recovery only; unchanged through contact'},indent=2))
