"""Legacy original-UV exporter for reduction candidates. Final rebaked assets use export_baked.py."""
import bpy,sys,json,math,os
import numpy as np
from pathlib import Path
if 'FIGC_EXPORT_SOURCE' not in os.environ:raise RuntimeError('Use export_baked.py for the final rebaked authoring file; trials must supply FIGC_EXPORT_SOURCE')
P=Path(__file__).resolve().parents[1];T=P/'textures';OUT=Path(os.environ.get('FIGC_EXPORT_DIR',str(P/'export')));OUT.mkdir(exist_ok=True,parents=True)
bpy.ops.wm.open_mainfile(filepath=os.environ.get('FIGC_EXPORT_SOURCE',str(P/'work/final_motion.blend')));scene=bpy.context.scene;scene.render.fps=30;scene.render.fps_base=1
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data;rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update()
head=np.array([d.value for d in me.attributes['head'].data]);huv=me.uv_layers['HeadUV'].data;buv=me.uv_layers['UVMap'].data
for p in me.polygons:
 if head[p.index]:
  for li in p.loop_indices:buv[li].uv=huv[li].uv
me.uv_layers.remove(me.uv_layers['HeadUV']);me.uv_layers.active=me.uv_layers['UVMap']
def material(name,suffix):
 
 if name in bpy.data.materials:bpy.data.materials[name].name=name+'_reference'
 m=bpy.data.materials.new(name);m.use_nodes=True;nt=m.node_tree;bs=nt.nodes.get('Principled BSDF')
 def tex(s,cs):
  n=nt.nodes.new('ShaderNodeTexImage');size='2k' if suffix=='_gear' else '1k';n.image=bpy.data.images.load(str(T/f'figc{suffix}_{s}_{size}.png'));n.image.colorspace_settings.name=cs;return n
 nt.links.new(tex('basecolor','sRGB').outputs['Color'],bs.inputs['Base Color'])
 nm=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(tex('normal','Non-Color').outputs['Color'],nm.inputs['Color']);nt.links.new(nm.outputs['Normal'],bs.inputs['Normal'])
 sep=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(tex('metal_rough','Non-Color').outputs['Color'],sep.inputs['Color']);nt.links.new(sep.outputs['Green'],bs.inputs['Roughness']);nt.links.new(sep.outputs['Blue'],bs.inputs['Metallic'])
 return m
mats=[material('FighterChain_A',''),material('FighterChainHead_A','_head')];me.materials.clear()
for m in mats:me.materials.append(m)
for p in me.polygons:p.material_index=int(head[p.index]);p.use_smooth=True
gear=material('FighterChainGear_A','_gear')
for name in ['Axe','Shield']:
 o=bpy.data.objects[name];o.data.materials.clear();o.data.materials.append(gear)
 for face in o.data.polygons:face.material_index=0
for o in bpy.data.objects:o.select_set(o in [body,bpy.data.objects['Axe'],bpy.data.objects['Shield']])
bpy.context.view_layer.objects.active=body;bpy.ops.object.join();body.name=body.data.name='FighterChain'
for img in bpy.data.images:
 if img.source=='FILE':img.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'mm6_figc_authoring.blend'))
for o in bpy.data.objects:o.select_set(o in [body,rig])
bpy.context.view_layer.objects.active=rig
rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=rig.animation_data.action.slots[0]
bpy.ops.export_scene.gltf(filepath=str(OUT/'mm6_figc_lod0.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=True,export_attributes=False,export_morph=False,export_image_format='AUTO',export_reset_pose_bones=True,export_anim_slide_to_zero=True)
info={'triangles':sum(len(p.vertices)-2 for p in body.data.polygons),'clips':{a.name:float((a.frame_range[1]-a.frame_range[0])/30) for a in bpy.data.actions},'bones':len(rig.data.bones),'rest_height_m':max(v.co.z for v in me.vertices)-min(v.co.z for v in me.vertices)}
(OUT/'export_info.json').write_text(json.dumps(info,indent=2));print('EXPORT',info)
