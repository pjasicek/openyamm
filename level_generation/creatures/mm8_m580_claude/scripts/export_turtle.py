"""Pack the shared PBR maps into the portable animated master and editable Blender source."""
from pathlib import Path
import bpy,sys
P=Path(__file__).resolve().parents[1];T=P/'textures'
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_uv.blend'));m=bpy.data.objects['Turtle'];rig=bpy.data.objects['Turtle_Rig'];sc=bpy.context.scene
for slot,label,name in [(0,'m580','TurtleBody')]:
 mat=bpy.data.materials.new(name+'_final');mat.name=name;mat.use_nodes=True;mat.use_backface_culling=True;mat['openyamm_specular']=0.
 nt=mat.node_tree;bs=nt.nodes.get('Principled BSDF');bs.inputs['Specular IOR Level'].default_value=0.;bs.inputs['Metallic'].default_value=1;bs.inputs['Roughness'].default_value=1
 def tex(suffix,space):
  n=nt.nodes.new('ShaderNodeTexImage');n.image=bpy.data.images.load(str(T/f'{label}_{suffix}.png'),check_existing=True);n.image.colorspace_settings.name=space;return n
 nt.links.new(tex('basecolor','sRGB').outputs['Color'],bs.inputs['Base Color']);mr=tex('metal_rough','Non-Color');sep=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(mr.outputs['Color'],sep.inputs['Color']);nt.links.new(sep.outputs['Green'],bs.inputs['Roughness']);nt.links.new(sep.outputs['Blue'],bs.inputs['Metallic'])
 normal=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(tex('normal','Non-Color').outputs['Color'],normal.inputs['Color']);nt.links.new(normal.outputs['Normal'],bs.inputs['Normal']);m.data.materials[slot]=mat
# Ensure stable material names after replacing the untextured checkpoint's original datablocks.
for slot,name in [(0,'TurtleBody')]:
 old=bpy.data.materials.get(name)
 if old and old!=m.data.materials[slot]:old.name=name+'_unused'
 m.data.materials[slot].name=name
for o in bpy.data.objects:o.select_set(o in [m,rig])
bpy.context.view_layer.objects.active=rig;sc.render.fps=48;rig.animation_data.action=bpy.data.actions['SwimIdle'];rig.animation_data.action_slot=rig.animation_data.action.slots[0];sc.frame_set(0)
for image in bpy.data.images:
 if image.source=='FILE':image.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'export/mm8_m580.blend'))
bpy.ops.export_scene.gltf(filepath=str(P/'export/mm8_m580_lod0.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=False,export_frame_step=1,export_skins=True,export_all_influences=False,export_attributes=False,export_morph=False,export_image_format='AUTO',export_reset_pose_bones=True,export_anim_slide_to_zero=True,export_extras=True)
# Runtime owns its specular semantics; Blender's optional extension is not consumed by the game.
sys.path.insert(0,str(Path('tools').resolve()));from build_actor_lods import read_glb,write_glb
path=P/'export/mm8_m580_lod0.glb';doc,binary=read_glb(path)
for mat in doc['materials']:
 mat.get('extensions',{}).pop('KHR_materials_specular',None)
 if not mat.get('extensions'):mat.pop('extensions',None)
for key in ['extensionsUsed','extensionsRequired']:
 if key in doc:doc[key]=[x for x in doc[key] if x!='KHR_materials_specular']
write_glb(path,doc,binary)
print('EXPORTED',len(rig.data.bones),'bones',len(bpy.data.actions),'clips')
