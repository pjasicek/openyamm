"""Portable animated master with separate 1K body/head sets and named effect sockets."""
import bpy,json,sys
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_master.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];sc=bpy.context.scene;T=P/'textures'
for m in list(bpy.data.materials):
 if m.name!='Foam':m.name='Source_'+m.name
for slot,label,name in [(0,'body','Water_A'),(1,'head','WaterHead_A')]:
 mat=bpy.data.materials.new(name);mat.use_nodes=True;mat.use_backface_culling=False;nt=mat.node_tree;bs=nt.nodes.get('Principled BSDF');bs.inputs['Metallic'].default_value=1;bs.inputs['Roughness'].default_value=1
 def tex(suffix,cs):
  node=nt.nodes.new('ShaderNodeTexImage');node.image=bpy.data.images.load(str(T/f'wel_{label}_{suffix}.png'),check_existing=False);node.image.colorspace_settings.name=cs;return node
 nt.links.new(tex('basecolor_1k','sRGB').outputs['Color'],bs.inputs['Base Color']);mr=tex('metal_rough_1k','Non-Color');sep=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(mr.outputs['Color'],sep.inputs['Color']);nt.links.new(sep.outputs['Green'],bs.inputs['Roughness']);nt.links.new(sep.outputs['Blue'],bs.inputs['Metallic']);nm=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(tex('normal_1k','Non-Color').outputs['Color'],nm.inputs['Color']);nt.links.new(nm.outputs['Normal'],bs.inputs['Normal']);body.data.materials[slot]=mat
prop=bpy.data.objects['Trident'];prop.name='TridentMesh'
if not prop.data.uv_layers:prop.data.uv_layers.new(name='UVMap')
# Poseidon UVs come from the authored blade/shaft atlas.
mat=bpy.data.materials.new('Trident_A');mat.use_nodes=True;nt=mat.node_tree;bs=nt.nodes.get('Principled BSDF');bs.inputs['Metallic'].default_value=1;bs.inputs['Roughness'].default_value=1
base=nt.nodes.new('ShaderNodeTexImage');base.image=bpy.data.images.load(str(T/'wel_trident_basecolor.png'));nt.links.new(base.outputs['Color'],bs.inputs['Base Color']);mr=nt.nodes.new('ShaderNodeTexImage');mr.image=bpy.data.images.load(str(T/'wel_trident_metal_rough.png'));mr.image.colorspace_settings.name='Non-Color';sep=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(mr.outputs['Color'],sep.inputs['Color']);nt.links.new(sep.outputs['Green'],bs.inputs['Roughness']);nt.links.new(sep.outputs['Blue'],bs.inputs['Metallic']);prop.data.materials.clear();prop.data.materials.append(mat)
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update()
# Empty sockets are parented with a rest-space inverse, so the bone tails do not offset the authored positions.
sockets={'Socket_Eye_Left':('B_Head',(.0264,-.0829,1.9134)),'Socket_Eye_Right':('B_Head',(-.0452,-.0821,1.9134)),'Socket_Gaze':('B_Head',(-.01,-.10,1.9134))}
for sd in ['L','R']:
 n='B_'+sd+'_Hand';b=rig.data.bones[n];p=b.head_local+(b.tail_local-b.head_local).normalized()*.06;sockets['Socket_Palm_'+('Left' if sd=='L' else 'Right')]=(n,p)
for n,(bn,position) in sockets.items():
 obj=bpy.data.objects.new(n,None);sc.collection.objects.link(obj);obj.parent=rig;obj.parent_type='BONE';obj.parent_bone=bn;obj.matrix_world=Matrix.Translation(Vector(position));bpy.context.view_layer.update()
 # Parent inverse is measured on the actual rest bone parenting transform (which includes its tail).
 parent_matrix=rig.matrix_world@rig.pose.bones[bn].matrix@Matrix.Translation((0,rig.data.bones[bn].length,0));obj.matrix_parent_inverse=parent_matrix.inverted();obj.matrix_basis=Matrix.Translation(Vector(position))
for o in bpy.data.objects:o.select_set(o==body or o==rig or o.name in sockets or o.name in ['TridentMesh','Foam'])
bpy.context.view_layer.objects.active=rig;sc.render.fps=60;rig.animation_data.action=bpy.data.actions['Standing'];sc.frame_set(1)
bpy.context.view_layer.update()
ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();z=[v.co.z for v in m.vertices];height=max(z)-min(z);ev.to_mesh_clear()
(P/'export/export_info.json').write_text(json.dumps({'triangles':len(body.data.polygons),'bones':len(rig.data.bones),'standing_height_m':height,'binding_scale':216*.899994/height,'clips':{a.name:float((a.frame_range[1]-a.frame_range[0])/60) for a in bpy.data.actions},'fps':60},indent=2))
for image in bpy.data.images:
 if image.source=='FILE':image.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'export/mm6_wel.blend'))
bpy.ops.export_scene.gltf(filepath=str(P/'export/mm6_wel_lod0.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=False,export_attributes=False,export_morph=False,export_image_format='AUTO',export_reset_pose_bones=True,export_anim_slide_to_zero=True,export_extras=False)
print('EXPORTED WATER',len(body.data.polygons),'faces',len(rig.data.bones),'bones',len(bpy.data.actions),'actions')
