"""final_materials.py for the 35 % retexture: materials from textures/, export/mm6_drag.blend +
export/mm6_drag_selected.glb, renders to review/r35/. No spine UV remap: the fresh UVs give spines their own islands."""
import bpy,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];T=P/'textures';bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_r35.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];sc=bpy.context.scene
body.data.validate(verbose=True,clean_customdata=False);assert not body.data.validate(clean_customdata=False)
for old in list(bpy.data.materials):old.name='Previous_'+old.name
for slot,label in enumerate(['body','head']):
 mat=bpy.data.materials.new('Lizard'+label.title()+'_A');mat.use_nodes=True;mat.use_backface_culling=False;nt=mat.node_tree;bs=nt.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=1
 def tex(suffix,cs):
  n=nt.nodes.new('ShaderNodeTexImage');n.image=bpy.data.images.load(str(T/f'drag_{label}_{suffix}.png'),check_existing=True);n.image.colorspace_settings.name=cs;return n
 base=tex('basecolor_2k','sRGB');nt.links.new(base.outputs['Color'],bs.inputs['Base Color']);mr=tex('metal_rough_2k','Non-Color');sep=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(mr.outputs['Color'],sep.inputs['Color']);nt.links.new(sep.outputs['Green'],bs.inputs['Roughness']);nt.links.new(sep.outputs['Blue'],bs.inputs['Metallic']);nm=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(tex('normal_2k','Non-Color').outputs['Color'],nm.inputs['Color']);nt.links.new(nm.outputs['Normal'],bs.inputs['Normal']);nt.nodes.active=base;body.data.materials[slot]=mat

rig.animation_data_create();rig.animation_data.action=bpy.data.actions['Standing'];sc.render.fps=24;sc.frame_set(0)
for ob in bpy.data.objects:ob.select_set(ob in [body,rig])
bpy.context.view_layer.objects.active=rig
for im in bpy.data.images:
 if im.users and im.source=='FILE':
  if im.packed_file:im.unpack(method='REMOVE')
  im.reload();im.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'export/mm6_drag.blend'))
bpy.ops.export_scene.gltf(filepath=str(P/'export/mm6_drag_selected.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=False,export_attributes=False,export_morph=False,export_image_format='AUTO',export_reset_pose_bones=True,export_anim_slide_to_zero=True)
sc.render.engine='CYCLES';sc.cycles.samples=12;sc.cycles.device='CPU';sc.render.resolution_x=1000;sc.render.resolution_y=750;sc.render.resolution_percentage=100;sc.world=bpy.data.worlds.new('Studio');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.20,.20,.20,1);sc.world.node_tree.nodes['Background'].inputs[1].default_value=.8
for name,loc,energy,size in [('Key',(2,-3,4),250,3),('Fill',(-3,-1,2),150,3),('Rim',(0,3,3),280,2)]:
 l=bpy.data.objects.new(name,bpy.data.lights.new(name,'AREA'));sc.collection.objects.link(l);l.location=loc;l.data.energy=energy;l.data.shape='DISK';l.data.size=size;l.rotation_euler=(Vector((0,-.5,.8))-l.location).to_track_quat('-Z','Y').to_euler()
cam=bpy.data.objects.new('Camera',bpy.data.cameras.new('Camera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO'
for name,clip,frame,offset,target,size in [('head','Standing',0,(2,-5,.6),(0,-.32,.82),.55),('side','Standing',0,(5,0,.1),(0,0,.5),1.7),('dead','Dead',0,(3,-5,3),(0,-.05,.25),1.65),('whole','Standing',0,(3,-5,1.5),(0,-.05,.48),1.65),('front','Standing',0,(0,-5,0),(0,-.05,.48),1.65),('attack','Attack',18,(2,-5,.6),(0,-.36,.8),.45)]:
 rig.animation_data.action=bpy.data.actions[clip];sc.frame_set(frame);target=Vector(target);cam.location=target+Vector(offset);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=size;sc.render.filepath=str(P/'review'/'r35'/f'textured_{name}.png');bpy.ops.render.render(write_still=True)
