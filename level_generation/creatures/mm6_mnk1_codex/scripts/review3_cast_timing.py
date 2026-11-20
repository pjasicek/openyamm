"""Give the Cast elbow-plane transition two samples without moving its palm release or endpoints."""
import bpy,json,numpy as np
from pathlib import Path
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/animation_finish.blend'));a=bpy.data.actions['Cast']
new=[0,10,10.5,11,12.5,13.5,30];old=[0,10,11.5,12,12.5,13.5,30]
for layer in a.layers:
 for strip in layer.strips:
  for cb in strip.channelbags:
   for fc in cb.fcurves:
    samples=[(float(f),fc.evaluate(float(np.interp(f,new,old)))) for f in np.arange(0,30.01,.5)]
    while len(fc.keyframe_points):fc.keyframe_points.remove(fc.keyframe_points[-1],fast=True)
    fc.keyframe_points.add(len(samples))
    for key,(f,v) in zip(fc.keyframe_points,samples):key.co=(f,v);key.interpolation='LINEAR'
    fc.update()
assert np.interp(13.5,new,old)==13.5 and new[-1]==old[-1]
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/animation_finish.blend'));(p/'work/review3_cast_timing.json').write_text(json.dumps({'new_frames':new,'source_frames':old,'release_s':.45,'duration_s':1},indent=2))
