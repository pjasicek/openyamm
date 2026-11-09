"""Measured boot contact patches on the exported animation, at the viewer's 48 Hz."""
import bpy,sys,json,math,numpy as np,hashlib
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/export_reimport.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];scene=bpy.context.scene;patch={}
rest=np.array([tuple(body.matrix_world@v.co)for v in body.data.vertices])
for sd in 'LR':
 ids=np.where((rest[:,2]<.001)&((rest[:,0]>0)==(sd=='L')))[0];assert len(ids)>12
 y=rest[ids,1];patch[sd]={'all':ids,'heel':ids[y>=np.quantile(y,.7)],'toe':ids[y<=np.quantile(y,.3)]}
report={}
for name in ['Standing','Fidget','Hit','Attack','Walking']:
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];end=float(a.frame_range[1])/scene.render.fps;rows={sd:[]for sd in 'LR'}
 for t in sorted(set([*np.arange(0,end+1e-6,1/48),end])):
  f=t*scene.render.fps;scene.frame_set(int(f),subframe=f%1);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();co=np.array([tuple(body.matrix_world@v.co)for v in m.vertices]);ev.to_mesh_clear()
  for sd,sets in patch.items():
   points=co[sets['all']];_,_,v=np.linalg.svd(points-points.mean(0));normal=v[-1];tilt=math.degrees(math.acos(np.clip(abs(normal[2]),0,1)))
   heel=co[sets['heel'],2];toe=co[sets['toe'],2]
   rows[sd].append({'seconds':float(t),'tilt_deg':tilt,'heel_m':[float(heel.min()),float(heel.max())],'toe_m':[float(toe.min()),float(toe.max())]})
 report[name]={}
 for sd,data in rows.items():
  required=data if name in ['Standing','Fidget','Hit']else [r for r in data if min(r['heel_m']+r['toe_m'])<.008]
  if name=='Attack':required+=[data[0],data[-1]]
  assert required
  ok=all(r['tilt_deg']<3 and min(r['heel_m']+r['toe_m'])>=-.002 and max(r['heel_m']+r['toe_m'])<.01 for r in required)
  report[name][sd]={'sample_hz':48,'samples':len(data),'max_tilt_deg':max(r['tilt_deg']for r in data),
   'heel_height_min_max_m':[min(r['heel_m'][0]for r in data),max(r['heel_m'][1]for r in data)],
   'toe_height_min_max_m':[min(r['toe_m'][0]for r in data),max(r['toe_m'][1]for r in data)],
   'required_samples':len(required),'pass':ok,'trace':data}
  print('SOLE GATE',name,sd,{k:v for k,v in report[name][sd].items()if k!='trace'},flush=True)
h=hashlib.sha256((P/'export/mm6_dwa1.glb').read_bytes()).hexdigest();out={'runtime_sha256':h,'method':'SVD plane of bind-space sole contact vertices below 1 mm; heel/toe outer fore-aft 30 percent patches','clips':report,'pass':all(r['pass']for d in report.values()for r in d.values())}
(P/'review/round2/sole_gate.json').write_text(json.dumps(out,indent=2)+'\n');assert out['pass']
