"""Keep the editable attack master in step with the exact GLB timestamp edit."""
from pathlib import Path
import bpy,json,numpy as np
P=Path(__file__).resolve().parents[1];OUT=P/'review/attack_windup'
info=json.loads((OUT/'retime.json').read_text())
cut=info['original_cut_seconds']*30;factor=info['windup_duration_factor'];shift=cut*(1-factor)
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_attack_options.blend'))
a=bpy.data.actions[info['clip']]
maximum=0;count=0
for layer in a.layers:
 for strip in layer.strips:
  for bag in strip.channelbags:
   for curve in bag.fcurves:
    assert all(k.interpolation=='LINEAR' for k in curve.keyframe_points)
    times=np.unique(np.r_[np.linspace(0,a.frame_end,257),cut]);before=[curve.evaluate(float(t)) for t in times]
    boundary=curve.evaluate(cut)
    curve.keyframe_points.insert(cut,boundary,options={'FAST'})
    for key in curve.keyframe_points:
     t=key.co.x;key.co.x=t*factor if t<=cut else t-shift
     key.interpolation='LINEAR'
    curve.update()
    for t,expected in zip(times,before):
     actual=curve.evaluate(float(t*factor if t<=cut else t-shift))
     maximum=max(maximum,abs(actual-expected))
    count+=1
a.frame_end=info['duration']*30
assert maximum<1e-5,maximum
rig=bpy.data.objects['Rig'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
bpy.context.scene.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_attack_windup.blend'))
(OUT/'authoring_check.json').write_text(json.dumps({'fcurves':count,'max_curve_error':maximum,'duration':a.frame_end/30},indent=2)+'\n')
print('RETIME_AUTHORING',count,maximum,flush=True)
