"""Every clip at 48 Hz: body/hand edge ratios and independently measured posture."""
import bpy,sys,json,math
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];path=sys.argv[sys.argv.index('--')+1]
bpy.ops.wm.open_mainfile(filepath=str(Path(path).resolve()));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data;scene=bpy.context.scene
co=np.array([tuple(v.co)for v in me.vertices]);E=np.array([tuple(e.vertices)for e in me.edges]);length=np.linalg.norm(co[E[:,0]]-co[E[:,1]],axis=1);pv=np.array([x.value for x in me.attributes['piece'].data]);names=[g.name for g in body.vertex_groups];W=np.zeros((len(co),len(names)))
for v in me.vertices:
 for e in v.groups:W[v.index,e.group]=e.weight
masks={}
for side in 'LR':
 for region,keys in [('arm',('UpperArm','Forearm')),('hand',('Hand','Finger'))]:
  w=W[:,[i for i,n in enumerate(names)if n.startswith(f'B_{side}_')and any(k in n for k in keys)]].sum(1)
  masks[side+'_'+region]=(w[E[:,0]]>.3)&(w[E[:,1]]>.3)&(length>1e-5)
report={}
for a in bpy.data.actions:
 if a.name not in ('Standing','Walking','Running','Attack','Cast','Hit','Death','Dead','Fidget'):continue
 rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];lo,hi=a.frame_range;duration=(hi-lo)/30;row={'duration':duration,'samples':0,'posture':[],'bounds':[],'stretch':{n:{'p99':0,'max':0}for n in masks}}
 for t in np.linspace(0,duration,max(2,math.ceil(duration*48)+1)):
  f=lo+t*30;scene.frame_set(int(f),subframe=float(f%1));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();xyz=np.array([tuple(v.co)for v in mesh.vertices]);ev.to_mesh_clear();rat=np.linalg.norm(xyz[E[:,0]]-xyz[E[:,1]],axis=1)/np.maximum(length,1e-6)
  for n,m in masks.items():
   vals=rat[m];entry=row['stretch'][n];entry['p99']=max(entry['p99'],float(np.percentile(vals,99)))
   if vals.max()>entry['max']:
    k=np.where(m)[0][np.argmax(vals)];entry.update(max=float(vals.max()),time=float(t),edge=E[k].tolist(),pieces=pv[E[k]].tolist(),coordinates=co[E[k]].tolist(),weights=[{names[g.group]:round(g.weight,3)for g in me.vertices[int(v)].groups if g.weight>.001}for v in E[k]])
  pel=rig.pose.bones['B_Pelvis'].head;neck=rig.pose.bones['B_Neck'].head;sp=rig.pose.bones['B_Spine'].head;d=neck-sp;lean=math.degrees(math.atan2(math.hypot(d.x,d.y),d.z));row['posture'].append([float(t),pel.z,lean]);row['bounds'].append([xyz.min(0).tolist(),xyz.max(0).tolist()]);row['samples']+=1
 rows=np.array(row.pop('posture'));row['posture']={'pelvis_min':float(rows[:,1].min()),'pelvis_max':float(rows[:,1].max()),'trunk_lean_max':float(rows[:,2].max()),'trunk_lean_mean':float(rows[:,2].mean())};bd=np.array(row.pop('bounds'));row['bounds']=[bd[:,0,:].min(0).tolist(),bd[:,1,:].max(0).tolist()];report[a.name]=row;print('SCAN',a.name,row)
(P/'review/deformation_scan.json').write_text(json.dumps(report,indent=2))
