"""Rebake the detailed source onto a non-overlapping reduced-head atlas, retaining the rig and body UVs."""
from pathlib import Path
import bpy,bmesh,math,shutil,numpy as np
p=Path(__file__).resolve().parents[1];path=p/'work/rig_uv.blend';backup=p/'work/rig_uv_before_head_atlas.blend'
if not backup.exists():shutil.copyfile(path,backup)
bpy.ops.wm.open_mainfile(filepath=str(backup))
body=bpy.data.objects['Body'];source=bpy.data.objects['HeadSource'];rig=bpy.data.objects['Rig'];rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
head=body.copy();head.data=body.data.copy();head.name='AtlasBakeHead';head.modifiers.clear();head.parent=None;bpy.context.collection.objects.link(head)
me=head.data;me.attributes.new('source_face','INT','FACE').data.foreach_set('value',range(len(me.polygons)));me.attributes.new('source_vertex','INT','POINT').data.foreach_set('value',range(len(me.vertices)))
bm=bmesh.new();bm.from_mesh(me);hd=bm.faces.layers.int['head'];bmesh.ops.delete(bm,geom=[f for f in bm.faces if not f[hd]],context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6);bm.to_mesh(me);bm.free();print('HEAD_TOPOLOGY',len(me.vertices),len(me.polygons),flush=True)
for uv in list(me.uv_layers):
 if uv.name!='HeadUV':me.uv_layers.remove(uv)
me.uv_layers.active=me.uv_layers['HeadUV'];me.uv_layers['HeadUV'].active_render=True
for edge in me.edges:edge.use_seam=False
for ob in bpy.context.view_layer.objects:ob.select_set(ob==head)
head.hide_set(False);bpy.context.view_layer.objects.active=head;bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.004,margin_method='FRACTION',area_weight=0,correct_aspect=True);bpy.ops.object.mode_set(mode='OBJECT')
for f in me.polygons:
 orig=body.data.polygons[me.attributes['source_face'].data[f.index].value];uvs={tuple(round(v,5) for v in me.vertices[me.loops[li].vertex_index].co):me.uv_layers['HeadUV'].data[li].uv.copy() for li in f.loop_indices}
 for li in orig.loop_indices:body.data.uv_layers['HeadUV'].data[li].uv=uvs[tuple(round(v,5) for v in body.data.vertices[body.data.loops[li].vertex_index].co)]
# Smooth continuous source skin across its split UV vertices before normal projection.
bm=bmesh.new();bm.from_mesh(source.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6);bm.to_mesh(source.data);bm.free()
for ob in [head,source]:
 if ob.data.attributes.get('custom_normal'):ob.data.attributes.remove(ob.data.attributes['custom_normal'])
 for f in ob.data.polygons:
  if ob==head or f.center.z<1.59:f.use_smooth=True
high=bpy.data.materials.new('HeadSourceBake');high.use_nodes=True;nodes=high.node_tree.nodes;links=high.node_tree.links;bs=nodes.get('Principled BSDF')
tex=nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(p/'meshy/head_model_v1/texture_urls_0_base_color.png'));tex.image.colorspace_settings.name='sRGB'
links.new(tex.outputs['Color'],bs.inputs['Base Color']);links.new(tex.outputs['Color'],bs.inputs['Emission Color']);bs.inputs['Emission Strength'].default_value=1
source.data.materials.clear();source.data.materials.append(high)
for f in source.data.polygons:f.material_index=0
mat=bpy.data.materials.new('HeadAtlasTarget');mat.use_nodes=True;me.materials.clear();me.materials.append(mat)
for f in me.polygons:f.material_index=0
node=mat.node_tree.nodes.new('ShaderNodeTexImage');mat.node_tree.nodes.active=node
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=1;scene.render.bake.use_selected_to_active=True;scene.render.bake.cage_extrusion=.008;scene.render.bake.max_ray_distance=.035;scene.render.bake.margin=16;scene.render.bake.use_clear=True
for ob in bpy.context.view_layer.objects:ob.hide_render=ob not in [head,source];ob.select_set(False)
source.hide_set(False);head.hide_set(False);source.select_set(True);head.select_set(True);bpy.context.view_layer.objects.active=head
for suffix,kind,space in [('base','EMIT','sRGB'),('normal','NORMAL','Non-Color')]:
 im=bpy.data.images.new('HeadAtlas_'+suffix,width=2048,height=2048,alpha=False);im.colorspace_settings.name=space;node.image=im;bpy.ops.object.bake(type=kind);im.filepath_raw=str(p/'texturing'/('head_base_bake.png' if suffix=='base' else 'head_normal_bake.png'));im.file_format='PNG';im.save();print('HEAD_ATLAS_BAKED',suffix,flush=True)
bpy.data.objects.remove(head,do_unlink=True);source.hide_set(True);source.hide_render=True;body.hide_set(False);body.hide_render=False
bpy.ops.wm.save_as_mainfile(filepath=str(path))
