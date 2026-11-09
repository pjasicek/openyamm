import bpy,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];T=P/'textures';bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_master.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];sc=bpy.context.scene
body.data.validate(verbose=True,clean_customdata=False);assert not body.data.validate(clean_customdata=False)
for slot,label in enumerate(['body','head','wings']):
 mat=bpy.data.materials.new('Drake'+label.title()+'_A');mat.use_nodes=True;mat.use_backface_culling=False;nt=mat.node_tree;bs=nt.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=1
 def tex(suffix,cs):
  n=nt.nodes.new('ShaderNodeTexImage');n.image=bpy.data.images.load(str(T/f'drg1_{label}_{suffix}.png'),check_existing=True);n.image.colorspace_settings.name=cs;return n
 base=tex('basecolor_2k','sRGB');nt.links.new(base.outputs['Color'],bs.inputs['Base Color']);mr=tex('metal_rough_2k','Non-Color');sep=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(mr.outputs['Color'],sep.inputs['Color']);nt.links.new(sep.outputs['Green'],bs.inputs['Roughness']);nt.links.new(sep.outputs['Blue'],bs.inputs['Metallic']);nm=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(tex('normal_2k','Non-Color').outputs['Color'],nm.inputs['Color']);nt.links.new(nm.outputs['Normal'],bs.inputs['Normal']);nt.nodes.active=base;body.data.materials[slot]=mat
# Keep charred remains double-sided, matching the body shadow merge contract.
body.data.materials[3].use_backface_culling=False
rig.animation_data_create();rig.animation_data.action=bpy.data.actions['Standing'];sc.render.fps=24;sc.frame_set(0)
for ob in bpy.data.objects:ob.select_set(ob in [body,rig,bpy.data.objects.get('DeathFlames')])
bpy.context.view_layer.objects.active=rig
for im in bpy.data.images:
 if im.users and im.source=='FILE':im.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'export/mm6_drg1_full.blend'))
bpy.ops.export_scene.gltf(filepath=str(P/'export/mm6_drg1_full.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=False,export_attributes=False,export_morph=False,export_image_format='AUTO',export_reset_pose_bones=True,export_anim_slide_to_zero=True)
import sys
sys.path.insert(0,str(P.parents[2]/'tools'))
from build_actor_lods import read_glb,write_glb
glb=P/'export/mm6_drg1_full.glb';document,binary=read_glb(glb);fire=next(m for m in document['materials'] if m['name']=='DrakeDeathFlames');assert fire.get('alphaMode')=='BLEND' and 'baseColorTexture' in fire['pbrMetallicRoughness'];fire.pop('emissiveTexture',None);fire['emissiveFactor']=[0,0,0];fire.setdefault('extensions',{})['KHR_materials_unlit']={};document.setdefault('extensionsUsed',[]).append('KHR_materials_unlit');write_glb(glb,document,binary)
sc.render.engine='CYCLES';sc.cycles.samples=12;sc.cycles.device='CPU';sc.render.resolution_x=1000;sc.render.resolution_y=750;sc.render.resolution_percentage=100;sc.world=bpy.data.worlds.new('Studio');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.16,.16,.16,1);sc.world.node_tree.nodes['Background'].inputs[1].default_value=.8
for name,loc,energy,size in [('Key',(2,-3,4),320,3),('Fill',(-3,-1,2),180,3),('Rim',(0,3,3),280,2)]:
 l=bpy.data.objects.new(name,bpy.data.lights.new(name,'AREA'));sc.collection.objects.link(l);l.location=loc;l.data.energy=energy;l.data.shape='DISK';l.data.size=size;l.rotation_euler=(Vector((0,0,.4))-l.location).to_track_quat('-Z','Y').to_euler()
cam=bpy.data.objects.new('Camera',bpy.data.cameras.new('Camera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO'
for name,clip,frame,loc,target,size in [('whole','Standing',0,(4,-6,2),(0,.1,.45),3.2),('attack','Attack',23,(3,-5,1.6),(0,-.34,.67),.65),('front','Standing',7,(0,-6,.6),(0,0,.45),3.0),('dead','Dead',0,(3,-5,2),(0,0,.1),.48),('neck','Standing',0,(2,-6,1.3),(0,-.30,.57),.55),('burn_early','Death',10,(3,-6,2),(0,.1,.45),3.2),('burn_peak','Death',20,(3,-6,2),(0,.1,.45),3.2),('burn_end','Death',30,(3,-6,2),(0,.1,.45),3.2)]:
 rig.animation_data.action=bpy.data.actions[clip];sc.frame_set(frame);cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=size;sc.render.filepath=str(P/'review'/f'textured_{name}.png');bpy.ops.render.render(write_still=True)
