from pathlib import Path
import bpy,json,sys,runpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v13.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];me=body.data
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
piece=[x.value for x in me.attributes['piece'].data];faces=[tuple(f.vertices) for f in me.polygons if all(piece[i]==0 for i in f.vertices)];tree=BVHTree.FromPolygons([v.co for v in me.vertices],faces)
for v in me.vertices:
 if piece[v.index]!=14:continue
 loc,n,fi,d=tree.find_nearest(v.co);tri=faces[fi];assert len(tri)==3
 bc=barycentric_transform(loc,*[me.vertices[i].co for i in tri],Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)));weights={}
 for i,w in zip(tri,bc):
  for g in me.vertices[i].groups:weights[g.group]=weights.get(g.group,0)+g.weight*max(w,0)
 for g in body.vertex_groups:g.remove([v.index])
 total=sum(weights.values())
 for gi,w in weights.items():
  if w>1e-6:body.vertex_groups[gi].add([v.index],w/total,'REPLACE')
me.update();bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_v13c.blend'))
# Reuse the conservative rest-shape fitter with the transferred skin weights.
s=(p/'scripts/review2_cloth_fit.py').read_text().replace("rig_v13.blend","rig_v13c.blend")
exec(compile(s,str(p/'scripts/review2_cloth_fit.py'),'exec'),globals())
