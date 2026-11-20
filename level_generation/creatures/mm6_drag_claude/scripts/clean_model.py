import bpy,bmesh,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/static_v1.blend'));o=bpy.data.objects['Body'];me=o.data
parts=np.array([v.value for v in me.attributes['part'].data]);bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table()
# Part 39 is the detached bridge between two tail spines, not a spike.
bmesh.ops.delete(bm,geom=[v for v in bm.verts if parts[v.index]==39],context='VERTS');bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
parts=np.array([v.value for v in me.attributes['part'].data]);changed=0
for v,part in zip(me.vertices,parts):
 x,y,z=v.co
 # Open the fins laterally; the generated membranes were almost sagittal.
 if part in (1,2) or (part==0 and z>.818 and y>-.315 and abs(x)>.023):
  w=1 if part in (1,2) else min(1,max(0,(z-.818)/.045))*min(1,max(0,(y+.315)/.04))
  s=1 if x>0 else -1;dx=abs(x)-.028;dy=y+.31;a=math.radians(67)*w
  v.co.x=s*(.028+dx*math.cos(a)+dy*math.sin(a));v.co.y=-.31-dx*math.sin(a)+dy*math.cos(a);changed+=1
for f in me.polygons:f.use_smooth=True
co=np.array([v.co[:] for v in me.vertices]);me.calc_loop_triangles();np.savez(P/'work/geometry.npz',co=co,parts=parts,edges=np.array([e.vertices[:] for e in me.edges]),tri=np.array([t.vertices[:] for t in me.loop_triangles]))
(P/'work/cleanup.json').write_text(json.dumps({'removed_bridge_part':39,'fin_vertices_adjusted':changed,'triangles':len(me.loop_triangles)},indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/clean_v1.blend'))
sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='SINGLE';sc.display.shading.single_color=(.62,.66,.64);sc.display.shading.show_cavity=True;sc.render.resolution_x=1000;sc.render.resolution_y=1000;sc.render.resolution_percentage=100
cam=bpy.data.objects.new('Camera',bpy.data.cameras.new('Camera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=1.18
for name,offset,target,size in [('front',(0,-5,0),(0,0,.5),1.18),('side',(5,0,0),(0,0,.5),1.18),('quarter',(3,-5,1),(0,0,.5),1.18),('head',(3,-5,1),(0,-.32,.85),.4)]:
 target=Vector(target);cam.location=target+Vector(offset);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=size;sc.render.filepath=str(P/'review'/f'clean_{name}.png');bpy.ops.render.render(write_still=True)
