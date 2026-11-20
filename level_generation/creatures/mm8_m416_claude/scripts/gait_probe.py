from pathlib import Path
import bpy,numpy as np,json
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/ready_final.blend'));r=bpy.data.objects['Rig'];o=bpy.data.objects['Body'];a=bpy.data.actions['Running'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];names=[g.name for g in o.vertex_groups];feet={s:np.array([sum(g.weight for g in v.groups if names[g.group] in [f'B_{s}_Foot',f'B_{s}_Toe0'])>.5 for v in o.data.vertices]) for s in 'LR'};rows=[]
for f in np.arange(0,float(a.frame_range[1])+.001,.25):
 bpy.context.scene.frame_set(int(f),subframe=float(f%1));ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();co=np.array([v.co[:] for v in me.vertices]);ev.to_mesh_clear();rows.append([f,*[x for s in 'LR' for x in (co[feet[s],2].min(),r.pose.bones[f'B_{s}_Foot'].head.y)]])
rows=np.array(rows);out={}
for height in [.04,.08,.12,.16]:
 vs=[]
 for x,y in zip(rows[:-1],rows[1:]):
  for z,k in [(1,2),(3,4)]:
   v=(y[k]-x[k])*120
   if max(x[z],y[z])<height and v>0:vs.append(v)
 out[str(height)]={'samples':len(vs),'stride':float(np.median(vs)*a.frame_range[1]/30)}
out['foot_y_range']={s:float(np.ptp(rows[:,k])) for s,k in [('L',2),('R',4)]};(P/'work/gait_probe.json').write_text(json.dumps(out,indent=2));print('GAIT',out)
