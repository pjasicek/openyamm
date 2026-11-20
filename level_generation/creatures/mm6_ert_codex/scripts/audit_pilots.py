"""Dense mesh deformation screen across the pilot clips; exact worst edges identify local repairs."""
import bpy,json,math
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/pilots_v6.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];scene=bpy.context.scene
rest=np.array([v.co[:] for v in body.data.vertices]);edges=np.array([e.vertices[:] for e in body.data.edges]);length=np.linalg.norm(rest[edges[:,0]]-rest[edges[:,1]],axis=1)
assert length.min()>1e-7
regions={}
for sd,sg in [('L',1),('R',-1)]:
 for part,keys in [('arm',['UpperArm','Forearm','Hand']),('hand',['Hand']),('leg',['Thigh','Calf','Foot','Toe0'])]:
  ids={body.vertex_groups[f'B_{sd}_{n}'].index for n in keys};weights=np.array([sum(e.weight for e in v.groups if e.group in ids) for v in body.data.vertices])
  regions[sd+'_'+part]=(weights[edges[:,0]]>.5)&(weights[edges[:,1]]>.5)
regions['body']=np.ones(len(edges),bool)
report={}
for name in ['Walking','Attack']:
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
 peaks={k:{'p99':0.,'max':0.} for k in regions};ground=[];worst=[]
 for t in np.linspace(0,a.frame_range[1]/30,121):
  frame=t*30;scene.frame_set(math.floor(frame),subframe=frame%1);deps=bpy.context.evaluated_depsgraph_get();ev=body.evaluated_get(deps);me=ev.to_mesh()
  co=np.array([v.co[:] for v in me.vertices]);ev.to_mesh_clear();assert np.isfinite(co).all()
  ratio=np.linalg.norm(co[edges[:,0]]-co[edges[:,1]],axis=1)/length
  ground.append(float(co[:,2].min()))
  for key,mask in regions.items():
   r=ratio[mask];peaks[key]['p99']=max(peaks[key]['p99'],float(np.percentile(r,99)))
   if float(r.max())>peaks[key]['max']:
    ix=np.where(mask)[0][np.argmax(r)];peaks[key].update(max=float(r.max()),time=float(t),edge=edges[ix].tolist(),rest_centroid=rest[edges[ix]].mean(0).tolist(),rest_length_m=float(length[ix]),posed_length_m=float(length[ix]*r.max()))
  for pb in rig.pose.bones:assert max(abs(v-1) for v in pb.scale)<1e-4,(name,t,pb.name,tuple(pb.scale))
 for key,row in peaks.items():
  row['weights']=[{body.vertex_groups[e.group].name:round(e.weight,3) for e in body.data.vertices[v].groups if e.weight>.01} for v in row['edge']]
 report[name]={'stretch':peaks,'ground_range':[min(ground),max(ground)]}
 print('AUDIT',name,json.dumps(report[name]))
(P/'work/pilot_deformation_v6.json').write_text(json.dumps(report,indent=2))
