import bpy
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/step1.blend'))
sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.studiolight_rotate_z=.3;sc.display.shading.show_shadows=True;sc.display.shading.show_cavity=True;sc.display.shading.cavity_type='BOTH';sc.display.shading.color_type='MATERIAL';sc.display.shading.background_type='WORLD';sc.world=bpy.data.worlds.new('World');sc.world.color=(.13,.13,.15)
sc.render.resolution_x=sc.render.resolution_y=800;sc.render.resolution_percentage=100
cam=bpy.data.objects.new('ReviewCamera',bpy.data.cameras.new('ReviewCamera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO'
for name,pos,target,scale in [('R1hand',(-.8,-3,1.72),(-.81,-.2,1.72),.5)]:
 cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;sc.render.filepath=str(P/'review'/f'{name}.png');bpy.ops.render.render(write_still=True)
