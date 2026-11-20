import bpy,sys,os,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
P=Path(__file__).resolve().parents[1];path=P/'work/addons_v2/equipped.blend';bpy.ops.wm.open_mainfile(filepath=str(path));r=bpy.data.objects['Rig'];b=bpy.data.objects['Kept'];r.animation_data.action=None
for p in r.pose.bones:p.matrix_basis.identity()
co=[v.co.copy() for v in b.data.vertices];pc=[a.value for a in b.data.attributes['piece'].data];fs=[p.vertices[:] for p in b.data.polygons if pc[p.vertices[0]]==0];tree=BVHTree.FromPolygons(co,fs);count=0
for v in b.data.vertices:
 if pc[v.index]!=1 or v.co.z>=1.43:continue
 t=min(1,(1.43-v.co.z)/.025);h,n,i,d=tree.find_nearest(v.co);ids=fs[i];w=barycentric_transform(h,*[co[j] for j in ids],Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)));acc={g.group:g.weight*(1-t) for g in v.groups}
 for j,f in zip(ids,w):
  for g in b.data.vertices[j].groups:acc[g.group]=acc.get(g.group,0)+max(0,f)*g.weight*t
 for g in list(v.groups):b.vertex_groups[g.group].remove([v.index])
 acc=sorted(acc.items(),key=lambda p:-p[1])[:8];total=sum(w for k,w in acc)
 for k,w in acc:
  if w>1e-8:b.vertex_groups[k].add([v.index],w/total,'REPLACE')
 count+=1
# 2 mm covers the chords between liner vertices without a visible floating band.
for v in bpy.data.objects['hes_kept_collar'].data.vertices:
 p=v.co;rad=Vector((p.x+.03255,p.y-.034,0));p+=rad.normalized()*.002
bpy.ops.wm.save_as_mainfile(filepath=str(path));print('HIDDEN_CHEST_NECK',count,flush=True);sys.stdout.flush();sys.stderr.flush();os._exit(0)
