from pathlib import Path
import bpy,json,numpy as np,math
from mathutils import Vector,Quaternion,Matrix
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_uv.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data
pv=np.array([x.value for x in me.attributes['piece'].data]);P=np.array([tuple(v.co) for v in me.vertices]);q=P[:,2]-.2*P[:,1]
head=[tuple(f.vertices) for f in me.polygons if all(pv[i] in [0,7,8,11] and P[i,2]>1.49 for i in f.vertices)]
collar=[]
for f in me.polygons:
 c=P[list(f.vertices)].mean(0);ids=pv[list(f.vertices)]
 if (np.all(ids==1) and abs(c[0])>.11 and 1.36<c[2]<1.64) or (np.all(ids==0) and abs(c[0])>.14 and 1.25<c[2]<1.46):collar.append(tuple(f.vertices))
assert len(head)>100 and len(collar)>20,(len(head),len(collar))

report={}
for yaw_limit,pitch_limit in [(25,15),(15,8),(8,4),(0,0)]:
 bad=[];samples=0
 for name in ['Standing','Walking','Attack','Hit','Fidget']:
  a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
  for f in np.linspace(0,a.frame_range[1],9):
   bpy.context.scene.frame_set(int(f),subframe=f-int(f));original={n:rig.pose.bones[n].matrix_basis.copy() for n in ['B_Neck','B_Head']}
   for yaw in [-yaw_limit,0,yaw_limit]:
    for pitch in [-pitch_limit,0,pitch_limit]:
     for n,m in original.items():rig.pose.bones[n].matrix_basis=m
     bpy.context.view_layer.update();q=Quaternion((0,0,1),math.radians(yaw))@Quaternion((1,0,0),math.radians(pitch));q=Quaternion(q.axis,q.angle/2);R=q.to_matrix().to_4x4()
     for n in ['B_Neck','B_Head']:
      pb=rig.pose.bones[n];m=pb.matrix.copy();c=m.translation.copy();pb.matrix=Matrix.Translation(c)@R@Matrix.Translation(-c)@m;bpy.context.view_layer.update()
     ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();verts=[v.co.copy() for v in mesh.vertices];ev.to_mesh_clear();pairs=BVHTree.FromPolygons(verts,head).overlap(BVHTree.FromPolygons(verts,collar));samples+=1
     if pairs:bad.append({'clip':name,'frame':float(f),'yaw':yaw,'pitch':pitch,'pairs':len(pairs)})
   for n,m in original.items():rig.pose.bones[n].matrix_basis=m
 report[f'{yaw_limit}/{pitch_limit}']={'samples':samples,'intersections':bad};print('HEAD_LOOK',yaw_limit,pitch_limit,len(bad),bad[:2],flush=True)
 if not bad:break
assert not bad,report
(p/'review/head_look.json').write_text(json.dumps({'limits':{'yaw':yaw_limit,'pitch':pitch_limit},'checks':report},indent=2)+'\n')
