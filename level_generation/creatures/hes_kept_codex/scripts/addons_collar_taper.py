import bpy,sys,os,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];path=P/'work/addons_v2/equipped.blend';bpy.ops.wm.open_mainfile(filepath=str(path));r=bpy.data.objects['Rig'];b=bpy.data.objects['Kept'];r.animation_data.action=None
for p in r.pose.bones:p.matrix_basis.identity()
co=[v.co.copy() for v in b.data.vertices];pc=[a.value for a in b.data.attributes['piece'].data];t=BVHTree.FromPolygons(co,[p.vertices[:] for p in b.data.polygons if pc[p.vertices[0]]==1]);alltree=BVHTree.FromPolygons(co,[p.vertices[:] for p in b.data.polygons])
def radius(a,z):
 c=Vector((-.03255,.034,z));v=Vector((math.cos(a),math.sin(a),0));hit,n,i,d=t.ray_cast(c+v*.25,-v,.5);assert hit is not None;return (hit-c).dot(v)
for v in bpy.data.objects['hes_kept_collar'].data.vertices:
 p=v.co
 if p.z<1.451:
  a=math.atan2(p.y-.034,p.x+.03255);z=1.451+(p.z-1.451)*.45;dr=radius(a,z)-radius(a,p.z);p.x+=math.cos(a)*dr;p.y+=math.sin(a)*dr;p.z=z
for v in bpy.data.objects['hes_kept_plate'].data.vertices:
 h,n,i,d=alltree.find_nearest(v.co);v.co+=n*.002
bpy.ops.wm.save_as_mainfile(filepath=str(path));sys.stdout.flush();sys.stderr.flush();os._exit(0)
