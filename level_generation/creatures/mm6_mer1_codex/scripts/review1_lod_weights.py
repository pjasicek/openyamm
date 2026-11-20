import bpy,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
P=Path(__file__).resolve().parents[1];sel=json.loads((P/'review/reduction/selection.json').read_text());axes=[Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1))]
for e in sel['body'][1:3]:
 path=P/e['blend'];bpy.ops.wm.open_mainfile(filepath=str(path));o=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];parts=[a.value for a in o.data.attributes['piece'].data]
 with bpy.data.libraries.load(str(P/sel['body'][0]['blend']),link=False)as(src,dst):dst.objects=['Body']
 hi=dst.objects[0];hi.data.calc_loop_triangles();hp=[a.value for a in hi.data.attributes['piece'].data];co=[v.co.copy()for v in hi.data.vertices]
 for pid in [8,9]:
  tris=[t for t in hi.data.loop_triangles if all(hp[i]==pid for i in t.vertices)];tree=BVHTree.FromPolygons(co,[t.vertices[:]for t in tris],all_triangles=True)
  for v in o.data.vertices:
   if parts[v.index]!=pid:continue
   hit,n,fi,dist=tree.find_nearest(v.co);assert dist<.045,(pid,dist);t=tris[fi];w=barycentric_transform(hit,*[co[i]for i in t.vertices],*axes);weights={}
   for vi,a in zip(t.vertices,w):
    for g in hi.data.vertices[vi].groups:
     name=hi.vertex_groups[g.group].name
     if name in rig.data.bones:weights[name]=weights.get(name,0)+max(0,a)*g.weight
   total=sum(weights.values());assert total>0
   for g in list(v.groups):o.vertex_groups[g.group].remove([v.index])
   for name,value in weights.items():
    if value>1e-8:o.vertex_groups[name].add([v.index],value/total,'REPLACE')
 bpy.data.objects.remove(hi,do_unlink=True);bpy.ops.wm.save_as_mainfile(filepath=str(path))
