import bpy
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_v3.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene
sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='SINGLE';sc.display.shading.single_color=(.65,.68,.62);sc.display.shading.show_cavity=True;sc.display.shading.show_shadows=False;sc.render.resolution_x=900;sc.render.resolution_y=650;sc.render.resolution_percentage=100
cam=bpy.data.objects.new('Camera',bpy.data.cameras.new('Camera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=.6
for name,frames in [('Standing',[0,7,14,21]),('Attack',[0,12,18,23,30]),('Hit',[3])]:
 rig.animation_data.action=bpy.data.actions[name]
 for f in frames:
  sc.frame_set(f)
  for view,pos in [('front',(0,-6,.65)),('quarter',(4,-6,2))]:
   cam.location=pos;cam.rotation_euler=(Vector((0,-.38,.72))-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(P/'review'/f'jawcheck_{name}_{f:02d}_{view}.png');bpy.ops.render.render(write_still=True)
