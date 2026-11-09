import bpy,sys,json,math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
for tag in ['1.0000','0.7000']:
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/reduction_v5/Body_l0_r{tag}.blend'));sc=bpy.context.scene;rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];sc.frame_set(0)
 for o in bpy.data.objects:
  if o.type=='MESH':o.hide_render=o!=body
 sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=16;sc.cycles.use_denoising=True;sc.render.resolution_x=sc.render.resolution_y=960;sc.render.resolution_percentage=100;sc.render.film_transparent=True;sc.render.image_settings.color_mode='RGBA';sc.view_settings.view_transform='Standard';sc.view_settings.look='None'
 world=bpy.data.worlds.new('MetricWorld');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(1,1,1,1);world.node_tree.nodes['Background'].inputs[1].default_value=.6;sc.world=world
 for m in body.data.materials:
  bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Specular IOR Level'].default_value=0
  for link in list(bs.inputs['Metallic'].links):m.node_tree.links.remove(link)
  bs.inputs['Metallic'].default_value=0
  if tag=='1.0000':
   im=bpy.data.images.load(str(P/f'textures/natf_{"head"if"Head"in m.name else"body"}_normal_gl.png'));im.colorspace_settings.name='Non-Color';node=bs.inputs['Normal'].links[0].from_node.inputs['Color'].links[0].from_node;node.image=im
 cam=common.ortho_camera('MetricCamera',(0,-6,.83),(math.pi/2,0,0),1.65*960/700);sc.camera=cam;sc.render.filepath=str(P/f'review/pbr_probe_{tag}.png');bpy.ops.render.render(write_still=True)
