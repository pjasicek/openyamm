import bpy,numpy as np,json,math,os
from pathlib import Path
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/os.environ.get('GATE_BLEND','work/anim_reduced.blend')))
r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];me=b.data;sc=bpy.context.scene
co=np.array([tuple(v.co) for v in me.vertices]);E=np.array([tuple(e.vertices) for e in me.edges]);lens=np.linalg.norm(co[E[:,0]]-co[E[:,1]],axis=1);names=[g.name for g in b.vertex_groups];W=np.zeros((len(co),len(names)))
for v in me.vertices:
 for g in v.groups:W[v.index,g.group]=g.weight
pv=np.zeros(len(co),np.int32);me.attributes['piece'].data.foreach_get('value',pv)
regions={}
for sd in ['L','R']:
 for region,keys in [('arm',['UpperArm','Forearm','Hand']),('hand',['Hand','Finger'])]:
  vs=W[:,[i for i,n in enumerate(names) if (n.startswith(f'B_{sd}_') and any(k in n for k in keys)) or (region=='arm' and n.startswith((f'ClothArm_{sd}_',f'Cuff_{sd}')))]].sum(1)>.3
  regions[sd+'_'+region]=(vs[E[:,0]] & vs[E[:,1]])
regions['robe']=(pv[E[:,0]]==1)&(pv[E[:,1]]==1)
report={}
for a in bpy.data.actions:
 r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];worst={k:{'p99':0,'max':0} for k in regions};heights=[];leans=[];floors=[];floor_worst=(999,None,None)
 for f in np.arange(0,int(a.frame_range[1])+.01,.5):
  sc.frame_set(int(f),subframe=float(f%1));ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();P=np.array([tuple(v.co) for v in m.vertices]);ev.to_mesh_clear();stretch=np.linalg.norm(P[E[:,0]]-P[E[:,1]],axis=1)/np.maximum(lens,1e-6)
  for k,mask in regions.items():
   p99=float(np.percentile(stretch[mask],99));mx=float(stretch[mask].max())
   if p99>worst[k]['p99']:worst[k]['p99']=p99;worst[k]['p99_frame']=float(f)
   if mx>worst[k]['max']:worst[k]['max']=mx;worst[k]['max_frame']=float(f)
  pelvis=r.pose.bones['B_Pelvis'].head;neck=r.pose.bones['B_Neck'].head;v=neck-pelvis;heights.append(pelvis.z);leans.append(math.degrees(math.atan2(math.hypot(v.x,v.y),v.z)));floors.append(float(P[:,2].min()))
  if floors[-1]<floor_worst[0]:floor_worst=(floors[-1],float(f),int(pv[int(P[:,2].argmin())]))
 report[a.name]={'stretch':worst,'pelvis_height_m':[min(heights),max(heights)],'trunk_lean_deg':[min(leans),max(leans)],'min_floor_m':min(floors),'floor_worst':floor_worst,'samples':len(heights),'G4_pass':max(worst[k]['p99'] for k in ['L_arm','R_arm'])<=2.0,'G5_pass':max(worst[k]['max'] for k in ['L_hand','R_hand'])<=4.5}
 print('DENSE',a.name,json.dumps(report[a.name]))
(p/'work/gates_dense.json').write_text(json.dumps(report,indent=2))
