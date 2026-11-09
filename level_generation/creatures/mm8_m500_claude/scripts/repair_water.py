"""Keep the first body, fit the single-crest second head, and orient the caudal fin vertically."""
import bpy,bmesh,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/v1_step1.blend'))
body=bpy.data.objects['Body'];bm=bmesh.new();bm.from_mesh(body.data)
part=bm.verts.layers.int.get('part')
bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[part]==4],context='VERTS')
region=[v for v in bm.verts if v.co.y<.65]
region+= [e for e in bm.edges if all(v.co.y<.65 for v in e.verts)]
region+= [f for f in bm.faces if all(v.co.y<.65 for v in f.verts)]
bmesh.ops.bisect_plane(bm,geom=region,dist=1e-6,plane_co=(0,0,1.55),plane_no=(0,0,1),clear_outer=True)
# The returned fan is across the back; its upright stalk permits a quarter-turn into the sagittal plane.
for v in bm.verts:
 if v.co.y>1.65 and v.co.z>.55:
  u=min(1,max(0,(v.co.z-.55)/.45));u=u*u*(3-2*u)
  pivot=Vector((0,2.05,.55));v.co=pivot+Matrix.Rotation(math.pi/2*u,3,'Z')@(v.co-pivot)
  v.co.z=.55+(v.co.z-.55)*.65
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(body.data);bm.free()
with bpy.data.libraries.load(str(P/'work/step1.blend'),link=False) as (src,dst):dst.objects=['Body']
head=dst.objects[0];bpy.context.collection.objects.link(head);head.name='SelectedHead'
bm=bmesh.new();bm.from_mesh(head.data)
bmesh.ops.delete(bm,geom=[v for v in bm.verts if v.co.x<.1 or v.co.x>.85 or v.co.y>.45],context='VERTS')
bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-6,plane_co=(0,0,1.60),plane_no=(0,0,1),clear_inner=True)
for v in bm.verts:v.co+=Vector((-.492,-.015,-.03))
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(head.data);bm.free()
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);head.select_set(True);bpy.context.view_layer.objects.active=body;bpy.ops.object.join()
bm=bmesh.new();bm.from_mesh(body.data)
seam=[e for e in bm.edges if e.is_boundary and all(abs(v.co.z-1.55)<1e-4 or abs(v.co.z-1.57)<1e-4 for v in e.verts) and all(v.co.y<.3 for v in e.verts)]
assert len(seam)>6,len(seam)
result=bmesh.ops.bridge_loops(bm,edges=seam,use_pairs=True)
assert len(result['faces'])>3,len(result['faces'])
neck=[v for v in bm.verts if 1.49<v.co.z<1.63 and v.co.y<.15]
for _ in range(4):bmesh.ops.smooth_vert(bm,verts=neck,factor=.35,use_axis_x=True,use_axis_y=True,use_axis_z=True)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(body.data);bm.free()
body.data.normals_split_custom_set([(0,0,0)]*len(body.data.loops))
body.data.materials.clear();m=bpy.data.materials.new('WaterClay');m.diffuse_color=(.48,.53,.55,1);body.data.materials.append(m)
for f in body.data.polygons:f.use_smooth=True;f.material_index=0
co=np.array([v.co[:] for v in body.data.vertices]);edges=np.array([e.vertices[:] for e in body.data.edges]);body.data.calc_loop_triangles();tri=np.array([t.vertices[:] for t in body.data.loop_triangles])
np.savez(P/'work/geometry_repaired.npz',co=co,edges=edges,tri=tri)
assert np.isfinite(co).all()
(P/'work/geometry_repaired.json').write_text(json.dumps({'vertices':len(co),'triangles':len(tri),'bbox':[co.min(0).tolist(),co.max(0).tolist()],'neck_bridge_faces':len(result['faces']),'sources':['body_geometry_v1 body','body_geometry_v2 head'],'repairs':['discard floating fin fragment','single medial crest head','sagittal caudal fan','recalculate geometric normals']},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/geometry_repaired.blend'))
sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.color_type='MATERIAL';sc.display.shading.light='STUDIO';sc.display.shading.show_cavity=True;sc.display.shading.show_shadows=False
sc.world=bpy.data.worlds.new('ReviewWorld');sc.world.color=(.15,.15,.15);sc.render.resolution_x=sc.render.resolution_y=800;sc.render.resolution_percentage=100
cam=bpy.data.objects.new('ReviewCamera',bpy.data.cameras.new('ReviewCamera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO'
for name,pos,target,scale in [('front',(0,-6,1.1),(0,0,1.1),2.4),('side',(6,1.3,1.0),(0,1.3,1.0),3.9),('quarter',(4,-6,3),(0,.65,1),3.4),('back',(0,6,1.1),(0,0,1.1),2.4),('head',(2,-5,2.2),(0,0,1.77),.7)]:
 cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;sc.render.filepath=str(P/'review'/f'repaired_{name}.png');bpy.ops.render.render(write_still=True)
