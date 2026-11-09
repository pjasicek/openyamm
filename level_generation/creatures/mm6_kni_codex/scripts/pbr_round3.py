"""Matched PBR renders with actual tier colours, roughness/specular and tangent normals."""
import bpy,sys,json,math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];W=P/'work/round3';R=P/'review/round3';T=P/'textures/round3';sys.path.insert(0,str(P/'scripts'));import reduce_round2 as old;import common

def setup(body,rig,variant,tier,pixels=700,lod=0):
 s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=16;s.cycles.use_denoising=True;s.cycles.seed=1729;s.render.threads_mode='FIXED';s.render.threads=4;s.render.film_transparent=True;s.render.resolution_x=s.render.resolution_y=[1024,640,320,192][lod];s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA';s.view_settings.view_transform='Standard';s.view_settings.look='None';s.view_settings.exposure=0;s.view_settings.gamma=1
 s.world=bpy.data.worlds.new('Studio');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[0].default_value=(.5,.5,.5,1);s.world.node_tree.nodes['Background'].inputs[1].default_value=.7
 for name,loc,power,size in [('Key',(-3,-4,5),450,4),('Fill',(4,-1,3),250,4),('Rim',(0,4,4),300,3)]:
  data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size;o=bpy.data.objects.new(name,data);s.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
 mat=bpy.data.materials.new('Tier '+tier);mat.use_nodes=True;body.data.materials.clear();body.data.materials.append(mat);n=mat.node_tree.nodes;l=mat.node_tree.links;bs=n.get('Principled BSDF');bs.inputs['Metallic'].default_value=0
 for key in ['basecolor','metal_rough','normal']:
  path=W/f'{variant}_tier_{tier}.png'if key=='basecolor'else (W/f'high_{key}.png'if variant=='high'else T/(f'knight_normal_l{lod}.png' if key=='normal' and lod>0 else f'knight_{key}.png'));tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(path),check_existing=True)
  if key!='basecolor':tex.image.colorspace_settings.name='Non-Color'
  if key=='basecolor':l.new(tex.outputs['Color'],bs.inputs['Base Color'])
  elif key=='normal':
   nm=n.new('ShaderNodeNormalMap');l.new(tex.outputs['Color'],nm.inputs['Color']);l.new(nm.outputs['Normal'],bs.inputs['Normal'])
  else:
   sep=n.new('ShaderNodeSeparateColor');l.new(tex.outputs['Color'],sep.inputs[0]);l.new(sep.outputs['Green'],bs.inputs['Roughness']);l.new(sep.outputs['Red'],bs.inputs['Specular IOR Level'])
 act=bpy.data.actions['Standing'];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];s.frame_set(0)
 h=json.loads((R/'silhouette_curve.json').read_text())[0]['body_standing_height_m'];scale=(h if lod==0 else 2.1778047)*s.render.resolution_x/pixels
 return s,scale

def render(variant,tier,prefix,pixels=700,lod=0,views=range(8),blend=None):
 if variant=='high':body,rig=old.reset(lod)
 else:
  bpy.ops.wm.open_mainfile(filepath=str(blend or W/f'rebaked_l{lod}.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig']
 s,scale=setup(body,rig,variant,tier,pixels,lod)
 for i in views:
  d=Vector((math.sin(i*math.pi/4),-math.cos(i*math.pi/4),.05)).normalized();cam=common.ortho_camera('MetricCamera',Vector((0,0,.95))+d*6,(0,0,0),scale);cam.rotation_mode='QUATERNION';cam.rotation_quaternion=(-d).to_track_quat('-Z','Y');s.camera=cam;s.render.filepath=str(R/f'{prefix}_{i}.png');bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam,do_unlink=True)
if __name__=='__main__':
 for tier in 'abc':
  for variant in ['high','low']:render(variant,tier,f'pbr_{variant}_{tier}')
