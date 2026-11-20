"""Source-calibrated angular-acceleration gate on the final GLB, sampled at 48 Hz."""
import sys,json,math
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation,Slerp
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P.parents[2]/'tools'))
from merge_head_material import read_glb,accessor_array
BONES=[f'B_{side}_{part}'for side in 'LR'for part in ['UpperArm','Forearm','Hand']]
def measure(path,clip):
 d,b=read_glb(path);a=next(a for a in d['animations']if a['name'].split('|')[-1].split('@')[-1]==clip);tracks={}
 duration=0
 for c in a['channels']:
  s=a['samplers'][c['sampler']];t=accessor_array(d,b,s['input']).ravel();duration=max(duration,float(t[-1]))
  if c['target']['path']=='rotation':
   q=accessor_array(d,b,s['output']);tracks[c['target']['node']]=(t,Rotation.from_quat(q))
 parents={ch:i for i,n in enumerate(d['nodes'])for ch in n.get('children',[])};times=np.arange(0,duration+1e-7,1/48);local={}
 for i,n in enumerate(d['nodes']):
  if i in tracks:
   t,q=tracks[i];local[i]=Slerp(t,q)(np.clip(times,t[0],t[-1])) if len(t)>1 else Rotation.from_quat(np.tile(q.as_quat()[0],(len(times),1)))
  else:local[i]=Rotation.from_quat(np.tile(n.get('rotation',[0,0,0,1]),(len(times),1)))
 world={}
 def w(i):
  if i not in world:world[i]=w(parents[i])*local[i]if i in parents else local[i]
  return world[i]
 out={}
 for name in BONES:
  ix=next(i for i,n in enumerate(d['nodes'])if n.get('name')==name);q=w(ix)
  velocity=(q[1:]*q[:-1].inv()).as_rotvec()*180/math.pi*48
  acceleration=np.linalg.norm(np.diff(velocity,axis=0),axis=1)*48
  out[name]={'max_acceleration_deg_s2':float(acceleration.max()),'p99_acceleration_deg_s2':float(np.percentile(acceleration,99)),'worst_time_s':float(times[int(acceleration.argmax())+1]),'max_step_degrees':float(np.linalg.norm(velocity,axis=1).max()/48)}
 return out
library=P.parents[2]/'anim_library/humanoid_set/2Hand Bow.glb'
spec={'Standing':'2HandBowIdle','Walking':'2HandBowWalk','Hit':'2HandBowGetHitF1','Death':'2HandBowDeath1','Fidget':'2HandBowBoost1'}
source={k:measure(library,v)for k,v in spec.items()}
draw=measure(P/'work/source_motion.glb','Draw');release=measure(P/'work/source_motion.glb','Release')
source['Attack']={n:max([draw[n],release[n]],key=lambda v:v['max_acceleration_deg_s2'])for n in BONES};source['Cast']=source['Attack'];source['Dead']=source['Standing']
report={'hz':48,'method':'World-space quaternion log velocities; finite-difference vector acceleration. Limit is source role maximum for the same anatomical segment across both sides plus 10 degrees per sample squared (23040 deg/s2), matching the existing source-relative trace allowance; never a fitted threshold. Report every upper arm, forearm and wrist separately.','clips':{},'failures':[]}
for clip in source:
 row=measure(P/'export/mm6_arc1.glb',clip)
 for name,v in row.items():
  segment=name.split('_')[-1];ref=max(x['max_acceleration_deg_s2']for n,x in source[clip].items()if n.endswith(segment));limit=ref+10*48**2
  v.update(source_max_acceleration_deg_s2=ref,limit_deg_s2=limit,pass_=v['max_acceleration_deg_s2']<=limit and v['max_step_degrees']<90)
  v['pass']=v.pop('pass_')
  if not v['pass']:report['failures'].append([clip,name,v])
 report['clips'][clip]=row
(P/'review/round2/angular_acceleration.json').write_text(json.dumps(report,indent=2));print('ANGULAR_ACCELERATION',report['failures']);assert not report['failures']
