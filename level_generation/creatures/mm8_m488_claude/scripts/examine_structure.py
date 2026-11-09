from pathlib import Path
import sys,json,bpy,bmesh,numpy as np
sys.path.insert(0,str(Path(__file__).parent));import common
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/imported.blend'))
ob=bpy.data.objects['Body'];me=ob.data
labels=np.array([d.value for d in me.attributes['piece'].data]);report=[]
bm=bmesh.new();bm.from_mesh(me)
seen=set()
for e in bm.edges:
 if not e.is_boundary or e in seen:continue
 stack=[e];edges=set()
 while stack:
  t=stack.pop()
  if t in edges:continue
  edges.add(t);seen.add(t)
  stack.extend(q for v in t.verts for q in v.link_edges if q.is_boundary and q not in edges)
 vs=list({v for e in edges for v in e.verts});co=np.array([v.co[:] for v in vs])
 report.append({'piece':int(labels[vs[0].index]),'vertices':[v.index for v in vs],'coordinates':co.tolist(),'min':co.min(0).tolist(),'max':co.max(0).tolist(),'count':len(vs)})
(p/'review/geometry/boundaries.json').write_text(json.dumps(report,indent=2))
print('BOUNDARIES',[(x['piece'],x['count'],x['min'],x['max']) for x in report]);bm.free()
for piece in [0,1]:
 copy=ob.copy();copy.data=me.copy();bpy.context.collection.objects.link(copy);ob.hide_render=True;copy.hide_render=False
 bm=bmesh.new();bm.from_mesh(copy.data);bm.verts.ensure_lookup_table()
 bmesh.ops.delete(bm,geom=[v for v in bm.verts if labels[v.index]!=piece],context='VERTS');bm.to_mesh(copy.data);bm.free()
 common.workbench_clay(bpy.context.scene)
 common.render_views(str(p/'review/geometry'/f'piece{piece}'),1.05,2.5,views=('front','left','back'),resolution=(960,960))
 bpy.data.objects.remove(copy,do_unlink=True)

ob.hide_render=False
cam=common.ortho_camera('underside',(0,-4,-1.5),(0,0,0),1.3)
from mathutils import Vector
cam.rotation_euler=(Vector((0,0,0.85))-cam.location).to_track_quat('-Z','Y').to_euler()
bpy.context.scene.camera=cam;bpy.context.scene.render.filepath=str(p/'review/geometry/underside.png');bpy.ops.render.render(write_still=True)
