import bpy,sys,json
import numpy as np
from pathlib import Path
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_weighted.blend'));o=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];me=o.data
pv=np.zeros(len(me.vertices),np.int32);me.attributes['piece'].data.foreach_get('value',pv);groups={g.name:g for g in o.vertex_groups};names={g.index:g.name for g in o.vertex_groups};changes=0
def put(i,w):
 global changes
 for g in groups.values():g.remove([i])
 total=sum(w.values());assert total>0
 for n,v in w.items():
  if v>1e-6:groups[n].add([i],v/total,'REPLACE')
 changes+=1
for v in me.vertices:
 i=v.index;x,y,z=v.co;part=pv[i];w={names[e.group]:e.weight for e in v.groups if e.weight>1e-5};sd='L' if x>0 else 'R'
 if part in (2,3):
  good={n:ww for n,ww in w.items() if n.startswith('B_'+sd+'_') and any(t in n for t in ('Forearm','Hand','Finger'))}
  if not good:good={f'B_{sd}_Forearm':1}
  put(i,good)
 elif part in (4,12,13) or (part==0 and (z>1.45 or (z>1.30 and abs(x)<.065 and y<-.07) or (z>1.36 and y>.08))):put(i,{'B_Head':1})
 elif part in (5,6,10,11):
  t=np.clip((z-.13)/.14,0,1);put(i,{f'B_{sd}_Foot':1-t,f'B_{sd}_Calf':t})
 elif part in (7,8,9):put(i,{'B_Pelvis':1})
 elif part>=14:
  n='B_Pelvis' if z<1.08 else 'B_Spine' if z<1.2 else 'B_Spine1' if z<1.30 else 'B_Spine2';put(i,{n:1})
 elif part==0 and abs(x)<.17 and z<1.40:
  arm=[n for n in w if any(t in n for t in ('Clavicle','UpperArm','Forearm','Hand'))];moved=0
  for n in arm:
   keep=float(np.clip((abs(x)-.10)/.07,0,1));moved+=w[n]*(1-keep);w[n]*=keep
  w['B_Spine2']=w.get('B_Spine2',0)+moved;put(i,w)
bpy.context.view_layer.objects.active=o
for ob in bpy.data.objects:ob.select_set(ob==o)
bpy.ops.object.vertex_group_limit_total(limit=4);bpy.ops.object.vertex_group_normalize_all(lock_active=False)
assert max(abs(sum(e.weight for e in v.groups)-1) for v in me.vertices)<1e-5
print('WEIGHT_CLEANUP',changes);bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_clean.blend'))
