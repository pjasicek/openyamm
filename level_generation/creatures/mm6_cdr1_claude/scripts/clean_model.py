import bpy,bmesh,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/static_v1.blend'));o=bpy.data.objects['Body'];me=o.data
bm=bmesh.new();bm.from_mesh(me);bad=[]
for f in bm.faces:
 lengths=[e.calc_length() for e in f.edges];long=max(lengths)
 if long>.15 and f.calc_area()/long**2<.015:bad.append(f)
print('REMOVED_BRIDGE_FACES',len(bad));assert 0<len(bad)<100
bmesh.ops.delete(bm,geom=bad,context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bmesh.ops.dissolve_degenerate(bm,dist=1e-7,edges=list(bm.edges));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
for v in me.vertices:
 x,y,z=v.co
 # Recenter the head/body midline; shorten only the tail past the haunches.
 x+=float(np.interp(y,[-.5,-.35,-.08,.2,.5],[.005,.003,.001,0,-.0005]))
 if y>-.08:y=-.08+(y+.08)*.64
 # Enlarge the skull through a smooth neck transition, retaining the continuous skin.
 w=max(0,min(1,(-y-.36)/.065));w=w*w*(3-2*w)
 pivot=Vector((0,-.43,.31));v.co=(Vector((x,y,z))-pivot)*(1+.32*w)+pivot
 v.co*=3
# The native anatomy is bilateral; the positive half has intact wing topology and no head-wing needles.
bm=bmesh.new();bm.from_mesh(me);bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-6,plane_co=(0,0,0),plane_no=(1,0,0),clear_inner=True,clear_outer=False);bm.to_mesh(me);bm.free()
bpy.context.view_layer.objects.active=o;mod=o.modifiers.new('RepairBilateral','MIRROR');mod.use_clip=True;mod.use_mirror_merge=True;mod.merge_threshold=.001;bpy.ops.object.modifier_apply(modifier=mod.name)
co=np.array([v.co[:] for v in me.vertices]);me.calc_loop_triangles();np.savez(P/'work/geometry.npz',co=co,parts=np.array([a.value for a in me.attributes['part'].data]),edges=np.array([e.vertices[:] for e in me.edges]),tri=np.array([t.vertices[:] for t in me.loop_triangles]))
(P/'work/cleanup.json').write_text(json.dumps({'removed_bridge_faces':len(bad),'triangles':len(me.loop_triangles),'bounds':[co.min(0).tolist(),co.max(0).tolist()]},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/clean_v1.blend'))
sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='SINGLE';sc.display.shading.single_color=(.64,.68,.65);sc.display.shading.show_cavity=True;sc.display.shading.show_shadows=False;sc.render.resolution_x=1200;sc.render.resolution_y=900;sc.render.resolution_percentage=100
cam=bpy.data.objects.new('Camera',bpy.data.cameras.new('Camera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO';center=(co.min(0)+co.max(0))/2
for name,offset,target,size in [('front',(0,-6,0),center,3.6),('side',(6,0,0),center,3.8),('top',(0,0,6),center,4.3),('quarter',(4,-6,2),center,3.6),('head',(2,-5,1),(0,-1.36,.96),.7)]:
 target=Vector(target);cam.location=target+Vector(offset);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=size;sc.render.filepath=str(P/'review'/f'clean_{name}.png');bpy.ops.render.render(write_still=True)
print('CLEAN',len(me.loop_triangles),co.min(0),co.max(0))
