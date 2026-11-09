import bpy,json,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round2_head_lod0.blend'));b=bpy.data.objects['Body'];me=b.data
faces=[list(f.vertices) for f in me.polygons];tree=BVHTree.FromPolygons([v.co for v in me.vertices],faces,all_triangles=True)
for x,z in [(-.075,1.49),(.075,1.49),(-.050,1.42),(-.08,1.48),(-.065,1.49),(-.06,1.42)]:
 loc,n,i,d=tree.ray_cast(Vector((x,-6,z)),Vector((0,1,0)));f=me.polygons[i];c=sum((me.vertices[v].co for v in f.vertices),Vector())/3;uv=barycentric_transform(loc,*[me.vertices[v].co for v in f.vertices],*[Vector((*me.uv_layers['MergedUV'].data[l].uv,0)) for l in f.loop_indices]);print('PATCH',x,z,'hit',list(loc),'centroid',list(c),'material',me.materials[f.material_index].name,'uv',list(uv),flush=True)
