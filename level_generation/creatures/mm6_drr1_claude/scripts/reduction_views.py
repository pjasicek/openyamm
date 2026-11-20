import bpy,json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];O=P/'review/reduction'
for label,src in [('full','work/textured_master_v2.blend'),('step01','review/reduction/step_01.blend'),('step02','review/reduction/step_02.blend')]:
 bpy.ops.wm.open_mainfile(filepath=str(P/src));sc=bpy.context.scene;rig=bpy.data.objects['Wyrm_Rig'];rig.animation_data.action=bpy.data.actions['Running'];sc.frame_set(5,subframe=.5)
 sc.render.engine='BLENDER_WORKBENCH';sc.render.resolution_x=1200;sc.render.resolution_y=850;sc.render.resolution_percentage=100;sc.display.shading.light='STUDIO';sc.display.shading.color_type='SINGLE';sc.display.shading.single_color=(.65,.68,.61);sc.display.shading.show_cavity=True;sc.display.shading.background_type='VIEWPORT';sc.display.shading.background_color=(.14,.14,.14)
 cam=bpy.data.objects.new('CompareCamera',bpy.data.cameras.new('CompareCamera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO'
 for view,xyz,target,size in [('side',(1,0,.3),(0,0,.2),1.1),('legs',(.45,-.55,.15),(0,-.24,.12),.32)]:
  cam.location=xyz;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=size;sc.render.filepath=str(O/f'{label}_{view}.png');bpy.ops.render.render(write_still=True)
