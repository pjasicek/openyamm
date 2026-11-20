"""Keep the medial shoulder on the clavicle and the grafted head free of arm weights."""
from pathlib import Path
import bpy,bmesh,numpy as np,json,sys
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
reports={}
for source,target in [('motion_final','motion_weighted'),('rig_texturing','rig_texturing_weighted')]:
 bpy.ops.wm.open_mainfile(filepath=str(p/f'work/{source}.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data
 import surface_fit;surface_fit.apply(body)
 import fit_skin;fit_skin.apply(body,rig)
 names=[g.name for g in body.vertex_groups];idx={n:i for i,n in enumerate(names)};w=np.zeros((len(me.vertices),len(names)));co=np.array([v.co[:] for v in me.vertices]);pv=np.array([v.value for v in me.attributes['piece'].data])
 for v in me.vertices:
  for ge in v.groups:w[v.index,ge.group]=ge.weight
 count=0
 edges=np.array([e.vertices[:] for e in me.edges]);neighbours=[[] for _ in me.vertices]
 for a,b in edges:neighbours[a].append(b);neighbours[b].append(a)
 # Smooth the full shoulder blend; a hard medial cutoff leaves a stationary underarm flap.
 for side in 'LR':
  sh=np.array(rig.data.bones[f'B_{side}_UpperArm'].head_local)
  channels=[idx[n] for n in ['B_Spine1','B_Spine2',f'B_{side}_Clavicle',f'B_{side}_UpperArm',f'B_{side}_UpperArmTwist']]
  mask=(pv==0)&(np.linalg.norm(co-sh,axis=1)<.28)
  ids=np.flatnonzero(mask);total=w[:,channels].sum(1)
  for _ in range(24):
   new=w.copy()
   for vi in ids:
    ns=neighbours[vi]
    if ns and total[vi]>.01:
     value=.5*w[vi,channels]+.5*w[np.ix_(ns,channels)].mean(0)
     new[vi,channels]=value/max(value.sum(),1e-9)*total[vi]
   w=new
  count+=len(ids)
 head={vi for f in me.polygons if me.attributes['head'].data[f.index].value for vi in f.vertices}
 for vi in head:
  k=float(np.clip((co[vi,2]-2.015)/.08,0,1));w[vi]=0;w[vi,idx['B_Head']]=k;w[vi,idx['B_Neck']]=1-k
 # The upper-arm band stays rigid along the humerus.
 for vi in np.flatnonzero(pv==2):w[vi]=0;w[vi,idx['B_R_UpperArm']]=1
 order=np.argsort(w,axis=1)[:,:-8];dropped=float(np.take_along_axis(w,order,axis=1).sum(1).max())
 np.put_along_axis(w,order,0.,axis=1)
 assert (w>0).sum(1).max()<=8
 w/=np.maximum(w.sum(1,keepdims=True),1e-10);assert np.allclose(w.sum(1),1,atol=1e-6)
 for g in body.vertex_groups:g.remove(list(range(len(me.vertices))))
 for vi in range(len(me.vertices)):
  for gi in np.where(w[vi]>1e-6)[0]:body.vertex_groups[int(gi)].add([vi],float(w[vi,gi]),'REPLACE')
 reports[source]={'shoulder_influences_changed':count,'head_vertices':len(head),'max_weight_removed_for_eight_influences':dropped}
 bpy.ops.wm.save_as_mainfile(filepath=str(p/f'work/{target}.blend'))
 if source=='motion_final':
  common.workbench_clay(bpy.context.scene);a=bpy.data.actions['Attack'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
  for f in [12,18,24,30]:
   bpy.context.scene.frame_set(f);common.render_views(str(p/f'review/shoulder_fit_{f}'),1.4,3.1,views=('front','left','back'),resolution=(500,700))
(p/'work/shoulder_weights.json').write_text(json.dumps(reports,indent=2))
