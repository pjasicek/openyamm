import bpy
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_uv.blend'))
b=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];r.animation_data.action=bpy.data.actions['Standing'];bpy.context.scene.frame_set(1)
image=bpy.data.images.new('UV checker',width=1024,height=1024);image.generated_type='COLOR_GRID'
for mat in b.data.materials:
 nt=mat.node_tree;n=nt.nodes.new('ShaderNodeTexImage');n.image=image;nt.nodes.active=n;nt.links.new(n.outputs['Color'],nt.nodes.get('Principled BSDF').inputs['Base Color'])
sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.color_type='TEXTURE';sc.display.shading.light='STUDIO';sc.display.shading.show_shadows=False;sc.display.shading.show_cavity=False;sc.render.resolution_x=sc.render.resolution_y=800
cam=bpy.data.objects.new('UVReviewCamera',bpy.data.cameras.new('UVReviewCamera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO'
for name,pos,target,scale in [('body',(4,-6,3),(.4,.8,1),3.3),('head',(1,-4,2),(0,0,1.75),.65)]:
 cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;sc.render.filepath=str(P/'review'/f'uv_checker_{name}.png');bpy.ops.render.render(write_still=True)
