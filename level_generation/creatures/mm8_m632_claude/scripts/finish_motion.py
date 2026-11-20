"""Fit a continuous wind-up to the native MM8 event, retaining the recoil and recovery."""
import bpy,json,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/motion_native.blend'))
assert bpy.context.scene.render.fps==60
for a in bpy.data.actions:
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     if a.name=='Attack':
      boundaries=[(f,fc.evaluate(f)) for f in (21,21+16.5/21,37.5)]
      for f,value in boundaries:fc.keyframe_points.insert(f,value,options={'FAST'})
      for k in fc.keyframe_points:
       # Keep the raise; play old viewer frames 44–60 at 2.5x, then shift recovery.
       f=k.co.x
       if f<=21:k.co.x=f*54/21
       elif f<=37.5:k.co.x=54+(f-21)*21/16.5
       else:k.co.x=75+(f-37.5)*.8
       if k.co.x>55:k.co.x=55+(k.co.x-55)/2.5 if k.co.x<=75 else k.co.x-12
     for k in fc.keyframe_points:
      k.co.x*=2;k.interpolation='LINEAR'
     fc.update()
 a.frame_end=(93 if a.name=='Attack' else a.frame_end)*2
 common.action_continuity(a)
bpy.context.scene.render.fps=120
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/motion_timed.blend'))
(P/'work/clip_timing.json').write_text(json.dumps({'fps':120,'durations':{a.name:float(a.frame_range[1]/120) for a in bpy.data.actions},'attack_impact_s':1.05,'native_attack_s':1.25,'attack_followthrough_s':.5,'native_hit_max_s':.625,'note':'Viewer frames 44–60 play at 2.5x, bringing clip release to 1.05 s. The native gameplay event remains 1.25 s; runtime fits the wind-up to it. Recovery remains 0.5 s.'},indent=2))
