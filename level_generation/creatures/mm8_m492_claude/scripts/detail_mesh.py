import bpy,json
import numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/static_v1.blend'))
o=bpy.data.objects['Body'];sc=bpy.context.scene
sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='SINGLE';sc.display.shading.single_color=(.65,.68,.65);sc.display.shading.show_cavity=True;sc.display.shading.show_shadows=False;sc.render.resolution_x=1200;sc.render.resolution_y=1000;sc.render.resolution_percentage=100
cam=bpy.data.objects.new('Camera',bpy.data.cameras.new('Camera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO'
for name,target,scale,d in [('head_side',(0,-.325,.32),.19,(1,0,0)),('head_under',(0,-.325,.32),.19,(.7,-1,-.7)),('body_side',(0,-.2,.13),.30,(1,0,0)),('wing_top',(.24,-.18,.3),.5,(0,0,1)),('head_front',(0,-.325,.32),.19,(0,-1,0))]:
 target=Vector(target);cam.location=target+Vector(d)*3;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;sc.render.filepath=str(P/'review'/f'detail_{name}.png');bpy.ops.render.render(write_still=True)
