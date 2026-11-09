"""Fit the final cape to the ground plane without suspending the fallen body above it."""
from pathlib import Path
import bpy,ast,json,math,numpy as np
from mathutils import Vector,Quaternion
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1]
source=p/'work/rig_uv.blend'; backup=p/'work/rig_uv_before_ground.blend'
if not backup.exists():
 import shutil;shutil.copyfile(source,backup)
bpy.ops.wm.open_mainfile(filepath=str(backup))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];wand=bpy.data.objects['Wand'];scene=bpy.context.scene;names=[b.name for b in rig.data.bones]
tree=ast.parse((p/'scripts/author_pilots.py').read_text())
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'set_act','sample','apply','current','write'}],type_ignores=[]),'helpers','exec'),globals())
piece=np.array([x.value for x in body.data.attributes['piece'].data]);skin=np.isin(piece,[0,2,3,4]);cape=np.array([x.value for x in body.data.attributes['cape'].data])>0
faces=[tuple(f.vertices) for f in body.data.polygons if all(skin[i] for i in f.vertices)]
axis=rig.data.bones['Cape0'].matrix_local.to_3x3().inverted()@Vector((1,0,0))
def coords(ob):
 ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();pts=[ob.matrix_world@v.co for v in me.vertices];ev.to_mesh_clear();return pts

act=bpy.data.actions['Death'];pose=sample(act,39);apply(pose);pts=coords(body);core=min(v.z for i,v in enumerate(pts) if not cape[i]);surface=BVHTree.FromPolygons(pts,faces)
axes={n:rig.data.bones[n].matrix_local.to_3x3().inverted()@Vector((1,0,0)) for n in ['Cape0','Cape1','Cape2']}
def cost(angles):
 for n,a in zip(axes,angles):rig.pose.bones[n].rotation_quaternion=pose[n][0]@Quaternion(axes[n],math.radians(a))
 bpy.context.view_layer.update();pts=coords(body);low=min(v.z for i,v in enumerate(pts) if cape[i]);depth=0
 for i in np.flatnonzero(cape):
  loc,n,fi,d=surface.find_nearest(pts[i],.08)
  if loc is not None and (pts[i]-loc).dot(n)<-.7*d:depth=max(depth,d)
 error=max(0,core-.015-low)
 return error*error+100*depth*depth,low,depth
best=(100,None)
for a in range(-2,5,2):
 for b in range(-14,-3,2):
  for c in range(-75,-14,10):
   vals=cost([a,b,c]);score=vals[0]+1e-8*(a*a+b*b+c*c)
   if score<best[0]:
    best=(score,[a,b,c]);print('CAPE_BEST',best,vals,flush=True)
print('CAPE_RESULT',best,flush=True)
(p/'work/cape_ground_solve.json').write_text(json.dumps({'best':best,'core_min':core})+'\n')
