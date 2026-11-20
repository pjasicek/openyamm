"""Compare final world rotations at 48 Hz with the retargeted source before corrective passes."""
import bpy,sys,os,json,math,hashlib
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1];kind=os.environ['KEPT_BODY'];src=sys.argv[sys.argv.index('--')+1]
BONES=['B_Head','B_Neck','B_Spine2']+[f'B_{s}_{b}' for s in 'LR' for b in ('UpperArm','Forearm','Hand','Foot')]
def measure(path):
 bpy.ops.wm.open_mainfile(filepath=str(path));r=bpy.data.objects['Rig'];sc=bpy.context.scene;out={}
 for a in bpy.data.actions:
  if not a.name.startswith('Kept_'):continue
  r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];qs={n:[]for n in BONES}
  for f in np.arange(0,a.frame_range[1]+1e-6,30/48):
   sc.frame_set(int(f),subframe=float(f%1))
   for n in BONES:qs[n].append((r.matrix_world@r.pose.bones[n].matrix).to_quaternion())
  out[a.name]={}
  for n,Q in qs.items():
   step=np.array([math.degrees(a.rotation_difference(b).angle) for a,b in zip(Q[:-1],Q[1:])]);step=np.minimum(step,360-step)
   out[a.name][n]={'step':float(step.max(initial=0)),'second_difference':float(abs(np.diff(step)).max(initial=0))}
 return out
baseline=measure(P/'work'/kind/'motion_all.blend');final=measure(Path(src).resolve());bad=[]
for name,bones in final.items():
 base=name.replace('Armed','').replace('Kept_Dead','Kept_Death')
 for n,values in bones.items():
  for metric,v in values.items():
   ref=baseline[base][n][metric];limit=max(ref*1.5,ref+8)
   if v>limit:bad.append({'clip':name,'bone':n,'metric':metric,'final':v,'source':ref,'limit':limit})
r={'source_sha256':hashlib.sha256(Path(src).read_bytes()).hexdigest(),'baseline':'motion_all.blend; retargeted selected source before foot/carry/timing/clearance corrections','sample_hz':48,'limit':'max(1.5 x source, source + 8 degrees per sample)','baseline_metrics':baseline,'final_metrics':final,'failures':bad,'pass':not bad}
(P/'review'/kind/'jerk_comparison.json').write_text(json.dumps(r,indent=2)+'\n');print('JERK',kind,'pass',not bad,'failures',bad,flush=True)

sys.stdout.flush();sys.stderr.flush();os._exit(0)
