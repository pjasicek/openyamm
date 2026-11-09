"""Check conservative head following against the fitted shoulder surface."""
from pathlib import Path
import bpy,json,numpy as np,math,sys
from mathutils import Vector,Quaternion,Matrix
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'mm6_natm_claude/scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'export/mm8_m592.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene;co=np.array([tuple(v.co) for v in body.data.vertices]);E=np.array([tuple(e.vertices) for e in body.data.edges]);L=np.linalg.norm(co[E[:,0]]-co[E[:,1]],axis=1);valid=L>1e-5
head=[tuple(f.vertices) for f in body.data.polygons if all(co[i,1]<-.3 and co[i,2]>1.17 for i in f.vertices)]
torso=[tuple(f.vertices) for f in body.data.polygons if not body.data.attributes['head'].data[f.index].value and all(co[i,2]>1.0 and abs(co[i,0])<.5 for i in f.vertices)]
assert len(head)>200 and len(torso)>100
report=[]
for name in ['Standing','Walking','Running','Attack','Hit','Fidget']:
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
 for f in np.linspace(0,a.frame_range[1],5):
  sc.frame_set(int(f),subframe=f%1);orig={n:rig.pose.bones[n].matrix_basis.copy() for n in ['B_Neck','B_Head']}
  for yaw,pitch in [(0,0),(-15,-10),(-15,10),(15,-10),(15,10)]:
   for n,m in orig.items():rig.pose.bones[n].matrix_basis=m
   bpy.context.view_layer.update();q=Quaternion((0,0,1),math.radians(yaw))@Quaternion((1,0,0),math.radians(pitch));R=Quaternion(q.axis,q.angle/2).to_matrix().to_4x4()
   for n in orig:
    pb=rig.pose.bones[n];m=pb.matrix.copy();c=m.translation.copy();pb.matrix=Matrix.Translation(c)@R@Matrix.Translation(-c)@m;bpy.context.view_layer.update()
   ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();c=np.array([tuple(v.co) for v in me.vertices]);ev.to_mesh_clear();pairs=BVHTree.FromPolygons(c.tolist(),head).overlap(BVHTree.FromPolygons(c.tolist(),torso));ratio=np.linalg.norm(c[E[:,0]]-c[E[:,1]],axis=1)/np.maximum(L,1e-9);r={'clip':name,'frame':float(f),'yaw':yaw,'pitch':pitch,'head_shoulder_intersections':len(pairs),'edge_p99':float(np.percentile(ratio[valid],99))};report.append(r)
   assert not pairs,r
   if name=='Standing' and f==0 and yaw:
    common.workbench_clay(sc,textured=True);common.render_views(str(P/'review'/f'head_look_{yaw}_{pitch}'),1.30,1.25,views=('front','three_quarter'),resolution=(650,650),target=(0,-.25))
  for n,m in orig.items():rig.pose.bones[n].matrix_basis=m
(P/'review/head_look.json').write_text(json.dumps({'limits':{'yaw':15,'pitch':10},'samples':report},indent=2)+'\n');print('HEAD_LOOK',len(report),'passed',flush=True)
