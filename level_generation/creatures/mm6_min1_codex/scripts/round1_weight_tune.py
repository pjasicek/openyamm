"""Distribute shoulder roll over the existing counter-twist helpers; choose by the complete ROM."""
import bpy,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/round1_contacts.blend'));b=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];me=b.data;sc=bpy.context.scene;co=np.array([v.co[:] for v in me.vertices]);names=[g.name for g in b.vertex_groups];idx={n:i for i,n in enumerate(names)};W=np.zeros((len(co),len(names)))
for v in me.vertices:
 for g in v.groups:W[v.index,g.group]=g.weight
E=np.array([e.vertices[:] for e in me.edges]);rl=np.linalg.norm(co[E[:,0]]-co[E[:,1]],axis=1);masks={};tt={}
for s in 'RL':
 arm=[i for i,n in enumerate(names) if n.startswith('B_'+s+'_') and any(k in n for k in ['UpperArm','Forearm','Hand'])];wa=W[:,arm].sum(1);masks[s]=(wa[E[:,0]]>.3)&(wa[E[:,1]]>.3);U,F=[np.array(r.data.bones[f'B_{s}_{n}'].head_local) for n in ['UpperArm','Forearm']];d=F-U;tt[s]=(co-U)@d/(d@d)
def install(V):
 V=V.copy()
 for i in range(len(V)):
  keep=np.argsort(V[i])[-8:];total=V[i,keep].sum()
  for g in list(me.vertices[i].groups):b.vertex_groups[g.group].remove([i])
  for k in keep:
   if V[i,k]>1e-7:b.vertex_groups[int(k)].add([i],float(V[i,k]/total),'REPLACE')
 bpy.context.view_layer.update()
def measure():
 worst={}
 for a in bpy.data.actions:
  r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];mx=0
  frames=range(int(a.frame_range[0]),int(a.frame_range[1])+1,2)
  for f in frames:
   sc.frame_set(f);ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();v=np.array([v.co[:] for v in m.vertices]);ev.to_mesh_clear();ratio=np.linalg.norm(v[E[:,0]]-v[E[:,1]],axis=1)/np.maximum(rl,1e-8);mx=max(mx,max(float(np.percentile(ratio[mask],99)) for mask in masks.values()))
  worst[a.name]=mx
 return worst
report=[];best=(999,None,None)
for end,share in [(0,0),(.45,.8),(.6,.8),(.75,.8),(.9,.8),(.6,1.0),(.75,1.0),(.9,1.0)]:
 V=W.copy()
 if end:
  for s in 'RL':
   t=np.clip(tt[s]/end,0,1);fall=1-t*t*(3-2*t);a=idx[f'B_{s}_UpperArm'];c=idx[f'B_{s}_UpperArmTwist'];total=V[:,a]+V[:,c];V[:,c]=total*fall*share;V[:,a]=total-V[:,c]
 install(V);m=measure();score=max(m.values());report.append({'end_fraction':end,'counter_share':share,'G4':m});print('SHOULDER',end,share,m,flush=True)
 if score<best[0]:best=(score,V.copy(),[end,share])
install(best[1]);(P/'review/round1/shoulder_weights.json').write_text(json.dumps({'curve':report,'selected':best[2],'maximum_G4':best[0]},indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round1_weight_tuned.blend'))
