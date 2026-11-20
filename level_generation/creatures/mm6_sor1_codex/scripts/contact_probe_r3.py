import bpy,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/round3_motion.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];staff=bpy.data.objects['Staff'];a=bpy.data.actions['Attack'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];pv=[x.value for x in body.data.attributes['piece'].data]
for f in [37.5,77.5,120,165,250]:
 bpy.context.scene.frame_set(int(f),subframe=f%1);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();v=[x.co.copy() for x in me.vertices];faces=[tuple(x.vertices) for x in me.polygons if all(pv[i]!=3 for i in x.vertices)];tree=BVHTree.FromPolygons(v,faces);ev.to_mesh_clear();se=staff.evaluated_get(bpy.context.evaluated_depsgraph_get());sm=se.to_mesh();bad=[]
 for i,x in enumerate(sm.vertices):
  pt=x.co;q,n,ix,d=tree.find_nearest(pt,.05)
  if q is not None and (pt-q).dot(n)<-.7*d:bad.append((d*1000,i,pv[faces[ix][0]],list(pt),list(q)))
 se.to_mesh_clear();print('PROBE',f,sorted(bad,reverse=True)[:3]);print('JOINTS',{n:list(rig.pose.bones[n].head) for n in ['B_R_UpperArm','B_R_Forearm','B_R_Hand','B_L_UpperArm','B_L_Forearm','B_L_Hand']})
