"""Portable 60-fps export preserving the rig, half-frame foot contacts, sword drop, and shared texture sets."""
import bpy,sys,json
import numpy as np
from pathlib import Path
from mathutils import Matrix
P=Path(__file__).resolve().parents[1];T=P/'textures'
# Attack v2 (2026-10-19): the textured master with the refitted two-handed slash (scripts/attack_v2.py); the old
# clip stays in it as Attack_v1 and is dropped below with the other unlisted actions.
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_textured_fit_attack_v2.blend'))
r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];sw=bpy.data.objects['SwordMesh'];me=b.data;r.animation_data.action=None
for pb in r.pose.bones:pb.matrix_basis=Matrix()
bpy.context.view_layer.update()
hd=np.array([x.value for x in me.attributes['head'].data]);uv=me.uv_layers['UVMap'].data;huv=me.uv_layers['HeadUV'].data
for f in me.polygons:
 if hd[f.index]:
  for li in f.loop_indices:uv[li].uv=huv[li].uv
for layer in list(me.uv_layers):
 if layer.name!='UVMap':me.uv_layers.remove(layer)
me.uv_layers.active=me.uv_layers['UVMap']
def material(name,prefix,suffix):
 m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree;bs=n.nodes.get('Principled BSDF')
 def tex(label,cs):
  q=n.nodes.new('ShaderNodeTexImage');q.image=bpy.data.images.load(str(T/f'{prefix}_{label}{suffix}.png'));q.image.colorspace_settings.name=cs;return q
 n.links.new(tex('basecolor','sRGB').outputs['Color'],bs.inputs['Base Color'])
 nm=n.nodes.new('ShaderNodeNormalMap');n.links.new(tex('normal','Non-Color').outputs['Color'],nm.inputs['Color']);n.links.new(nm.outputs['Normal'],bs.inputs['Normal'])
 sep=n.nodes.new('ShaderNodeSeparateColor');n.links.new(tex('metal_rough','Non-Color').outputs['Color'],sep.inputs['Color']);n.links.new(sep.outputs['Green'],bs.inputs['Roughness']);n.links.new(sep.outputs['Blue'],bs.inputs['Metallic'])
 m['openyamm_specular']=1.;m['openyamm_specular_mask']=True
 return m
me.materials.clear()
for mat in [material('M432_A','m432','_1k'),material('M432Head_A','m432_head','_1k')]:me.materials.append(mat)
me.polygons.foreach_set('material_index',hd.tolist())
sw.data.materials.clear();sw.data.materials.append(material('Sword_A','m432_sword',''))
# Reference crop is x399..625, y20..1516; broad faces intentionally share their symmetric ornament.
for v in sw.data.uv_layers.active.data:
 u,vv=v.uv;v.uv=((u*1024-399)/226,1-((1-vv)*1536-20)/1496)
sw.parent=None;sw.matrix_parent_inverse=Matrix();sw.matrix_world=Matrix();sw.data.transform(r.data.bones['Socket_Sword'].matrix_local)
sw.vertex_groups.clear();sw.vertex_groups.new(name='Socket_Sword').add(list(range(len(sw.data.vertices))),1.,'REPLACE');r.data.bones['Socket_Sword'].use_deform=True
for o in bpy.data.objects:o.select_set(o in (b,sw))
bpy.context.view_layer.objects.active=b;bpy.ops.object.join();b.name=b.data.name='M432'
for at in list(b.data.attributes):
 if at.name in ('piece','garment','finger','head','orig_co'):b.data.attributes.remove(at)
keep=['Standing','Walking','Running','Attack','Cast','Hit','Death','Dead','Fidget']
for a in list(bpy.data.actions):
 if a.name not in keep:bpy.data.actions.remove(a);continue
 factor=60 if a.name=='Dead' else 2
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:
      k.co.x*=factor;k.handle_left.x*=factor;k.handle_right.x*=factor;k.interpolation='LINEAR'
     fc.update()
 a.frame_start*=factor;a.frame_end*=factor
sc=bpy.context.scene;sc.render.fps=60;sc.render.fps_base=1
r.animation_data.action=bpy.data.actions['Standing'];r.animation_data.action_slot=r.animation_data.action.slots[0];sc.frame_set(0)
e=b.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=e.to_mesh()
head_groups={b.vertex_groups[n].index for n in ('B_Head','B_Neck')}
head_ids=[v.index for v in b.data.vertices if sum(g.weight for g in v.groups if g.group in head_groups)>.5]
head_top=max(mesh.vertices[i].co.z for i in head_ids);e.to_mesh_clear();assert 1.4<head_top<2.1
(P/'export').mkdir(exist_ok=True);(P/'delivery').mkdir(exist_ok=True)
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(P/'delivery/mm8_dark_elf_warrior.blend'))
for o in bpy.data.objects:o.select_set(o in (b,r))
bpy.context.view_layer.objects.active=r
out=P/'export/mm8_m432_lod0.glb'
bpy.ops.export_scene.gltf(filepath=str(out),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=False,export_attributes=False,export_morph=False,export_image_format='AUTO',export_reset_pose_bones=True,export_anim_slide_to_zero=True,export_extras=True)
info={'triangles':sum(len(f.vertices)-2 for f in b.data.polygons),'bones':len(r.data.bones),'fps':60,'standing_head_top_m':head_top,'clips':{a.name:float((a.frame_range[1]-a.frame_range[0])/60) for a in bpy.data.actions}}
(P/'export/export_info.json').write_text(json.dumps(info,indent=1));print('EXPORT',info)
