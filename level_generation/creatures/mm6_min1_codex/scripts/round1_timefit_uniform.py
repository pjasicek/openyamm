"""Stretch only the fast elbow transitions, preserving every fitted spatial pose and fixed grip."""
import bpy,runpy,json,math
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];report=[]
for strength in [1.8,2.0,2.2,2.5,2.8,3.2]:
 bpy.ops.wm.open_mainfile(filepath=str(P/'work/round1_lod0.blend'));fps=bpy.context.scene.render.fps
 for role in ['Attack','Cast']:
  a=bpy.data.actions[role];dur=float(a.frame_range[1])/fps;ts=np.linspace(0,dur,int(dur*2400)+1);u=ts.copy()
  if role=='Cast':u=np.where(ts<.8,ts,np.where(ts<=1.2,.8,ts-.4))
  rate=np.full_like(ts,strength)
  if False:pass
  tt=np.r_[0,np.cumsum((rate[:-1]+rate[1:])*.5*np.diff(ts))]
  for layer in a.layers:
   for strip in layer.strips:
    for bag in strip.channelbags:
     for fc in bag.fcurves:
      for k in fc.keyframe_points:
       t=float(np.interp(k.co.x/fps,ts,tt))*fps;k.co.x=t;k.handle_left.x=t;k.handle_right.x=t;k.interpolation='LINEAR'
      fc.update()
  a.frame_end=float(tt[-1]*fps);a.use_frame_range=True
 out=P/'work/round1_timefit.blend';bpy.ops.wm.save_as_mainfile(filepath=str(out));runpy.run_path(str(P/'scripts/round1_acceleration.py'),init_globals={'INPUT':str(out.relative_to(P))});d=json.loads((P/'review/round1/acceleration_gate.json').read_text());report.append({'strength':strength,'pass':d['pass'],'max_deg_s2':max(b['max_deg_s2'] for a in d['clips'].values() for b in a['bones'].values())});print('TIME FIT',report[-1],flush=True)
 if d['pass']:break
else:raise AssertionError('Timing fit did not meet shared acceleration limit')
(P/'review/round1/timing_fit.json').write_text(json.dumps(report,indent=2))
import sys
sys.argv=['g','--','work/round1_timefit.blend'];runpy.run_path(str(P/'scripts/rig_gates_48.py'))
runpy.run_path(str(P/'scripts/round1_precision.py'),init_globals={'INPUT':'work/round1_timefit.blend'})
