"""Dense motion/weight review on the final weighted master, and 48 Hz rotation smoothness."""
from pathlib import Path
import bpy,sys,runpy,json,math
import numpy as np
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import armik
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v6.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
nv=len(body.data.vertices);rest=np.array([v.co[:] for v in body.data.vertices]);edges=np.array([e.vertices[:] for e in body.data.edges]);length=np.linalg.norm(rest[edges[:,0]]-rest[edges[:,1]],axis=1);gn=[g.name for g in body.vertex_groups];weights=np.zeros((nv,len(gn)))
for v in body.data.vertices:
 for g in v.groups:weights[v.index,g.group]=g.weight
assert np.max(abs(weights.sum(1)-1))<.001
regions={}
for label,tokens in [('arms',['UpperArm','Forearm','Hand']),('hands',['Hand','Finger'])]:
 mask=weights[:,[i for i,n in enumerate(gn) if any(k in n for k in tokens)]].sum(1)>.3;regions[label]=(length>1e-5)&mask[edges].all(1)
report={'max_weight_sum_error':float(np.max(abs(weights.sum(1)-1))),'clips':{}}
for role in ['Standing','Walking','Running','Attack','Cast','Hit','Death','Dead','Fidget']:
 a=bpy.data.actions[role];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];out={'wrist_swing_deg':{},'wrist_twist_deg':{},'stretch':{}};feet=[]
 for f in np.arange(0,float(a.frame_range[1])+.001,.5):
  sc.frame_set(int(f),subframe=float(f-int(f)))
  for side in 'LR':
   swing,twist=armik.wrist_cost(rig,side,armik.W(rig,'B_'+side+'_Hand').to_3x3().normalized())
   for name,value in [('wrist_swing_deg',swing),('wrist_twist_deg',abs(twist))]:
    if value>out[name].get(side,{}).get('value',0):out[name][side]={'value':value,'frame':float(f)}
  ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();pos=np.array([v.co[:] for v in me.vertices]);ev.to_mesh_clear();ratio=np.linalg.norm(pos[edges[:,0]]-pos[edges[:,1]],axis=1)/np.maximum(length,1e-8)
  for label,sel in regions.items():
   entry=out['stretch'].setdefault(label,{'p99':0,'max':0});entry['p99']=max(entry['p99'],float(np.percentile(ratio[sel],99)))
   if ratio[sel].max()>entry['max']:entry.update(max=float(ratio[sel].max()),frame=float(f))
  feet.append([list(armik.W(rig,'B_'+s+'_Foot').translation) for s in 'LR'])
 if role in ['Walking','Running']:
  feet=np.array(feet);strides=[]
  for sd in range(2):
   lo=feet[:,sd,2]<feet[:,sd,2].min()+.015;strides.append(float(np.median(np.gradient(feet[:,sd,1],1/60)[lo])*float(a.frame_range[1])/30))
  out['measured_planted_foot_stride_m']=strides
 report['clips'][role]=out;print('MOTION',role,json.dumps(out),flush=True)
(p/'work/motion_audit.json').write_text(json.dumps(report,indent=2))
sys.argv=['jerk_probe.py','--',str(p/'work/rig_v6.blend'),*report['clips']];runpy.run_path(str(p/'scripts/jerk_probe.py'),run_name='__main__')
