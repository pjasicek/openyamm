import bpy,sys,numpy as np
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_arm_clear.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];a=bpy.data.actions['Death'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];scene=bpy.context.scene;common.workbench_clay(scene)
from mathutils.bvhtree import BVHTree
pv=[a.value for a in body.data.attributes['piece'].data]
for f,vi in [(56.5,2630),(15,3458),(156,3754)]:
 scene.frame_set(int(f),subframe=f-int(f));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());em=ev.to_mesh();co=[v.co.copy() for v in em.vertices];ev.to_mesh_clear();print('VERTEX',f,vi,'REST',list(body.data.vertices[vi].co),'POSE',list(co[vi]),'piece',pv[vi])
 for pid in [101,102,103,104]:
  fs=[tuple(poly.vertices) for poly in body.data.polygons if all(pv[i]==pid for i in poly.vertices)];tree=BVHTree.FromPolygons(co,fs);q,n,face,d=tree.find_nearest(co[vi]);print('NEAR',pid,list(q),list(n),d,'SIGNED',(co[vi]-q).dot(n))
