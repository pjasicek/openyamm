"""Paired packaged GLBs under identical studio light; Cycles CPU uses four wrapper threads."""
import bpy,json,sys,math,os
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];R=P/'review/triangle_rebake';sys.dont_write_bytecode=True
config=json.loads((R/'camera.json').read_text());entries=json.loads((R/'render_inputs.json').read_text())
for e in entries:
 label=e['label'];level=e['level'];tier=e['tier'];dest=R/f"textured/{label}/tier{tier}/lod{level}";dest.mkdir(parents=True,exist_ok=True)
 if all((dest/f'{k}.png').exists()for k in range(8)):continue
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(P/e['file']))
 sc=bpy.context.scene;body=bpy.data.objects['Lich'];rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
 act=bpy.data.actions['Standing'];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];sc.render.fps=30;sc.frame_set(0)
 for ob in bpy.data.objects:ob.hide_render=ob not in (body,rig)
 sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=24;sc.cycles.seed=17;sc.cycles.use_denoising=False;sc.cycles.max_bounces=3
 sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.resolution_percentage=100
 sc.view_settings.view_transform='Standard';sc.view_settings.look='Medium High Contrast'if False else 'None';sc.view_settings.exposure=0;sc.view_settings.gamma=1
 sc.world=bpy.data.worlds.new('StudioWorld');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.6,.6,.6,1);sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.6
 for name,position,power,size in [('Key',(-3,-4,5),550,4),('Fill',(4,-1,3),350,4),('Rim',(0,4,4),450,3)]:
  ld=bpy.data.lights.new(name,'AREA');ld.energy=power;ld.shape='DISK';ld.size=size;ob=bpy.data.objects.new(name,ld);sc.collection.objects.link(ob);ob.location=position;ob.rotation_euler=(Vector((0,0,1))-ob.location).to_track_quat('-Z','Y').to_euler()
 # Engine specular mask is the red ORM channel; keep the same modulation in both review materials.
 for mat in body.data.materials:
  nt=mat.node_tree;bs=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED');bs.inputs['Metallic'].default_value=0
  rough=bs.inputs['Roughness'];sep=rough.links[0].from_node if rough.links else None
  if sep and 'Red'in sep.outputs:
   scale=nt.nodes.new('ShaderNodeMath');scale.operation='MULTIPLY';scale.inputs[1].default_value=.5;nt.links.new(sep.outputs['Red'],scale.inputs[0]);nt.links.new(scale.outputs[0],bs.inputs['Specular IOR Level'])
 res=config['canvas_px'][level];sc.render.resolution_x=sc.render.resolution_y=res;cd=bpy.data.cameras.new('Comparison');cd.type='ORTHO';cd.ortho_scale=config['height_m']*res/config['actor_height_px'][level]
 cam=bpy.data.objects.new('Comparison',cd);sc.collection.objects.link(cam);sc.camera=cam;center=Vector(config['center_m'])
 for k in range(8):
  a=k*math.pi/4;cam.location=center+Vector((math.sin(a),-math.cos(a),0))*6;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(dest/f'{k}.png');bpy.ops.render.render(write_still=True)
 print('MATERIAL_RENDERED',label,tier,level,flush=True)
(R/'render_method.json').write_text(json.dumps({'renderer':'Cycles CPU, 24 samples, seed 17, no denoising, three area lamps and constant environment','tier_colors':'exact engine linear-luminance ramp rule from packaged GLB masks/ramps','surface':'packaged tangent normal, roughness and red ORM specular modulation','camera':config,'source':'render_inputs.json'},indent=2)+'\n')
