import bpy,math,json,os
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parents[1];out=p/'review/round3/reduction';size=800
lod_review=bool(os.environ.get('LOD_REVIEW'))
cases=[('source','work/animation_finish.blend',p/'textures',800),('reduced','work/candidate_rebaked.blend',out/'rebaked',800)]
if lod_review:cases=[(f'lod{level}_{which}',f'work/review_lod{which}.glb',p/'textures',round(pixels*1.955/1.711)) for level,pixels in [(1,500),(2,200),(3,80)] for which in [0,level]]
if os.environ.get('LOD_REVIEW')=='probe':cases=[('lod3_probe65','work/review_lod2.glb',p/'textures',91),('lod3_probe75','work/review_lod1.glb',p/'textures',91)]
for kind,blend,textures,size in cases:
 if blend.endswith('.blend'):bpy.ops.wm.open_mainfile(filepath=str(p/blend))
 else:bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(p/blend))
 body=next(o for o in bpy.data.objects if o.type=='MESH');rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');act=bpy.data.actions['Standing'];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];sc=bpy.context.scene;sc.frame_set(0);sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=16;sc.cycles.use_denoising=True;sc.cycles.max_bounces=2;sc.render.resolution_x=size;sc.render.resolution_y=size;sc.render.resolution_percentage=100;sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0;sc.view_settings.gamma=1
 sc.world=bpy.data.worlds.new('Reduction review world');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.35,.35,.35,1);sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.7
 for x,y,power in [(-3,-4,450),(3,-2,300),(0,4,400)]:
  data=bpy.data.lights.new('Review softbox','AREA');data.energy=power;data.shape='DISK';data.size=4;o=bpy.data.objects.new('Review softbox',data);sc.collection.objects.link(o);o.location=(x,y,4);o.rotation_euler=(Vector((0,0,.8))-o.location).to_track_quat('-Z','Y').to_euler()
 mat=bpy.data.materials.new('Actual tier');mat.use_nodes=True;nt=mat.node_tree;bsdf=nt.nodes.get('Principled BSDF');bsdf.inputs['Specular IOR Level'].default_value=0;bsdf.inputs['Metallic'].default_value=0
 def tex(path,space):
  node=nt.nodes.new('ShaderNodeTexImage');node.image=bpy.data.images.load(str(path),check_existing=False);node.image.colorspace_settings.name=space;return node
 base=tex(p/'work/tier_mnk1_b_Monk_A.png' if lod_review else out/f'{kind}_a.png','sRGB');nt.links.new(base.outputs['Color'],bsdf.inputs['Base Color']);normal=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(tex(textures/'mnk1_normal_1k.png','Non-Color').outputs['Color'],normal.inputs['Color']);nt.links.new(normal.outputs['Normal'],bsdf.inputs['Normal']);sep=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(tex(textures/'mnk1_orm_1k.png','Non-Color').outputs['Color'],sep.inputs['Color']);nt.links.new(sep.outputs['Green'],bsdf.inputs['Roughness']);body.data.materials.clear();body.data.materials.append(mat)
 for f in body.data.polygons:f.material_index=0;f.use_smooth=True
 data=bpy.data.cameras.new('Reduction camera');data.type='ORTHO';data.ortho_scale=1.955;cam=bpy.data.objects.new('Reduction camera',data);sc.collection.objects.link(cam);sc.camera=cam
 for tier in ('b' if lod_review else 'abc'):
  base.image=bpy.data.images.load(str(p/'work/tier_mnk1_b_Monk_A.png' if lod_review else out/f'{kind}_{tier}.png'),check_existing=False)
  for view in range(8):
   angle=view*math.pi/4;cam.location=(4*math.sin(angle),-4*math.cos(angle),.856);cam.rotation_euler=(Vector((0,0,.856))-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(out/f'{kind}_{tier}_{view}.png');bpy.ops.render.render(write_still=True)
