"""Half-frame contact screen: closed skin containment and separate garment proximity."""
from pathlib import Path
import sys,json,bpy,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
src,*clips=sys.argv[sys.argv.index('--')+1:]
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(Path(src).resolve()))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data
names=[g.name for g in body.vertex_groups];weight=np.zeros((len(me.vertices),len(names)))
for v in me.vertices:
 for x in v.groups:weight[v.index,x.group]=x.weight
piece=np.array([v.value for v in me.attributes['piece'].data]);faces=[list(f.vertices) for f in me.polygons]
skinfaces=[f for f in faces if piece[f[0]]==0];clothfaces=[f for f in faces if piece[f[0]]==1]
def region(side,parts,threshold):
 idx=[i for i,n in enumerate(names) if n.startswith('B_'+side+'_') and any(k in n for k in parts)]
 return weight[:,idx].sum(1)>threshold
parts={s:{'arm':region(s,['Clavicle','UpperArm','Forearm','Hand','Finger'],.15),'hand':region(s,['Hand','Finger'],.5),'forearm':region(s,['Forearm'],.5)} for s in 'LR'}
rest=np.array([v.co[:] for v in me.vertices]);
def inside(tree,point):
 votes=0
 for axis in ((1,.317,.193),(-.271,1,.419),(.219,-.349,1)):
  d=Vector(axis).normalized();start=Vector(point);count=0
  for _ in range(100):
   hit,normal,index,dist=tree.ray_cast(start,d,10)
   if hit is None:break
   count+=1;start=hit+d*1e-5
  else:raise AssertionError('Ray parity did not escape closed skin')
  votes+=count%2
 return votes>=2
rest_tree=BVHTree.FromPolygons(rest.tolist(),skinfaces)
assert inside(rest_tree,(0,.02,1.4)) and not inside(rest_tree,(5,5,5))
report={}
for name in clips:
 act=bpy.data.actions[name];rig.animation_data.action=act
 if act.slots:rig.animation_data.action_slot=act.slots[0]
 entry={}
 for fr in np.arange(act.frame_range[0],act.frame_range[1]+.01,.5):
  bpy.context.scene.frame_set(int(fr),subframe=float(fr%1));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());em=ev.to_mesh();co=np.array([v.co[:] for v in em.vertices]);ev.to_mesh_clear()
  skin=BVHTree.FromPolygons(co.tolist(),skinfaces)
  for side in 'LR':
   fl=[f for f in skinfaces if not any(parts[side]['arm'][i] for i in f)]
   other=BVHTree.FromPolygons(co.tolist(),fl)
   for region_name in ('hand','forearm'):
    for i in np.where(parts[side][region_name]&(piece==0))[0]:
     loc,normal,fi,dist=other.find_nearest(Vector(co[i]),.12)
     if loc is not None and (Vector(co[i])-loc).dot(normal)<-.7*dist:
      key=side+'_'+region_name
      if dist>entry.get(key,{}).get('depth_m',0):entry[key]={'depth_m':float(dist),'frame':float(fr),'vertex':int(i),'face':fl[fi]}
  for i in np.where(piece==1)[0]:
   loc,normal,fi,dist=skin.find_nearest(Vector(co[i]),.12)
   if loc is not None and dist>1e-5 and (Vector(co[i])-loc).dot(normal)<-.7*dist and inside(skin,co[i]):
    key='wrap_under_belt' if rest[i,2]>1.155 else 'wrap_exposed'
    if dist>entry.get(key,{}).get('depth_m',0):entry[key]={'depth_m':float(dist),'frame':float(fr),'vertex':int(i),'face':skinfaces[fi],'rest':rest[i].tolist()}
 report[name]=entry
 print(name,json.dumps(entry),flush=True)
(p/'review/contacts.json').write_text(json.dumps(report,indent=2)+'\n')
