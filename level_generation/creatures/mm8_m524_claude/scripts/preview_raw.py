import bpy,json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_uv.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];sc=bpy.context.scene
for label,slot in [('body',0),('head',1)]:
 mat=bpy.data.materials.new('Raw_'+label);mat.use_nodes=True;nt=mat.node_tree;bs=nt.nodes.get('Principled BSDF');tex=nt.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(P/'meshy'/f'{label}_retexture_v1/texture_urls_0_base_color.png'));nt.links.new(tex.outputs['Color'],bs.inputs['Base Color']);bs.inputs['Roughness'].default_value=.65;body.data.materials[slot]=mat
if body.data.uv_layers.get('BodyFull'):body.data.uv_layers.remove(body.data.uv_layers['BodyFull'])
body.data.uv_layers.active=body.data.uv_layers['UVMap'];body.data.uv_layers.active.active_render=True
sc.render.engine='CYCLES';sc.cycles.samples=24;sc.cycles.use_denoising=True;sc.world=bpy.data.worlds.new('Neutral');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.22,.22,.22,1)
for name,pos,power,size in [('Key',(3,-4,5),450,4),('Fill',(-3,-2,3),220,3),('Rim',(0,4,4),400,3)]:
 light=bpy.data.lights.new(name,'AREA');light.energy=power;light.shape='DISK';light.size=size;o=bpy.data.objects.new(name,light);sc.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
cam=bpy.data.objects.new('ReviewCamera',bpy.data.cameras.new('ReviewCamera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO';sc.render.resolution_x=sc.render.resolution_y=850;sc.render.resolution_percentage=100
rig.animation_data.action=bpy.data.actions['Standing'];sc.frame_set(1)
for name,pos,target,size in [('front',(0,-6,2.2),(1,.7,1),4.7),('quarter',(4,-6,3),(1,1,1),5.0),('back',(0,6,2.2),(1,.7,1),4.7),('head',(2,-5,2.2),(0,0,1.72),1.0),('left',(6,1,2),(0,1.5,.95),4.7)]:
 cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=size;sc.render.filepath=str(P/'review'/f'raw_{name}.png');bpy.ops.render.render(write_still=True)
