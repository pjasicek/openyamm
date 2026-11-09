import bpy,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_master.blend'));body=bpy.data.objects['Body'];sc=bpy.context.scene
for i,c in enumerate([(1,.08,.04,1),(.05,.8,.15,1),(.05,.2,1,1)]):body.data.materials[i].diffuse_color=c
sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='MATERIAL';sc.display.shading.show_cavity=True;sc.render.resolution_x=sc.render.resolution_y=800;sc.render.resolution_percentage=100
cam=bpy.data.objects.new('Camera',bpy.data.cameras.new('Camera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=.68;cam.location=(0,4,1.50);cam.rotation_euler=(Vector((0,.1,1.50))-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(P/'review/head_set_boundary.png');bpy.ops.render.render(write_still=True)
tree=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get());out=[]
for j in range(41):
 z=1.27+j*.01;hit,normal,fi,d=tree.ray_cast(Vector((-.01,2,z)),Vector((0,-1,0)))
 if hit is not None:out.append({'z':round(z,3),'y':round(hit.y,4),'material':body.data.polygons[fi].material_index,'face':fi})
(P/'work/head_set_boundary.json').write_text(json.dumps(out,indent=2));print(out,flush=True)
