import bpy,json,math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_master.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];sc=bpy.context.scene
for slot,label in [(0,'body'),(1,'head')]:
 mat=body.data.materials[slot];mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.7;img=bpy.data.images.load(str(P/'meshy'/f'{label}_retexture_v{2 if label == "body" else 1}/texture_urls_0_base_color.png'));tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=img;mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
rig.animation_data.action=bpy.data.actions['Standing'];sc.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/raw_textured_v2.blend'))
sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=24;sc.cycles.use_denoising=True;sc.world=bpy.data.worlds.new('World');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.22,.24,.28,1);sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.6
for name,pos,energy,size in [('Key',(-3,-4,6),500,4),('Fill',(4,-2,3),250,4),('Rim',(1,4,5),350,3)]:
 l=bpy.data.objects.new(name,bpy.data.lights.new(name,'AREA'));sc.collection.objects.link(l);l.location=pos;l.data.energy=energy;l.data.shape='DISK';l.data.size=size;l.rotation_euler=(Vector((0,0,1.2))-l.location).to_track_quat('-Z','Y').to_euler()
cam=bpy.data.objects.new('Camera',bpy.data.cameras.new('Camera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO';sc.render.resolution_x=sc.render.resolution_y=900;sc.render.resolution_percentage=100;sc.view_settings.view_transform='Standard'
for name,pos,target,scale in [('front',(0,-6,1.15),(0,0,1.15),2.5),('quarter',(4,-6,3),(0,.1,1.15),2.6),('back',(0,6,1.15),(0,0,1.15),2.5),('head',(1,-5,2.4),(0,0,1.99),.73),('chest',(0,-5,1.5),(0,0,1.48),.66)]:
 cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;sc.render.filepath=str(P/'review'/f'body2_{name}.png');bpy.ops.render.render(write_still=True)
