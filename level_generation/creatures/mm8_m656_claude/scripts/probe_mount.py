import bpy,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/master_complete.blend'));r=bpy.data.objects['Rig'];sc=bpy.context.scene;a=bpy.data.actions['Death'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
for x in [.245,.28,.30,.32]:
 for y in [0,.035,.065,.095]:
  vals=[]
  for f in np.arange(0,109.001,1):
   sc.frame_set(int(f));m=r.pose.bones['B_Pelvis'].matrix@r.data.bones['B_Pelvis'].matrix_local.inverted();vals.append((m@Vector((x,y,.98))).z)
  print('MOUNT',x,y,min(vals),flush=True)
bpy.ops.wm.open_mainfile(filepath=str(P/'work/master_settled.blend'));r=bpy.data.objects['Rig'];sc=bpy.context.scene
for name in ['Standing','Walking','Running','Hit','Attack','Fidget','Death']:
 a=bpy.data.actions[name];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];mx=(0,0)
 for f in np.arange(0,float(a.frame_range[1])+.001,1):
  sc.frame_set(int(f));trees=[]
  for n in ['Body','ScabbardMesh']:
   o=bpy.data.objects[n];e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();trees.append(BVHTree.FromPolygons([o.matrix_world@v.co for v in m.vertices],[tuple(p.vertices) for p in m.polygons]));e.to_mesh_clear()
  pairs=trees[0].overlap(trees[1]);c=len(pairs)
  if c>mx[0]:
   o=bpy.data.objects['Body'];g={v.index:v.name for v in o.vertex_groups};bones=sorted(set(g[max(o.data.vertices[v].groups,key=lambda e:e.weight).group] for bi,si in pairs for v in o.data.polygons[bi].vertices));print('CONTACT',name,f,c,bones)
  mx=max(mx,(c,float(f)))
 print('INTERSECTIONS',name,mx,flush=True)
