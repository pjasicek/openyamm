"""Ground the complete corpse with the shared floor solver, keeping the authored maul drop in world space."""
from pathlib import Path
import json,sys
import numpy as np
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'claude_shared/floor'))
from glb_pose import Glb,Model
from floor_fix import ground_death,channel
src,out,report_path=map(Path,sys.argv[1:4]);m=Model(Glb(src));nodes=m.glb.json['nodes'];maul=next(i for i,n in enumerate(nodes) if n.get('name')=='Thunder_Maul');parent=m.parent[maul]
assert [nodes[i]['name'] for i in m.root_joints]==['B_Pelvis']
roles=('Forge_Death','Forge_Dead');saved={}
for clip in roles:
 keys=m.clip_times(clip);times=np.unique(np.r_[keys,np.arange(keys[0],keys[-1],1/120)].astype(np.float32))
 saved[clip]=(times,[m.world(m.sample(clip,float(t)))[maul].copy() for t in times],min(m.lowest(clip,float(t)) for t in times))
ground_death(m,*roles,.001);report={}
for clip,(times,worlds,before) in saved.items():
 values=[]
 for t,target in zip(times,worlds):
  w=m.world(m.sample(clip,float(t)));values.append((np.linalg.inv(w[parent])@target)[:3,3])
 sampler=channel(m,clip,maul,'translation');assert sampler is not None
 sampler['input']=m.glb.append_accessor(times[:,None],'SCALAR');sampler['output']=m.glb.append_accessor(np.array(values),'VEC3');sampler['interpolation']='LINEAR'
 errors=[float(np.max(np.abs(m.world(m.sample(clip,float(t)))[maul]-target))) for t,target in zip(times,worlds)];assert max(errors)<2e-6
 lows=[m.lowest(clip,float(t)) for t in times];assert min(lows)>=-.002,(clip,min(lows))
 report[clip]={'before_floor_min_m':before,'after_floor_min_m':min(lows),'maul_world_matrix_max_error':max(errors),'samples':len(times)}
m.glb.write(out);report_path.write_text(json.dumps(report,indent=2)+'\n');print('FORGE_FLOOR',json.dumps(report),flush=True)
