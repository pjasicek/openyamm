from pathlib import Path
import bpy,numpy as np,json
P=Path(__file__).resolve().parents[1];s=bpy.context.scene;s.render.fps=48
bpy.ops.import_scene.gltf(filepath=str(P/'export/mm8_centaur.glb'))
r=next(o for o in bpy.data.objects if o.type=='ARMATURE')
for track in r.animation_data.nla_tracks:track.mute=True
report={}
for name,frames,duty,travel in [('Walking',36,.62,.7),('Running',32,.52,1.15)]:
 a=bpy.data.actions[name];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];hooves={}
 for bone,offset in [('FrontHoof_L',0),('HindHoof_R',0),('FrontHoof_R',.5),('HindHoof_L',.5)]:
  points=[]
  for u in np.linspace(.001,duty-.001,49):
   phase=(u-offset)%1;frame=phase*frames;s.frame_set(int(frame),subframe=float(frame%1));v=r.matrix_world@r.pose.bones[bone].head
   v.y-=u*travel/duty;points.append(list(v))
  points=np.array(points);drift=float(np.linalg.norm(points-points[0],axis=1).max());assert drift<.022,(name,bone,drift);hooves[bone]=drift
 report[name]={'stance_travel_m':travel,'stance_fraction':duty,'binding_travel_per_cycle_m':travel/duty,'compensated_hoof_drift_m':hooves,'samples_per_hoof':49}
(P/'review/stride_calibration.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
