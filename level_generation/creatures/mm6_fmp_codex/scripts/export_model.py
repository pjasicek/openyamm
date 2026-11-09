"""Portable 60 Hz model, separate 1K head/body sets and ordinary relaxed hands."""
import bpy,json,sys
import numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];T=P/'textures';out=P/'export';out.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_uv.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data;scene=bpy.context.scene
assert scene.render.fps==60
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update()
head=np.array([e.value for e in me.attributes['head'].data],int)
for f in me.polygons:
 if head[f.index]:
  for li in f.loop_indices:me.uv_layers['UVMap'].data[li].uv=me.uv_layers['HeadUV'].data[li].uv
for uv in list(me.uv_layers):
 if uv.name!='UVMap':me.uv_layers.remove(uv)
me.uv_layers.active=me.uv_layers['UVMap'];me.uv_layers['UVMap'].active_render=True
bpy.context.view_layer.objects.active=rig
for o in bpy.data.objects:o.select_set(o==rig)
def material(part,name):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.use_backface_culling=True
 nt=m.node_tree;bs=nt.nodes.get('Principled BSDF')
 def tex(suffix,color):
  n=nt.nodes.new('ShaderNodeTexImage');n.image=bpy.data.images.load(str(T/f'fmp_{part}_{suffix}_1k.png'));n.image.colorspace_settings.name=color;return n
 nt.links.new(tex('basecolor','sRGB').outputs['Color'],bs.inputs['Base Color'])
 normal=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(tex('normal','Non-Color').outputs['Color'],normal.inputs['Color']);nt.links.new(normal.outputs['Normal'],bs.inputs['Normal'])
 sep=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(tex('metal_rough','Non-Color').outputs['Color'],sep.inputs['Color'])
 nt.links.new(sep.outputs['Green'],bs.inputs['Roughness']);nt.links.new(sep.outputs['Blue'],bs.inputs['Metallic'])
 bs.inputs['Specular IOR Level'].default_value=.16
 return m
me.materials.clear()
for part,name in [('body','PeasantF2_A'),('head','PeasantF2Head_A')]:me.materials.append(material(part,name))
me.polygons.foreach_set('material_index',head.tolist())
for attribute in list(me.attributes):
 if attribute.name in ['head','piece','finger','orig_co']:me.attributes.remove(attribute)
body.name=body.data.name='PeasantF2'
keep={'Standing','Walking','Run','Hit','Fidget','Death','Dead'}
assert {a.name for a in bpy.data.actions}==keep
a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];scene.frame_set(0)
for o in bpy.data.objects:o.select_set(o in (body,rig))
bpy.context.view_layer.objects.active=rig
bpy.data.orphans_purge(do_recursive=True)
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(out/'mm6_fmp.blend'))
bpy.ops.export_scene.gltf(filepath=str(out/'mm6_fmp_lod0.glb'),use_selection=True,export_format='GLB',export_yup=True,
 export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,
 export_skins=True,export_all_influences=True,export_attributes=False,export_morph=False,
 export_image_format='AUTO',export_reset_pose_bones=True,export_anim_slide_to_zero=True)
scene.frame_set(0);bpy.context.view_layer.update()
ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();co=np.array([v.co[:] for v in mesh.vertices]);ev.to_mesh_clear()
info={'triangles':len(me.polygons),'bones':len(rig.data.bones),'head_faces':int(head.sum()),'fps':60,
 'standing_height_m':float(np.ptp(co[:,2])),'standing_floor_m':float(co[:,2].min()),'native_standing_height':249*.699997,
 'scale':float(249*.699997/np.ptp(co[:,2])),'walk_stride_m':float(scene.get('walk_stride_m', 0)),
 'clips':{a.name:float(a.frame_range[1]/60) for a in bpy.data.actions},'sockets':[]}
(out/'export_info.json').write_text(json.dumps(info,indent=2));print('EXPORTED',json.dumps(info))
