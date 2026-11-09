"""Regress the reported early elbow snap using dense actual bone motion, including viewer frames 6–8."""
import bpy,json,math
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];report={}
for revision,file in [('before','work/attack_v4/animations_before.blend'),('after','work/animations.blend'),('export','export/mm6_gar_lod0.glb')]:
 if revision=='export':
  bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(P/file));rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
 else:
  bpy.ops.wm.open_mainfile(filepath=str(P/file));rig=bpy.data.objects['Rig']
 scene=bpy.context.scene;a=next(a for a in bpy.data.actions if a.name=='Attack' or a.name.endswith('|Attack'));rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
 rows=[]
 for i in range(361):
  t=i/240;f=t*scene.render.fps;scene.frame_set(math.floor(f),subframe=f%1);row={'time':t}
  for side in ['R','L']:
   row[side]={part:list(rig.pose.bones[f'B_{side}_{part}'].head) for part in ['UpperArm','Forearm','Hand']}
  rows.append(row)
 changes=[]
 for i in range(1,len(rows)):
  d={'time':rows[i]['time']}
  for side in ['R','L']:
   old,cur=rows[i-1][side],rows[i][side]
   d[side]={part:float(np.linalg.norm(np.array(cur[part])-old[part])*240) for part in ['Forearm','Hand']}
  changes.append(d)
 early=[r for r in changes if r['time']<=.3];frames=[]
 for frame in range(17):
  t=frame/48;cur=rows[frame*5];frames.append({'frame':frame,'time':t,'R':cur['R']})
 report[revision]={'early_peak_elbow_speed_m_s':max(r['R']['Forearm'] for r in early),'early_peak_wrist_speed_m_s':max(r['R']['Hand'] for r in early),'worst_early_elbow':max(early,key=lambda r:r['R']['Forearm']),'frame6_to_8_elbow_travel_m':float(np.linalg.norm(np.array(rows[40]['R']['Forearm'])-rows[30]['R']['Forearm'])),'frames_48fps':frames,'samples':rows}
 print('ELBOW_MOTION',revision,{k:v for k,v in report[revision].items() if k not in ['frames_48fps','samples']},flush=True)
(P/'work/attack_v4/elbow_motion.json').write_text(json.dumps(report,indent=2)+'\n')

assert report['before']['early_peak_elbow_speed_m_s']>10
for revision in ['after','export']:
 assert report[revision]['early_peak_elbow_speed_m_s']<2
 assert report[revision]['frame6_to_8_elbow_travel_m']<.06
