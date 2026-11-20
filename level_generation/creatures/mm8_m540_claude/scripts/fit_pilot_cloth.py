"""Fit the existing garment hinges to the actual moving skin, following the Ogre cloth fitter."""
from pathlib import Path
import bpy,ast,sys,math,json,numpy as np
from mathutils import Vector,Quaternion
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'))
bpy.ops.wm.open_mainfile(filepath=str(p/'work/pilots_fitted.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];scene=bpy.context.scene;names=[b.name for b in rig.data.bones]
tree=ast.parse((p/'scripts/author_pilots.py').read_text())
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'set_act','sample','apply','current','write'}],type_ignores=[]),'pilot_helpers','exec'),globals())
me=body.data;pieces=[x.value for x in me.attributes['piece'].data]
faces=[tuple(f.vertices) for f in me.polygons if all(pieces[i] in (0,2,3,4) for i in f.vertices)]
ids={n:[i for i,x in enumerate(me.attributes[a].data) if x.value] for n,a in [('Cape0','cape'),('LoinFront','loin')]}
axes={n:rig.data.bones[n].matrix_local.to_3x3().inverted()@Vector((1,0,0)) for n in [*ids,'Cape1','Cape2']}
controls={'Cape0':{'Cape0':.1,'Cape1':.7,'Cape2':.5},'LoinFront':{'LoinFront':-1}}
def vertices():
 ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());em=ev.to_mesh();pts=[v.co.copy() for v in em.vertices];ev.to_mesh_clear();return pts
report={}
for name in ['Walking','Running']:
 act=bpy.data.actions[name];poses=[sample(act,f) for f in range(int(act.frame_range[1])+1)]
 increments={n:[] for n in ids};worst={n:0 for n in ids}
 for f,pose in enumerate(poses):
  apply(pose);skin=BVHTree.FromPolygons(vertices(),faces)
  for n in ids:
   trials=[]
   for degrees in range(0,61,3):
    for bone,gain in controls[n].items():rig.pose.bones[bone].rotation_quaternion=pose[bone][0]@Quaternion(axes[bone],gain*math.radians(degrees))
    bpy.context.view_layer.update();pts=vertices();depth=0
    for i in ids[n]:
     loc,normal,fi,d=skin.find_nearest(pts[i],.06)
     if loc is not None and (pts[i]-loc).dot(normal)<-.7*d:depth=max(depth,d)
    trials.append((degrees,depth))
    if depth<.001:break
   best=min(trials,key=lambda v:(v[1]>=.001,v[0] if v[1]<.001 else v[1]))
   increments[n].append(best[0]);worst[n]=max(worst[n],best[1])
   for bone in controls[n]:rig.pose.bones[bone].rotation_quaternion=pose[bone][0]
 for n,rows in increments.items():
  # Smooth an upper envelope so clearance does not disappear between fitted frames.
  vals=np.array(rows[:-1],float)
  high=np.maximum.reduce([np.roll(vals,-1),vals,np.roll(vals,1)])
  vals=np.maximum(vals,(np.roll(high,-1)+2*high+np.roll(high,1))/4)
  vals=np.r_[vals,vals[0]]
  for f,angle in enumerate(vals):
   for bone,gain in controls[n].items():
    q,l=poses[f][bone];poses[f][bone]=(q@Quaternion(axes[bone],math.radians(angle*gain)),l)
 poses[-1]=poses[0];write(name,poses);report[name]={'minimum_fit_depth_m':worst,'extra_angle_degrees':increments}
 print('CLOTH_FIT',name,worst,{n:[min(v),max(v)] for n,v in increments.items()},flush=True)
set_act(None)
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/pilots_fitted.blend'))
(p/'review/pilot_cloth_fit.json').write_text(json.dumps(report,indent=2)+'\n')
