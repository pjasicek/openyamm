from pathlib import Path
import bpy,json,numpy as np
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/hands.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
names=[g.name for g in body.vertex_groups];masks={s:np.array([sum(g.weight for g in v.groups if names[g.group]==f'B_{s}_Foot')>.5 for v in body.data.vertices]) for s in 'LR'}
report={}
for name in ('Walking','Running'):
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];end=float(a.frame_range[1]);ts=np.linspace(0,end,int(end*4)+1);rows={s:[] for s in 'LR'}
 for f in ts:
  sc.frame_set(int(f),subframe=f%1);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();c=np.array([tuple(body.matrix_world@v.co) for v in me.vertices]);ev.to_mesh_clear()
  for s in 'LR':rows[s].append([c[masks[s],1].mean(),c[masks[s],2].min()])
 vals=[]
 for s in 'LR':
  r=np.array(rows[s]);v=np.diff(r[:,0])/np.diff(ts/30);m=(r[:-1,1]<.025)&(r[1:,1]<.025)&(v>.1);vals.extend(v[m].tolist())
 assert len(vals)>5
 report[name]={'stance_samples':len(vals),'measured_stride_m':float(np.median(vals)*end/30),'backward_speed_mps':float(np.median(vals))}
(P/'review/gait_stride.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
