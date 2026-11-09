"""Copy the final underlying skin weights to the fitted breastplate and harness."""
import bpy,sys,os
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
P=Path(__file__).resolve().parents[1];path=P/'work/addons_v2/equipped.blend';bpy.ops.wm.open_mainfile(filepath=str(path));r=bpy.data.objects['Rig'];b=bpy.data.objects['Kept'];r.animation_data.action=None
for p in r.pose.bones:p.matrix_basis.identity()
co=[v.co.copy()for v in b.data.vertices];pc=[v.value for v in b.data.attributes['piece'].data];faces=[p.vertices[:]for p in b.data.polygons];head=[f for f in faces if pc[f[0]]==1];alltree=BVHTree.FromPolygons(co,faces);headtree=BVHTree.FromPolygons(co,head);o=bpy.data.objects['hes_kept_plate'];o.vertex_groups.clear()
for g in b.vertex_groups:o.vertex_groups.new(name=g.name)
for v in o.data.vertices:
 usehead=v.co.z>1.32 and v.co.y<.01 and abs(v.co.x+.03255)<.13;tree=headtree if usehead else alltree;fs=head if usehead else faces;hit,n,ix,d=tree.find_nearest(v.co);ids=fs[ix];w=barycentric_transform(hit,*[co[i]for i in ids],Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)));acc={}
 for i,f in zip(ids,w):
  for g in b.data.vertices[i].groups:acc[g.group]=acc.get(g.group,0)+max(0,f)*g.weight
 acc=sorted(acc.items(),key=lambda p:-p[1])[:8];total=sum(w for k,w in acc)
 for k,w in acc:
  if w>1e-8:o.vertex_groups[k].add([v.index],w/total,'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=str(path));sys.stdout.flush();sys.stderr.flush();os._exit(0)
