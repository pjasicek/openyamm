import bpy,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_uv.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];pa=np.array([a.value for a in body.data.attributes['part'].data]);body.data.materials.clear()
for n,c in [('Torso',(.8,.15,.15,1)),('Arms',(.1,.7,.15,1)),('Other',(.4,.4,.4,1))]:
 m=bpy.data.materials.new(n);m.diffuse_color=c;body.data.materials.append(m)
for f in body.data.polygons:f.material_index=0 if pa[f.vertices[0]]==0 else 1 if pa[f.vertices[0]] in [6,9] else 2
sc=bpy.context.scene;rig.animation_data.action=bpy.data.actions['Standing'];sc.frame_set(1);sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='MATERIAL';sc.display.shading.show_cavity=True;sc.render.resolution_x=sc.render.resolution_y=900;sc.render.resolution_percentage=100;cam=bpy.data.objects.new('C',bpy.data.cameras.new('C'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=.7;cam.location=(0,-5,1.63);cam.rotation_euler=(Vector((0,0,1.63))-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(P/'review/shoulder_parts.png');bpy.ops.render.render(write_still=True)
