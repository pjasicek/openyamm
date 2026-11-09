from pathlib import Path
import bpy,sys,ast,math,json,numpy as np
from mathutils import Vector,Matrix,Quaternion
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import armik
bpy.ops.wm.open_mainfile(filepath=str(p/'work/full_actions.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data
pv=np.array([x.value for x in me.attributes['piece'].data]);P=np.array([tuple(v.co) for v in me.vertices]);q=P[:,2]-.2*P[:,1]
head=[tuple(f.vertices) for f in me.polygons if me.attributes['head'].data[f.index].value and all(q[i]>1.395 for i in f.vertices)]
collar=[tuple(f.vertices) for f in me.polygons if not me.attributes['head'].data[f.index].value and all((pv[i]==1 and P[i,2]>1.29) or (pv[i]==0 and abs(P[i,0])>.12 and 1.1<P[i,2]<1.40) or 13<=pv[i]<=24 for i in f.vertices)]
assert len(head)>100 and len(collar)>100

scene=bpy.context.scene;names=[b.name for b in rig.data.bones]
tree=ast.parse((p/'scripts/author_pilots.py').read_text())
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'set_act','sample','apply','current','write','turn'}],type_ignores=[]),'helpers','exec'),globals())
a=bpy.data.actions['Running'];poses=[sample(a,f) for f in range(int(a.frame_range[1])+1)]
report=[]
for angle in [-18,-12,-6,0,6,12,18]:
 total=worst=0;example=None
 for f,pose in enumerate(poses):
  apply(pose);turn('B_Head',(1,0,0),angle)
  ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();verts=[v.co.copy() for v in mesh.vertices];ev.to_mesh_clear()
  pairs=BVHTree.FromPolygons(verts,head).overlap(BVHTree.FromPolygons(verts,collar));total+=len(pairs)
  if len(pairs)>worst:
   worst=len(pairs);example={'frame':f,'head_rest':[list(me.vertices[i].co) for i in head[pairs[0][0]]],'collar_rest':[list(me.vertices[i].co) for i in collar[pairs[0][1]]]}
 report.append({'angle':angle,'total':total,'worst':worst,'example':example})
 print('RUN_HEAD_CANDIDATE',angle,total,worst,example,flush=True)
(p/'review/running_collar_probe.json').write_text(json.dumps(report,indent=2)+'\n')
