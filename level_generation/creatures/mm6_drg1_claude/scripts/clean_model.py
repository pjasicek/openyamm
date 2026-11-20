import bpy,bmesh,json,sys
import numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/static_v1.blend'));o=bpy.data.objects['Body'];me=o.data
bm=bmesh.new();bm.from_mesh(me);bad=[]
for f in bm.faces:
 lengths=[e.calc_length() for e in f.edges];c=f.calc_center_median();long=max(lengths)
 if (abs(c.x)<.08 and c.y<-.35 and long>.055 and f.calc_area()/long**2<.06) or (abs(c.x)<.025 and c.y<-.432 and .115<c.z<.208) or (abs(c.x)<.024 and c.y<-.416 and .026<c.z<.080):bad.append(f)
print('BAD_BRIDGES',len(bad));bmesh.ops.delete(bm,geom=bad,context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bmesh.ops.dissolve_degenerate(bm,dist=1e-7,edges=list(bm.edges));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
# Restore native silhouette proportions: compact tail and less oversized wings.
for v in me.vertices:
 x,y,z=v.co
 if y>-.26:y=-.26+(y+.26)*.55
 if abs(x+.006)>.05:x=-.006+np.sign(x+.006)*(.05+(abs(x+.006)-.05)*.86)
 v.co=((x+.006)*3,(y+.30)*3,z*3)
co=np.array([v.co[:] for v in me.vertices]);me.calc_loop_triangles();np.savez(P/'work/geometry.npz',co=co,parts=np.array([a.value for a in me.attributes['part'].data]),edges=np.array([e.vertices[:] for e in me.edges]),tri=np.array([t.vertices[:] for t in me.loop_triangles]))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/clean_v1.blend'));print('CLEAN',len(me.loop_triangles),co.min(0),co.max(0))
sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='SINGLE';sc.display.shading.single_color=(.64,.68,.65);sc.display.shading.show_cavity=True;sc.display.shading.show_shadows=False;sc.render.resolution_x=1200;sc.render.resolution_y=900;sc.render.resolution_percentage=100
cam=bpy.data.objects.new('Camera',bpy.data.cameras.new('Camera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO'
for name,loc,target,size in [('front',(0,-6,.45),(0,0,.45),3.1),('side',(6,0,.45),(0,.18,.45),2.7),('three_quarter',(4,-6,2),(0,.15,.45),3.4),('head',(2,-5,1.1),(0,-.385,.70),.32)]:
 cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=size;sc.render.filepath=str(P/'review'/f'clean_{name}.png');bpy.ops.render.render(write_still=True)
