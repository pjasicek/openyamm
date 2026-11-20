"""Measure native-height binding and ground-support travel on the fitted model."""
from pathlib import Path
import bpy,json,numpy as np
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/ready_final.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
vg=[g.name for g in body.vertex_groups];foot={s:np.array([sum(e.weight for e in v.groups if vg[e.group] in (f'B_{s}_Foot',f'B_{s}_Toe0'))>.5 for v in body.data.vertices]) for s in ('L','R')}
def pose(name,f):
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];sc.frame_set(int(f),subframe=f-int(f));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();co=np.array([v.co[:] for v in m.vertices]);ev.to_mesh_clear();return co
co=pose('Standing',0);height=float(co[:,2].max());native_height=195
report={'standing_height_m':height,'native_visible_height_px':native_height,'sprite_scale':1.1999969482421875,'binding_scale':native_height*1.1999969482421875/height,'gaits':{}}
for name in ('Walking','Running'):
 a=bpy.data.actions[name];end=a.frame_range[1];step=.25 if name=='Running' else .5;ts=np.arange(0,end+.001,step);rows=[]
 for f in ts:
  co=pose(name,f);rows.append({s:(float(co[m,2].min()),float(rig.pose.bones[f'B_{s}_Foot'].head.y)) for s,m in foot.items()})
 vel=[]
 for a,b in zip(rows[:-1],rows[1:]):
  for s in foot:
   v=(b[s][1]-a[s][1])*30/step
   if max(a[s][0],b[s][0])<(.08 if name=='Running' else .04) and v>0:vel.append(v)
 assert vel,name
 stride=float(np.median(vel)*end/30);report['gaits'][name]={'support_samples':len(vel),'stride_m':stride,'median_support_velocity_mps':float(np.median(vel))}
(p/'work/runtime_calibration.json').write_text(json.dumps(report,indent=2));print('CALIBRATION',report)
