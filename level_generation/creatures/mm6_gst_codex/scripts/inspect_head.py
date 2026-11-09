"""Inspect the separate skull/cowl detail model before fitting it to the body."""
import bpy,bmesh,json,sys
import numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parent/'mm6_bar1_claude/scripts'));import common
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(P/'meshy/head_geometry_v1/model_urls_glb.glb'))
objs=[o for o in bpy.context.scene.objects if o.type=='MESH']
bpy.ops.object.select_all(action='DESELECT')
for o in objs:o.select_set(True)
bpy.context.view_layer.objects.active=objs[0];bpy.ops.object.join()
o=bpy.context.object;o.name=o.data.name='HeadDetail'
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
co=np.array([v.co[:] for v in o.data.vertices]);s=.44/np.ptp(co[:,2])
for v in o.data.vertices:v.co*=s
co=np.array([v.co[:] for v in o.data.vertices]);shift=np.array([-(co[:,0].min()+co[:,0].max())/2,-co[:,1].min()-.13,1.79-co[:,2].min()])
for v in o.data.vertices:v.co+=Vector(shift)
for f in o.data.polygons:f.use_smooth=True
bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6);bm.to_mesh(o.data);bm.free()
co=np.array([v.co[:] for v in o.data.vertices]);adj=[[] for _ in co]
for e in o.data.edges:
 a,b=e.vertices;adj[a].append(b);adj[b].append(a)
seen=set();parts=[];labels=np.full(len(co),-1)
for i in range(len(co)):
 if i in seen:continue
 todo=[i];seen.add(i);ids=[]
 while todo:
  a=todo.pop();ids.append(a)
  for b in adj[a]:
   if b not in seen:seen.add(b);todo.append(b)
 c=co[ids];idx=len(parts);labels[ids]=idx;parts.append({'part':idx,'verts':len(ids),'min':c.min(0).tolist(),'max':c.max(0).tolist(),'mean':c.mean(0).tolist()})
attr=o.data.attributes.new('part','INT','POINT');attr.data.foreach_set('value',labels)
o.data.calc_loop_triangles()
(P/'work/head_geometry.json').write_text(json.dumps({'triangles':len(o.data.loop_triangles),'components':parts},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/head_detail.blend'))
common.workbench_clay(bpy.context.scene)
common.render_views(str(P/'review/head_detail'),2.02,.56,views=('front','left','three_quarter','back'),resolution=(700,700),target=(0,.07))
print('HEAD_DETAIL',len(o.data.loop_triangles),'triangles',len(parts),'components')
