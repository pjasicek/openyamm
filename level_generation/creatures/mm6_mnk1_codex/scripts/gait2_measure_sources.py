"""Measure candidate Mixamo walk/run sources for the gait2 rework: cycle, natural stride (planted ankle speed x cycle),
leg length, stride/leg, hip bob, foot clearance. Usage: -- <fbx> [...]"""
import bpy,sys,math,json
import numpy as np
from pathlib import Path
p=Path(__file__).resolve().parents[1]
files=sys.argv[sys.argv.index('--')+1:];out={}
for fpath in files:
 for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
 for a in list(bpy.data.actions):bpy.data.actions.remove(a)
 bpy.ops.import_scene.fbx(filepath=fpath)
 arm=next(o for o in bpy.data.objects if o.type=='ARMATURE');sc=bpy.context.scene
 bn=lambda s:next(b.name for b in arm.data.bones if b.name.endswith(s))
 J={k:bn(k) for k in ['Hips','LeftUpLeg','LeftLeg','LeftFoot','LeftToeBase','RightUpLeg','RightLeg','RightFoot','RightToeBase']}
 act=arm.animation_data.action;f0,f1=map(int,act.frame_range);fps=sc.render.fps/sc.render.fps_base
 W=lambda n:np.array(arm.matrix_world@arm.pose.bones[n].head,dtype=float)
 rows=[]
 for f in range(f0,f1+1):
  sc.frame_set(f);rows.append({k:W(v) for k,v in J.items()})
 H=np.array([r['Hips'] for r in rows]);T=(f1-f0)/fps
 leg=np.mean([np.linalg.norm(rows[0][s+'UpLeg']-rows[0][s+'Leg'])+np.linalg.norm(rows[0][s+'Leg']-rows[0][s+'Foot']) for s in ['Left','Right']])
 # forward = from heel(ankle) to toe at planted frames, horizontal
 fwd=np.mean([r['LeftToeBase']-r['LeftFoot'] for r in rows],axis=0);fwd[2]=0;fwd/=np.linalg.norm(fwd)
 vs=[];lifts=[]
 for s in ['Left','Right']:
  A=np.array([r[s+'Foot'] for r in rows]);z=A[:,2];low=z<z.min()+.01*leg/0.9
  v=-np.gradient(A@fwd)*fps;vs.append(float(np.median(v[low])));lifts.append(float(z.max()-z.min()))
 stride=float(np.mean(vs))*T
 out[Path(fpath).name]={'cycle_s':float(T),'frames':f1-f0,'leg_m':float(leg),'stride_m':stride,'stride_per_leg':stride/leg,'speed_per_leg':stride/leg/T,
  'hip_height_per_leg':float(H[:,2].mean()/leg),'hip_bob_per_leg':float(np.ptp(H[:,2])/leg),'hip_travel':float(np.ptp(H@fwd)/leg),'ankle_lift_per_leg':[float(x/leg) for x in lifts]}
 print('SRC',Path(fpath).name,json.dumps({k:(round(v,3) if isinstance(v,float) else v) for k,v in out[Path(fpath).name].items()}),flush=True)
(p/'work/gait2_sources.json').write_text(json.dumps(out,indent=1))
