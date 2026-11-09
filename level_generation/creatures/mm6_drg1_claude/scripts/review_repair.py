import bpy,bmesh,math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/repaired_geometry.blend'));o=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];sc=bpy.context.scene
rig.animation_data_create();rig.animation_data.action=bpy.data.actions['Standing'];sc.frame_set(0)
sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='SINGLE';sc.display.shading.single_color=(.64,.68,.65);sc.display.shading.show_cavity=True;sc.display.shading.show_shadows=False;sc.render.resolution_x=1200;sc.render.resolution_y=900;sc.render.resolution_percentage=100
cam=bpy.data.objects.new('RepairCamera',bpy.data.cameras.new('RepairCamera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO'
for name,loc,target,size in [('neck_front',(0,-6,.65),(0,-.3,.58),.6),('neck_side',(6,0,.65),(0,-.3,.58),.6),('forelegs',(3,-6,2),(0,-.3,.28),.65),('whole',(4,-6,2),(0,.15,.45),3.4)]:
 cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=size;sc.render.filepath=str(P/'review'/f'repair_{name}.png');bpy.ops.render.render(write_still=True)
