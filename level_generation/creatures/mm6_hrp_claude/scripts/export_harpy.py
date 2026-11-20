"""Portable animated master with separate 1K body, wing and head sets and named effect sockets."""
import bpy,json,sys
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_master.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];sc=bpy.context.scene;T=P/'textures'
for slot,label,name in [(0,'body','HarpyBody_A'),(1,'head','HarpyHead_A'),(2,'wings','HarpyWings_A')]:
 if name in bpy.data.materials:bpy.data.materials[name].name=name+'_source'
 mat=bpy.data.materials.new(name);mat.use_nodes=True;mat.use_backface_culling=False;nt=mat.node_tree;bs=nt.nodes.get('Principled BSDF');bs.inputs['Metallic'].default_value=1;bs.inputs['Roughness'].default_value=1
 def tex(suffix,cs):
  node=nt.nodes.new('ShaderNodeTexImage');node.image=bpy.data.images.load(str(T/f'hrp_{label}_{suffix}.png'),check_existing=True);node.image.colorspace_settings.name=cs;return node
 nt.links.new(tex('basecolor_1k_graded','sRGB').outputs['Color'],bs.inputs['Base Color']);mr=tex('metal_rough_1k','Non-Color');sep=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(mr.outputs['Color'],sep.inputs['Color']);nt.links.new(sep.outputs['Green'],bs.inputs['Roughness']);nt.links.new(sep.outputs['Blue'],bs.inputs['Metallic']);nm=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(tex('normal_1k','Non-Color').outputs['Color'],nm.inputs['Color']);nt.links.new(nm.outputs['Normal'],bs.inputs['Normal']);body.data.materials[slot]=mat
rig.animation_data_create();rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update()
# Empty sockets are parented with a rest-space inverse, so the bone tails do not offset the authored positions.
sockets={'Socket_Eye_Left':('Head',(.035,-.177,1.61)),'Socket_Eye_Right':('Head',(-.055,-.177,1.61)),'Socket_Gaze':('Head',(-.01,-.19,1.61))}
for sd in ['L','R']:
 n=sd+'Hand';b=rig.data.bones[n];p=b.head_local+(b.tail_local-b.head_local).normalized()*.06;sockets['Socket_Palm_'+('Left' if sd=='L' else 'Right')]=(n,p)
for n,(bn,position) in sockets.items():
 obj=bpy.data.objects.new(n,None);sc.collection.objects.link(obj);obj.parent=rig;obj.parent_type='BONE';obj.parent_bone=bn;obj.matrix_world=Matrix.Translation(Vector(position));bpy.context.view_layer.update()
 # Parent inverse is measured on the actual rest bone parenting transform (which includes its tail).
 parent_matrix=rig.matrix_world@rig.pose.bones[bn].matrix@Matrix.Translation((0,rig.data.bones[bn].length,0));obj.matrix_parent_inverse=parent_matrix.inverted();obj.matrix_basis=Matrix.Translation(Vector(position))
for o in bpy.data.objects:o.select_set(o==body or o==rig or o.name in sockets)
bpy.context.view_layer.objects.active=rig;sc.render.fps=32;rig.animation_data.action=bpy.data.actions['Standing'];sc.frame_set(1)
for material in list(bpy.data.materials):
 if material.users==0:bpy.data.materials.remove(material)
for image in list(bpy.data.images):
 if image.users==0:bpy.data.images.remove(image)
 elif image.source=='FILE':image.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'export/mm6_hrp.blend'))
bpy.ops.export_scene.gltf(filepath=str(P/'export/mm6_hrp_lod0.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=False,export_attributes=False,export_morph=False,export_image_format='AUTO',export_reset_pose_bones=True,export_anim_slide_to_zero=True,export_extras=False)
print('EXPORTED HARPY',len(body.data.polygons),'faces',len(rig.data.bones),'bones',len(bpy.data.actions),'actions')
