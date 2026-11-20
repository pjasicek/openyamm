"""Fit the brief's floor-reaching arm proportions locally; retain upload coordinates for exact weight transfer."""
import bpy,json,sys,os
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/shortarms_weighted.blend'))
weighted=bpy.data.objects['Body'];names={g.index:g.name for g in weighted.vertex_groups}
arm_weights={s:np.array([sum(g.weight for g in v.groups if names[g.group].startswith('B_'+s+'_') and any(q in names[g.group] for q in ['UpperArm','Forearm','Hand','Finger'])) for v in weighted.data.vertices]) for s in ['L','R']}
bpy.ops.wm.open_mainfile(filepath=str(P/'work/gloamer_clean_v1.blend'))
body=bpy.data.objects['Body'];me=body.data;co=np.array([v.co[:] for v in me.vertices]);original=co.copy()
data=json.loads((P/'work/joints_fit_base.json').read_text());J={k:np.array(v) for k,v in data['joints'].items()}
for s in ['L','R']:
    shoulder,elbow,wrist=[J[s+'_'+n].copy() for n in ['UpperArm','Forearm','Hand']]
    up=elbow-shoulder;fore=wrist-elbow
    u=np.clip((original-shoulder)@up/(up@up),0,1);f=np.clip((original-elbow)@fore/(fore@fore),0,1)
    shift=u[:,None]*up*.10+f[:,None]*fore*1.40
    co+=shift*np.clip(arm_weights[s],0,1)[:,None]
    J[s+'_Forearm']=elbow+up*.10;J[s+'_Hand']=wrist+up*.10+fore*1.40
me.vertices.foreach_set('co',co.ravel());me.update()
assert np.isfinite(co).all() and np.max(np.linalg.norm(co-original,axis=1))<.55
# orig_co stays in the submitted upload frame; Meshy correspondence remains exact.
data['joints']={k:v.tolist() for k,v in J.items()};data['arm_extension']={'upper_arm':1.10,'forearm':2.40,'reason':'Pilot knuckles stopped at the knees; the design requires arms that reach the floor.'}
(P/'work/joints_final.json').write_text(json.dumps(data,indent=2)+'\n')
(P/'review/geometry/arm_proportion_change.json').write_text(json.dumps({'max_vertex_shift_m':float(np.linalg.norm(co-original,axis=1).max()),**data['arm_extension']},indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/gloamer_longarms_v1.blend'))
print('ARM PROPORTIONS',data['arm_extension'],flush=True)
sys.stdout.flush();sys.stderr.flush();os._exit(0)
