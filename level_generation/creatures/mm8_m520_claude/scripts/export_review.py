"""Selected weighted geometry, portable export and native scale/stride measurements."""
from pathlib import Path
import bpy,runpy,sys,json,numpy as np
p=Path(__file__).resolve().parents[1]
for name in ['fit_shoulder_weights.py','export_runtime.py']:
 s=p/'scripts'/name;sys.argv=[str(s)];runpy.run_path(str(s),run_name='__main__')
bpy.ops.wm.open_mainfile(filepath=str(p/'export/mm8_m520.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Cyclops'];scene=bpy.context.scene
ids=[v.index for v in body.data.vertices if not any(body.vertex_groups[g.group].name=='Boulder' and g.weight>.5 for g in v.groups)]
feet={s:[v.index for v in body.data.vertices if any(body.vertex_groups[g.group].name==f'B_{s}_Foot' and g.weight>.5 for g in v.groups)] for s in 'LR'}
report={}
for name in ['Standing','Walking','Running']:
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];rows=[]
 for f in range(int(a.frame_range[1])+1):
  scene.frame_set(f);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();co=np.array([v.co[:] for v in m.vertices]);ev.to_mesh_clear()
  row={s:{'low':float(co[feet[s],2].min()),'y':float(rig.pose.bones[f'B_{s}_Foot'].matrix.translation.y)} for s in 'LR'};rows.append(row)
  if name=='Standing' and f==0:report['standing_bounds']={'low':co[ids].min(0).tolist(),'high':co[ids].max(0).tolist(),'height':float(np.ptp(co[ids,2]))}
 if name!='Standing':
  speed=[]
  for x,y in zip(rows[:-1],rows[1:]):
   for side in 'LR':
    if x[side]['low']<.018 and y[side]['low']<.018:
     v=(y[side]['y']-x[side]['y'])*scene.render.fps
     if v>.05:speed.append(v)
  assert speed,name;report[name]={'stance_speed':float(np.median(speed)),'stride':float(np.median(speed)*a.frame_range[1]/scene.render.fps),'samples':len(speed)}
inventory=json.loads((p/'native/inventory.json').read_text());tiers={}
for key,b in inventory['bindings'].items():
 f=b['actions']['standing']['views']['0'][0];box=inventory['sources'][f['frame']]['native_bbox'];height=box[3]-box[1];scale=height*f['scale']/report['standing_bounds']['height'];tiers[b['label']]={'sprite_pixels':height,'native_scale':f['scale'],'model_scale':scale}
report['tiers']=tiers;(p/'work/runtime_calibration.json').write_text(json.dumps(report,indent=2));print('CALIBRATION',report,flush=True)
