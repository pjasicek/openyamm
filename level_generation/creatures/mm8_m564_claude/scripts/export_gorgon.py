"""Portable animated master; one PBR material and eight authored clips."""
from pathlib import Path
import bpy,bmesh,json
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/uv_master.blend'))
mesh=bpy.data.objects['Gorgon'];rig=bpy.data.objects['Gorgon_Rig'];sc=bpy.context.scene
bm=bmesh.new();bm.from_mesh(mesh.data)
dead=[f for f in bm.faces if f.calc_area()<1e-10]
bmesh.ops.delete(bm,geom=dead,context='FACES');bm.to_mesh(mesh.data);bm.free()
mat=bpy.data.materials.new('Gorgon_A');mat.use_nodes=True;nt=mat.node_tree
bsdf=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED')
def tex(name,cs):
 img=bpy.data.images.load(str(P/'textures'/name));img.colorspace_settings.name=cs
 node=nt.nodes.new('ShaderNodeTexImage');node.image=img;return node
bc=tex('gorgon_basecolor.png','sRGB');nt.links.new(bc.outputs['Color'],bsdf.inputs['Base Color'])
nm=tex('gorgon_normal_1k.png','Non-Color');nmap=nt.nodes.new('ShaderNodeNormalMap')
nt.links.new(nm.outputs['Color'],nmap.inputs['Color']);nt.links.new(nmap.outputs['Normal'],bsdf.inputs['Normal'])
mr=tex('gorgon_metal_rough_1k.png','Non-Color');sep=nt.nodes.new('ShaderNodeSeparateColor')
nt.links.new(mr.outputs['Color'],sep.inputs['Color']);nt.links.new(sep.outputs['Green'],bsdf.inputs['Roughness'])
nt.links.new(sep.outputs['Blue'],bsdf.inputs['Metallic'])
mesh.data.materials.clear();mesh.data.materials.append(mat)
rig.animation_data.action=bpy.data.actions['Standing'];sc.frame_set(1)
for obj in sc.objects:obj.select_set(obj in (mesh,rig))
bpy.context.view_layer.objects.active=rig
(P/'export').mkdir(exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(P/'export/mm8_m564_lod0.glb'),use_selection=True,
 export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',
 export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=False,
 export_attributes=False,export_morph=False,export_image_format='AUTO',export_reset_pose_bones=True,
 export_anim_slide_to_zero=True)
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'gorgon_master.blend'))
(P/'work/export_geometry.json').write_text(json.dumps({'triangles':len(mesh.data.polygons),'removed_zero_area_faces':len(dead),'bones':len(rig.data.bones),'fps':sc.render.fps},indent=2)+'\n')
