"""Keep the collar's rigid skin band local to the neck; lateral shoulder skin follows the shirt beneath the straps."""
import bpy,sys,os,math,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
P=Path(__file__).resolve().parents[1];path=P/'work/addons_v2/equipped.blend';bpy.ops.wm.open_mainfile(filepath=str(path));r=bpy.data.objects['Rig'];b=bpy.data.objects['Kept'];r.animation_data.action=None
for p in r.pose.bones:p.matrix_basis.identity()
co=[v.co.copy()for v in b.data.vertices];pc=[v.value for v in b.data.attributes['piece'].data];fs=[p.vertices[:]for p in b.data.polygons if pc[p.vertices[0]]==0];tree=BVHTree.FromPolygons(co,fs);count=0
for v in b.data.vertices:
 if pc[v.index]!=1 or not 1.38-1e-6<=v.co.z<=1.505+1e-6:continue
 rho=math.hypot((v.co.x+.03255)/.105,(v.co.y-.034)/.12);t=max(0,min(1,(rho-1)/.2))
 if not t:continue
 h,n,j,d=tree.find_nearest(v.co);ids=fs[j];w=barycentric_transform(h,*[co[i]for i in ids],Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)));acc={g.group:g.weight*(1-t)for g in v.groups}
 for i,f in zip(ids,w):
  for g in b.data.vertices[i].groups:acc[g.group]=acc.get(g.group,0)+max(0,f)*g.weight*t
 for g in list(v.groups):b.vertex_groups[g.group].remove([v.index])
 acc=sorted(acc.items(),key=lambda p:-p[1])[:8];total=sum(w for k,w in acc)
 for k,w in acc:
  if w>1e-8:b.vertex_groups[k].add([v.index],w/total,'REPLACE')
 count+=1
bpy.ops.wm.save_as_mainfile(filepath=str(path));print('SHOULDER_NECK_WEIGHTS',count,flush=True);sys.stdout.flush();sys.stderr.flush();os._exit(0)
