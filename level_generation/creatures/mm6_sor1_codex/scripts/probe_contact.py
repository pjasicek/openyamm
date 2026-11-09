import bpy,numpy as np,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/production_master.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];act=bpy.data.actions['Death'];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];bpy.context.scene.frame_set(99,subframe=.5)
ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();v=[x.co.copy() for x in m.vertices];ev.to_mesh_clear();pv=[a.value for a in body.data.attributes['piece'].data]
for i in [3435,3436,3437,3240]:
 print('VERTEX',i,'REST',list(body.data.vertices[i].co),'POSE',list(v[i]),'WEIGHTS',[(body.vertex_groups[g.group].name,g.weight) for g in body.data.vertices[i].groups])
 for piece in [101,102]:
  fs=[tuple(f.vertices) for f in body.data.polygons if all(pv[j]==piece for j in f.vertices)];tree=BVHTree.FromPolygons(v,fs);q,n,fi,d=tree.find_nearest(v[i]);hits=[]
  for direct in [(1,.037,.021),(.02,1,.01),(.01,.02,1)]:
   direction=Vector(direct).normalized();start=v[i].copy();count=0
   for k in range(30):
    hit,_,_,_=tree.ray_cast(start,direction,5)
    if hit is None:break
    count+=1;start=hit+direction*.00001
   hits.append(count)
  print('SHOE',piece,'d',d,'signed',(v[i]-q).dot(n),'hits',hits)
common.workbench_clay(bpy.context.scene,textured=True);common.render_views(str(p/'review/death_contact'),.32,1.8,views=('front','left','three_quarter'),resolution=(600,600))
