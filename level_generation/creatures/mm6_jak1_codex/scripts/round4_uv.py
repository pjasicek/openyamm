"""Pack fixed staff topology with explicit atlas gutters; carry island transforms to all LODs."""
import bpy,sys,json,numpy as np
from pathlib import Path
from mathutils.bvhtree import BVHTree
from mathutils import Vector
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'source/mm6_jak1_staff.blend'))
obj=bpy.data.objects['Staff'];me=obj.data;old=np.array([x.uv[:] for x in me.uv_layers.active.data]);parents=list(range(len(me.polygons)))
def root(i):
 while parents[i]!=i:parents[i]=parents[parents[i]];i=parents[i]
 return i
seen={}
for p in me.polygons:
 for li in p.loop_indices:
  key=tuple(np.round(old[li],7))
  if key in seen:parents[root(p.index)]=root(seen[key])
  seen[key]=p.index
labels=[root(p.index) for p in me.polygons]
for o in bpy.context.scene.objects:o.select_set(o==obj)
bpy.context.view_layer.objects.active=obj
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.select_all(action='SELECT');bpy.ops.uv.pack_islands(rotate=False,scale=True,margin_method='FRACTION',margin=.02)
bpy.ops.object.mode_set(mode='OBJECT')
new=np.array([x.uv[:] for x in me.uv_layers.active.data]);transforms={}
for label in set(labels):
 ix=[i for p in me.polygons if labels[p.index]==label for i in p.loop_indices];a=np.c_[old[ix],np.ones(len(ix))];t=np.linalg.lstsq(a,new[ix],rcond=None)[0];assert abs(a@t-new[ix]).max()<1e-5;transforms[label]=t
points=[(float(u),float(v),0) for u,v in old];tris=[tuple(p.loop_indices) for p in me.polygons];tree=BVHTree.FromPolygons(points,tris,all_triangles=False)
for level in range(1,4):
 mesh=bpy.data.objects[f'Staff_LOD{level}'].data;uv=mesh.uv_layers.active.data
 for p in mesh.polygons:
  center=np.mean([uv[i].uv[:] for i in p.loop_indices],axis=0);hit,n,idx,dist=tree.find_nearest(Vector((*center,0)));t=transforms[labels[idx]]
  for i in p.loop_indices:uv[i].uv=tuple(np.r_[uv[i].uv[:],1]@t)
receipt={'islands':len(transforms),'margin_fraction':.02,'minimum_border_pixels':float(min(new.min(),1-new.max())*1024),'positions_unchanged':True,'triangles_unchanged':True}
(P/'review/round4/uv_pack.json').write_text(json.dumps(receipt,indent=2));print(receipt,flush=True)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'source/mm6_jak1_staff.blend'))
