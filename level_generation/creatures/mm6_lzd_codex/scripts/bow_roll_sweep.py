import bpy,json,math,sys
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/master.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data;scene=bpy.context.scene
pv=np.array([x.value for x in me.attributes['piece'].data]);names=[g.name for g in body.vertex_groups];hand=np.array([sum(g.weight for g in v.groups if 'Hand'in names[g.group]or'Finger'in names[g.group])for v in me.vertices])>.25;faces=[tuple(f.vertices)for f in me.polygons if all(pv[v]<201 and not hand[v]for v in f.vertices)];inv=rig.data.bones['Bow'].matrix_local.inverted();bow=[inv@v.co for v in me.vertices if pv[v.index]==201 and abs((inv@v.co).z)>.11];cache=[]
for n in ['Standing','Walking','Running','Death','Dead','Fidget']:
 a=bpy.data.actions[n];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
 for f in np.linspace(*a.frame_range,7):
  scene.frame_set(int(f),subframe=float(f%1));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();xyz=[tuple(v.co)for v in m.vertices];ev.to_mesh_clear();cache.append((n,float(f),rig.pose.bones['Bow'].matrix.copy(),BVHTree.FromPolygons(xyz,faces)))
rows=[]
for angle in range(-180,181,15):
 rot=Matrix.Rotation(math.radians(angle),4,'Z');worst=0;hits=0;by={}
 for n,f,bm,tree in cache:
  M=bm@rot;pts=[M@v for v in bow]+[M@Vector((0,.215,z))for z in np.linspace(-.55,.55,41)];dmax=0
  for p in pts:
   loc,normal,idx,d=tree.find_nearest(p,.06)
   if loc is not None and (p-loc).dot(normal)<-.7*d:dmax=max(dmax,d)
  worst=max(worst,dmax);hits+=dmax>.002;by[n]=max(by.get(n,0),dmax)
 row={'angle':angle,'max_m':worst,'bad_poses':hits,'clips':by};rows.append(row);print('ROLL',row)
(P/'review/bow_roll_sweep.json').write_text(json.dumps(rows,indent=2));print('BEST',min(rows,key=lambda r:(r['bad_poses'],r['max_m'],abs(r['angle']))))
