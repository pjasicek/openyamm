import bpy
import bmesh
import json
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'body_v3.blend'))
body=bpy.data.objects['Lizardman_Body']
bm=bmesh.new(); bm.from_mesh(body.data)
before={'vertices':len(bm.verts),'faces':len(bm.faces),'boundaries':sum(e.is_boundary for e in bm.edges)}
# The GLB split coincident vertices at UV seams. Join only exact coincident chart copies;
# per-corner UVs remain on their original loops. This is not anatomical hole filling.
bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
after={'vertices':len(bm.verts),'faces':len(bm.faces),'boundaries':sum(e.is_boundary for e in bm.edges),'degenerate_faces':sum(f.calc_area()<1e-12 for f in bm.faces)}
bm.to_mesh(body.data); bm.free()
for p in body.data.polygons:p.use_smooth=True
if body.data.has_custom_normals:body.data.normals_split_custom_set([(0,0,0)]*len(body.data.loops))
body.data.update()
scene=bpy.context.scene; camera=scene.camera
scene.render.engine='BLENDER_WORKBENCH'
scene.display.shading.color_type='SINGLE';scene.display.shading.single_color=(.6,.6,.6)
scene.render.resolution_x=scene.render.resolution_y=700
review=ROOT/'body_review_v4';review.mkdir(exist_ok=True)
for name,center,direction,scale in [('profile',(0,0,.85),(-5,0,0),1.95),('front',(0,0,.85),(0,-5,0),1.95),('hand_right',(-.42,-.01,.78),(0,-5,0),.42),('hand_left',(.42,-.01,.78),(0,-5,0),.42),('feet',(0,0,.14),(0,-5,0),.85)]:
    center=Vector(center);camera.location=center+Vector(direction)
    camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=scale
    scene.render.filepath=str(review/f'clay_{name}.png');bpy.ops.render.render(write_still=True)
for o in scene.objects:o.select_set(False)
body.select_set(True);bpy.context.view_layer.objects.active=body
bpy.ops.export_scene.gltf(filepath=str(ROOT/'body_for_rig_v4.glb'),export_format='GLB',use_selection=True,export_animations=False,export_materials='EXPORT')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'body_v4.blend'))
(review/'repair.json').write_text(json.dumps({'before':before,'after':after,'operation':'Only coincident UV chart vertices joined and winding recalculated; no decimation or limb remodeling.'},indent=2))
(ROOT/'requests/body_rig_v1.json').write_text(json.dumps({'model_url':'@file:3d_20261006/body_for_rig_v4.glb','height_meters':1.7},indent=2))
print(json.dumps({'before':before,'after':after}),flush=True)
