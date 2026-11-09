import bpy,sys,json,math
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/round1/sword_clay.blend'));ob=bpy.data.objects['Sword'];T=P/'textures/sword_round1';mat=bpy.data.materials.new('KnightSword_Round1');mat.use_nodes=True;nt=mat.node_tree;bs=nt.nodes.get('Principled BSDF')
def tex(file,space):
 n=nt.nodes.new('ShaderNodeTexImage');n.image=bpy.data.images.load(str(T/file));n.image.colorspace_settings.name=space;return n
nt.links.new(tex('basecolor_1k.png','sRGB').outputs['Color'],bs.inputs['Base Color']);n=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(tex('normal_1k.png','Non-Color').outputs['Color'],n.inputs['Color']);nt.links.new(n.outputs['Normal'],bs.inputs['Normal']);mr=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(tex('metal_rough_1k.png','Non-Color').outputs['Color'],mr.inputs['Color']);nt.links.new(mr.outputs['Green'],bs.inputs['Roughness']);nt.links.new(mr.outputs['Blue'],bs.inputs['Metallic']);ob.data.materials.clear();ob.data.materials.append(mat)
counts=[sum(len(p.vertices)-2 for p in ob.data.polygons)]
for i,ratio in enumerate([.5,.20,.08],1):
 clone=ob.copy();clone.data=ob.data.copy();clone.name=f'Sword_LOD{i}';bpy.context.collection.objects.link(clone);bpy.context.view_layer.objects.active=clone;mod=clone.modifiers.new('Distance simplification','DECIMATE');mod.ratio=ratio;mod.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=mod.name);counts.append(sum(len(p.vertices)-2 for p in clone.data.polygons))
for o in bpy.data.objects:o.select_set(o.type=='MESH')
bpy.context.view_layer.objects.active=ob;bpy.ops.export_scene.gltf(filepath=str(P/'work/round1/sword_lods_canonical.glb'),use_selection=True,export_format='GLB',export_animations=False,export_yup=True,export_attributes=False)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round1/sword_textured.blend'));(P/'review/round1/lods.json').write_text(json.dumps({'triangles':counts},indent=2));print('SWORD LODS',counts)
