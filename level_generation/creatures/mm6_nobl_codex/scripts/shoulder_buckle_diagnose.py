import bpy,numpy as np,json
from pathlib import Path
p=Path(__file__).resolve().parents[1];out=p/'review/shoulder_buckle_20261011';out.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v12.blend'))
r=bpy.data.objects['Rig'];o=bpy.data.objects['Body'];me=o.data
co=np.array([v.co[:] for v in me.vertices]);pv=np.zeros(len(co),np.int32);me.attributes['piece'].data.foreach_get('value',pv)
names=[g.name for g in o.vertex_groups];w=np.zeros((len(co),len(names)))
for v in me.vertices:
 for g in v.groups:w[v.index,g.group]=g.weight
report={}
for part in [0,1,10,11,18,19]:
 ids=np.flatnonzero(pv==part)
 report[str(part)]={'bounds':[co[ids].min(0).tolist(),co[ids].max(0).tolist()],'weights':{names[i]:[float(w[ids,i].min()),float(w[ids,i].max())] for i in np.flatnonzero(w[ids].max(0)>1e-5)}}
print(json.dumps(report,indent=2));(out/'diagnosis.json').write_text(json.dumps(report,indent=2))
r.animation_data.action=None
for b in r.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update()
faces=np.array([poly.vertices[:] for poly in me.polygons])
poses=[];labels=[];matrices=[]
for a in bpy.data.actions:
 r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
 for f in range(int(a.frame_range[1])+1):
  bpy.context.scene.frame_set(f);bpy.context.view_layer.update()
  ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());em=ev.to_mesh()
  poses.append(np.array([v.co[:] for v in em.vertices]));ev.to_mesh_clear()
  labels.append((a.name,f));matrices.append(np.array([b.matrix@b.bone.matrix_local.inverted() for b in r.pose.bones]))
np.savez_compressed(out/'diagnosis.npz',co=co,pv=pv,w=w,names=names,faces=faces,poses=poses,labels=np.array(labels),matrices=matrices,bone_names=[b.name for b in r.pose.bones])
