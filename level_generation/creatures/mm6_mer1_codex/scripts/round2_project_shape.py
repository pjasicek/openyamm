import bpy,sys,json,numpy as np
from collections import Counter
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common,reduction_common as C
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round2/master.blend'));C.reset();hi=bpy.data.objects['Body'].data;hi.calc_loop_triangles();co=[v.co.copy()for v in hi.vertices];ns=[v.normal.copy()for v in hi.vertices];part=[a.value for a in hi.attributes['piece'].data];trees={};axis=[Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1))]
for pid in set(part):
 tris=[tuple(t.vertices)for t in hi.loop_triangles if Counter(part[i]for i in t.vertices).most_common(1)[0][0]==pid];trees[pid]=(BVHTree.FromPolygons(co,tris,all_triangles=True),tris)
for level in range(4):
 path=P/f'work/round2/body_lod{level}.blend';bpy.ops.wm.open_mainfile(filepath=str(path));C.reset();o=bpy.data.objects['Body'];out=[]
 for v in o.data.vertices:
  tree,tris=trees[o.data.attributes['piece'].data[v.index].value];loc,n,i,d=tree.find_nearest(v.co);vs=tris[i];w=barycentric_transform(loc,*[co[j]for j in vs],*axis);N=sum((ns[j]*q for j,q in zip(vs,w)),Vector()).normalized();out.append(N);v.co=loc
 o.data.normals_split_custom_set_from_vertices(out);bpy.ops.wm.save_as_mainfile(filepath=str(path))
 if level==0:
  common.workbench_clay(bpy.context.scene);bpy.context.scene.display.shading.color_type='SINGLE';bpy.context.scene.display.shading.single_color=(.3,.5,.3);common.render_views(str(P/'review/round2/projected_rest'),1.2,1.4,views=('front','left'),resolution=(650,800));C.activate('Attack',.4);common.render_views(str(P/'review/round2/projected_attack'),1.2,1.4,views=('front','left'),resolution=(650,800))
