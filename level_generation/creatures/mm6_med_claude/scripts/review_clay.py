import bpy,json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_v1.blend'))
rig=bpy.data.objects['Rig'];sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.show_shadows=True;sc.display.shading.show_cavity=True;sc.display.shading.cavity_type='BOTH';sc.display.shading.color_type='MATERIAL';sc.display.shading.background_type='WORLD';sc.world=bpy.data.worlds.new('World');sc.world.color=(.13,.13,.15);sc.render.resolution_x=sc.render.resolution_y=600;sc.render.resolution_percentage=100
cam=bpy.data.objects.new('ReviewCamera',bpy.data.cameras.new('ReviewCamera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO'
for role,frame in [('Standing',1),('Walk',8),('Running',8),('Attack',23),('Cast',23),('Hit',6),('Death',22),('Death',49),('Dead',1)]:
 rig.animation_data.action=bpy.data.actions[role];sc.frame_set(frame)
 for view,pos,target,size in [('front',(0,-6,2.5),(0,.1,1.05),2.65),('quarter',(4,-6,3),(0,.1,1.05),2.65),('side',(6,0,2.4),(0,.1,1.05),2.65)]:
  cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=size;sc.render.filepath=str(P/'review'/f'clay_{role}_{frame}_{view}.png');bpy.ops.render.render(write_still=True)
