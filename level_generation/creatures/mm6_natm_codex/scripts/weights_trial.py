"""Smooth only the shoulder/arm skin transition; hold the entire hand and finger region fixed."""
import bpy,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/motion_valid.blend'));rig=bpy.data.objects['Rig'];ob=bpy.data.objects['Body'];me=ob.data;co=np.array([tuple(v.co)for v in me.vertices]);pv=np.array([d.value for d in me.attributes['piece'].data]);names=[g.name for g in ob.vertex_groups];W=np.zeros((len(co),len(names)))
for v in me.vertices:
 for g in v.groups:W[v.index,g.group]=g.weight
base=W.copy();E=np.array([list(e.vertices)for e in me.edges]);lengths=np.linalg.norm(co[E[:,0]]-co[E[:,1]],axis=1);arms={s:base[:,[i for i,n in enumerate(names)if n.startswith(f'B_{s}_')and any(t in n for t in ['UpperArm','Forearm','Hand'])]].sum(1)for s in 'LR'};hand=base[:,[i for i,n in enumerate(names)if 'Hand'in n or 'Finger'in n]].sum(1);mask=(pv==0)&((arms['L']+arms['R'])>.01)&(hand<.3)&(abs(co[:,0])>.095)&(co[:,2]<1.49);adj=[[]for _ in co]
for a,b in E:
 if pv[a]==0 and pv[b]==0:adj[a].append(b);adj[b].append(a)
ids=np.where(mask)[0];armedges={s:(arms[s][E[:,0]]>.3)&(arms[s][E[:,1]]>.3)&(lengths>.00001)for s in 'LR'};samples=[(a,f)for a in bpy.data.actions for f in sorted(set(list(range(0,int(a.frame_range[1])+1,3))+[int(a.frame_range[1])]))];curve=[];chosen=None
for rounds in [0,2,4,8,12,20]:
 W=base.copy()
 for _ in range(rounds):
  nxt=W.copy()
  for i in ids:
   if adj[i]:nxt[i]=W[i]*.6+W[adj[i]].mean(0)*.4
  W=nxt
 for i in ids:
  keep=np.argsort(W[i])[-8:];values=W[i,keep];values/=values.sum()
  for g in ob.vertex_groups:g.remove([int(i)])
  for j,w in zip(keep,values):
   if w>1e-8:ob.vertex_groups[int(j)].add([int(i)],float(w),'REPLACE')
 bpy.context.view_layer.update();worst={};p99max=0
 for act,f in samples:
  rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];bpy.context.scene.frame_set(f);ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());mm=ev.to_mesh();v=np.empty((len(co),3));mm.vertices.foreach_get('co',v.ravel());ev.to_mesh_clear();ratios=np.linalg.norm(v[E[:,0]]-v[E[:,1]],axis=1)/np.maximum(lengths,1e-9)
  for s,m in armedges.items():
   value=float(np.percentile(ratios[m],99));p99max=max(p99max,value)
   if value>worst.get(act.name,{}).get('p99',0):worst[act.name]={'p99':value,'max':float(ratios[m].max()),'frame':f,'side':s}
 curve.append({'iterations':rounds,'p99_max':p99max,'clips':worst});print('WEIGHTS',rounds,p99max,worst,flush=True)
 if chosen is None or p99max<chosen[0]:chosen=(p99max,rounds,W.copy())
 if p99max<=1.95:break
W=chosen[2]
for i in ids:
 keep=np.argsort(W[i])[-8:];values=W[i,keep];values/=values.sum()
 for g in ob.vertex_groups:g.remove([int(i)])
 for j,w in zip(keep,values):
  if w>1e-8:ob.vertex_groups[int(j)].add([int(i)],float(w),'REPLACE')
rig.animation_data.action=None;bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/weight_fit.blend'));(P/'review/weight_refinement.json').write_text(json.dumps({'frozen_region':'all hand/finger vertices above 0.3 influence; head; torso centre; all non-skin shells','comparison_regions':'fixed original arm masks, so changed ownership cannot hide a stretched edge','selected_iterations':chosen[1],'sample_frames':len(samples),'curve':curve},indent=2))
