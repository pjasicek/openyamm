import bpy,sys,numpy as np,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_common as C
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round3/master.blend'));relaxed=[v.co.copy()for v in bpy.data.objects['Body'].data.vertices]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round3/before_shoulder_field.blend'));C.reset();o=bpy.data.objects['Body'];pv=[a.value for a in o.data.attributes['piece'].data]
for v,c in zip(o.data.vertices,relaxed):
 if pv[v.index]==1:v.co=c
me=o.data;me.calc_loop_triangles();tri=[tuple(t.vertices)for t in me.loop_triangles if all(pv[i]==2 for i in t.vertices)];co=[v.co.copy()for v in me.vertices];tree=BVHTree.FromPolygons(co,tri,all_triangles=True);changed=[]
for v in me.vertices:
 if pv[v.index]not in [6,7]or v.co.z<.20:continue
 amount=float(np.clip((v.co.z-.20)/.16,0,1));amount=amount*amount*(3-2*amount);point,n,fi,d=tree.find_nearest(v.co);vs=tri[fi];bary=barycentric_transform(point,*[co[i]for i in vs],Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)));w={g.group:g.weight*(1-amount)for g in v.groups}
 for i,k in zip(vs,bary):
  for g in me.vertices[i].groups:w[g.group]=w.get(g.group,0)+amount*max(0,k)*g.weight
 for g in list(v.groups):o.vertex_groups[g.group].remove([v.index])
 ws=sorted(w.items(),key=lambda x:-x[1])[:4];total=sum(x for _,x in ws)
 for gi,x in ws:
  if x>1e-8:o.vertex_groups[gi].add([v.index],x/total,'REPLACE')
 changed.append(v.index)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round3/master.blend'));(P/'review/round3/covered_leg_weights.json').write_text(json.dumps({'vertices':len(changed),'method':'Covered upper boot/pants vertices share the overlying skirt skin field; full geometry retained. Smooth 0.20–0.36 m ankle transition preserves sole weights. This prevents independent hidden-leg motion crossing the garment.'},indent=2))
