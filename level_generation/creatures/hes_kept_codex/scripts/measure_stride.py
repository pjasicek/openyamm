"""Measure planted-foot stride on the retained source-rate clips."""
import bpy,os,sys,json
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1];kind=os.environ['KEPT_BODY'];bpy.ops.wm.open_mainfile(filepath=str(P/'work'/kind/'rig_final_done.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene;report={}
for name in ('Kept_Walking','Kept_Running'):
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];f0,f1=a.frame_range;pts={s:[] for s in 'LR'}
 for f in np.arange(f0,f1+.001,.25):
  sc.frame_set(int(f),subframe=float(f%1))
  for s in 'LR':pts[s].append(np.array((rig.matrix_world@rig.pose.bones[f'B_{s}_Foot'].matrix).translation))
 T=(f1-f0)/30;vs=[]
 for s in 'LR':
  x=np.array(pts[s]);low=x[:,2]<x[:,2].min()+.01;vy=np.gradient(x[:,1])*120;vs.append(float(np.median(vy[low])))
 report[name]={'cycle_seconds':T,'planted_speed_m_s':vs,'stride_m':abs(float(np.mean(vs))*T)}
(P/'review'/kind/'stride.json').write_text(json.dumps(report,indent=2)+'\n');print('STRIDE',report,flush=True)
sys.stdout.flush();sys.stderr.flush();os._exit(0)
