"""Select the smallest rigid collar ellipse clearing the jaw/neck at the measured motion extremes."""
import bpy,sys,os,json,itertools
from pathlib import Path
import numpy as np
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];path=P/'work/male/runtime_ragged.blend';bpy.ops.wm.open_mainfile(filepath=str(path));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Kept'];collar=bpy.data.objects['hes_kept_collar'];scene=bpy.context.scene;D=np.load(P/'texturing/kept_m_uv.npz');faces=D['faces'][D['piece']==1].tolist();trees=[]
restbone=rig.data.bones['Kept_Collar'].matrix_local;centre=Vector((-.03255327,.02501907,1.46521306))
poses={'Kept_Standing':[0,23,52,60],'Kept_Attack':[0,2.5,4.5,10,20.5,24],'Kept_MaceAttack':[0,5,10,17,24],'Kept_Death':[0,6,8.5,9,11,12,12.5,13,16,23,30,39],'Kept_Hit':[0,4.5,5,6.5,9.5,15],'Kept_Running':[0,5,9,10,10.5,16,22],'Kept_Walking':[0,5.5,10,20,30],'Kept_Fidget':[0,7,10,20]}
for name,frames in poses.items():
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
 for f in frames:
  scene.frame_set(int(f),subframe=f%1);inv=restbone@(rig.matrix_world@rig.pose.bones['Kept_Collar'].matrix).inverted();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();points=[inv@body.matrix_world@v.co for v in m.vertices];ev.to_mesh_clear();trees.append(BVHTree.FromPolygons(points,faces,all_triangles=True))
points=[v.co.copy() for v in collar.data.vertices];points += [sum((collar.data.vertices[i].co for i in f.vertices),Vector())/len(f.vertices) for f in collar.data.polygons]
def inside(tree,p):
 d=Vector((.719,.371,.588)).normalized();o=p.copy();hits=0
 for _ in range(64):
  h,n,ix,dist=tree.ray_cast(o,d,5.)
  if h is None:return hits%2==1
  hits+=1;o=h+d*1e-5
 raise AssertionError('ray')
best=None;rows=[]
for sx,sy,dz in itertools.product((.8,.9,1.,1.1),( .6,.7,.8,.9,1.),(-.006,0,.006,.012)):
 M=Matrix.Translation(centre+Vector((0,0,dz)))@Matrix.Diagonal((sx,sy,1,1))@Matrix.Translation(-centre);pts=[M@p for p in points];worst=0.;count=0
 for tree in trees:
  for p in pts:
   h,n,idx,dist=tree.find_nearest(p,.03)
   if h is not None and (p-h).dot(n)<-.5*dist and dist>.0001 and inside(tree,p):worst=max(worst,float(dist));count+=1
 row={'scale_xy':[sx,sy],'dz':dz,'max_inside_m':worst,'inside_samples':count};rows.append(row)
 score=(count>0,worst,count,sx*sy,abs(dz))
 if best is None or score<best[0]:best=(score,M,row);print('BEST',row,flush=True)
M=best[1];collar.data.transform(M);rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
ob=collar.copy();ob.data=collar.data.copy();scene.collection.objects.link(ob)
for mod in list(ob.modifiers):ob.modifiers.remove(mod)
ob.vertex_groups.clear();ob.data.transform(restbone.inverted());ob.parent=None;ob.matrix_world=Matrix.Identity(4)
for o in bpy.data.objects:o.select_set(o==ob)
bpy.context.view_layer.objects.active=ob;bpy.ops.export_scene.gltf(filepath=str(P/'export/hes_kept_collar.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=False,export_skins=False,export_extras=True)
bpy.data.objects.remove(ob,do_unlink=True);bpy.ops.wm.save_as_mainfile(filepath=str(path));(P/'review/collar_shape_fit.json').write_text(json.dumps({'chosen':best[2],'tested_extreme_poses':sum(map(len,poses.values())),'candidates':rows},indent=2)+'\n');print('COLLAR_SHAPE',best[2],flush=True);sys.stdout.flush();sys.stderr.flush();os._exit(0)
