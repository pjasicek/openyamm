"""Inspect every clip on the evaluated mesh; retain numerical failures for repair."""
import bpy,sys,json,math
import numpy as np
from pathlib import Path
from mathutils import Matrix
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work'/(__import__('os').environ.get('INSPECT_BLEND','rig_final.blend'))))
sc=bpy.context.scene;rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data
rest=np.array([tuple(v.co) for v in me.vertices]);edges=np.array([tuple(e.vertices) for e in me.edges])
length=np.linalg.norm(rest[edges[:,0]]-rest[edges[:,1]],axis=1)
assert np.isfinite(rest).all() and length.min()>1e-7
gn={g.index:g.name for g in body.vertex_groups}
weights=np.array([sum(e.weight for e in v.groups) for v in me.vertices])
assert np.max(abs(weights-1))<.001
regions={}
for label,terms in [('arm',('UpperArm','Forearm','Clavicle')),('hand',('Hand','Finger')),('wing',('Wing_','Feather_'))]:
 w=np.array([sum(e.weight for e in v.groups if any(t in gn[e.group] for t in terms)) for v in me.vertices])
 regions[label]=(w[edges[:,0]]>.3)&(w[edges[:,1]]>.3)
results={}
for a in bpy.data.actions:
 if not a.use_fake_user:continue
 if __import__('os').environ.get('RAVEN_CHECK_CLIP',a.name)!=a.name:continue
 rig.animation_data_create();rig.animation_data.action=a
 if len(a.slots):rig.animation_data.action_slot=a.slots[0]
 samples=[];worlds=[]
 for f in np.arange(0,a.frame_range[1]+.01,.5):
  sc.frame_set(int(f),subframe=float(f-int(f)))
  ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh()
  co=np.array([tuple(v.co) for v in m.vertices]);ev.to_mesh_clear()
  assert np.isfinite(co).all() and np.abs(co).max()<10,(a.name,f)
  ratio=np.linalg.norm(co[edges[:,0]]-co[edges[:,1]],axis=1)/length
  samples.append({r:dict(p99=float(np.percentile(ratio[mask],99)),max=float(ratio[mask].max()),frame=float(f),edge=edges[np.where(mask)[0][np.argmax(ratio[mask])]].tolist()) for r,mask in regions.items()})
  worlds.append({pb.name:pb.matrix.to_quaternion() for pb in rig.pose.bones})
  assert max(abs(x-1) for pb in rig.pose.bones for x in pb.scale)<.001,(a.name,f,'scale')
 result={}
 for r in regions:
  worst=max((x[r] for x in samples),key=lambda x:x['max'])
  result[r]={'p99':max(x[r]['p99'] for x in samples),'worst':worst}
 result['max_rotation_step_deg']={n:max(math.degrees(2*math.acos(min(1,abs(worlds[i][n].normalized().dot(worlds[i-1][n].normalized()))))) for i in range(1,len(worlds))) for n in ('B_Head','B_R_Hand','B_L_Hand','B_L_Foot','B_R_Foot')}
 results[a.name]=result
 print('DEFORM',a.name,{r:(round(result[r]['p99'],2),round(result[r]['worst']['max'],2),result[r]['worst']['frame']) for r in regions})
rig.animation_data.action=None
(P/'work'/(__import__('os').environ.get('INSPECT_REPORT','deformation_final.json'))).write_text(json.dumps(results,indent=2,allow_nan=False))
