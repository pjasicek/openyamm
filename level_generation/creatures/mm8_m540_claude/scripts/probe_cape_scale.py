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

act=bpy.data.actions['Death'];pose=sample(act,39);apply(pose);pts=coords(body);core=min(v.z for i,v in enumerate(pts) if skin[i]);surface=BVHTree.FromPolygons(pts,faces)

from mathutils import Matrix
base={n:rig.pose.bones[n].matrix.copy() for n in ['Cape0','Cape1','Cape2']}
for factor in [.01,.05,.1,.2]:
 apply(pose);plane=core-.012;M=Matrix.Translation((0,0,plane))@Matrix.Diagonal((1,1,factor,1))@Matrix.Translation((0,0,-plane))
 for n in base:rig.pose.bones[n].matrix=M@base[n];bpy.context.view_layer.update()
 pts=coords(body);low=min(v.z for i,v in enumerate(pts) if cape[i]);high=max(v.z for i,v in enumerate(pts) if cape[i]);depth=0
 for i in np.flatnonzero(cape):
  loc,n,fi,d=surface.find_nearest(pts[i],.1)
  if loc is not None and (pts[i]-loc).dot(n)<-.7*d:depth=max(depth,d)
 print('FLAT_SCALE',factor,low,high,depth,[(n,list(rig.pose.bones[n].scale)) for n in base],flush=True)
